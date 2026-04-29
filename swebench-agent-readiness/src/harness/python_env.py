"""Prepare a host-local Python environment for a materialized pilot workspace."""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from swebench.harness.test_spec.test_spec import TestSpec


CONDA_BOOTSTRAP_CONSTRAINT_OVERRIDES = {
    "numpy": "numpy<2",
    "scipy": "scipy<1.14",
}


def _run(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    subprocess.run(command, check=True, cwd=str(cwd) if cwd else None, env=env)


def _extract_pip_installs(script_lines: list[str]) -> list[list[str]]:
    installs: list[list[str]] = []
    prefix = "python -m pip install "
    for line in script_lines:
        stripped = line.strip()
        marker = stripped.find(prefix)
        if marker >= 0:
            installs.append(shlex.split(stripped[marker + len(prefix) :]))
    return installs


def _conda_requirement_to_pip(requirement: str) -> str:
    """Relax conda bootstrap packages into pip-installable package names.

    The conda-create line describes the historical environment shape, but exact
    heavy scientific runtime pins often do not build cleanly on the host. We
    keep explicit upstream pip-install lines authoritative and widen only the
    packages that commonly fail as historical source builds, while preserving
    the original constraints for lighter dependencies and versioned build tools
    such as Cython.
    """
    package_name = re.split(r"[<>=!]+", requirement, maxsplit=1)[0]
    if package_name.lower() in CONDA_BOOTSTRAP_CONSTRAINT_OVERRIDES:
        return CONDA_BOOTSTRAP_CONSTRAINT_OVERRIDES[package_name.lower()]
    if requirement.count("=") == 1 and "==" not in requirement:
        name, version = requirement.split("=", 1)
        return f"{name}=={version}"
    return requirement


def _extract_conda_create_installs(script_lines: list[str]) -> list[list[str]]:
    installs: list[list[str]] = []
    for line in script_lines:
        stripped = line.strip()
        if not stripped.startswith("conda create "):
            continue
        tokens = shlex.split(stripped)
        packages: list[str] = []
        index = 2
        while index < len(tokens):
            token = tokens[index]
            if token in {"-n", "--name", "-c", "--channel", "--solver"}:
                index += 2
                continue
            if token.startswith(("--name=", "--channel=", "--solver=")):
                index += 1
                continue
            if token in {"-y", "--yes", "--override-channels"}:
                index += 1
                continue
            if token.startswith("-"):
                index += 1
                continue
            if token.startswith("python="):
                index += 1
                continue
            packages.append(_conda_requirement_to_pip(token))
            index += 1
        if packages:
            installs.append(packages)
    return installs


def _extract_inline_requirement_files(script_lines: list[str]) -> dict[str, str]:
    requirement_files: dict[str, str] = {}
    pattern = re.compile(
        r"^cat <<'(?P<tag>[^']+)' > (?P<target>\S+)\n(?P<body>.*)\n(?P=tag)$",
        re.DOTALL,
    )
    for line in script_lines:
        stripped = line.strip()
        match = pattern.match(stripped)
        if match is None:
            continue
        requirement_files[match.group("target")] = match.group("body").strip() + "\n"
    return requirement_files


def _extract_workspace_setup_commands(script_lines: list[str]) -> list[str]:
    commands: list[str] = []
    for line in script_lines:
        stripped = line.strip()
        if stripped.startswith("sed -i "):
            commands.append(stripped)
    return commands


def _extract_python_version(script_lines: list[str]) -> str | None:
    prefix = "conda create -n testbed python="
    for line in script_lines:
        stripped = line.strip()
        if stripped.startswith(prefix):
            version = stripped[len(prefix) :].split()[0]
            return version
    return None


def _build_venv_command(venv_dir: Path, python_version: str | None) -> list[str]:
    command = ["uv", "venv", "--seed", str(venv_dir)]
    if venv_dir.exists():
        command.append("--clear")
    if python_version is not None:
        command.extend(["--python", python_version])
    return command


def _resolve_local_install_arg(arg: str, workspace_dir: Path) -> str:
    if arg == ".":
        return str(workspace_dir)
    if arg.startswith("./"):
        return str(workspace_dir / arg[2:])
    if arg.startswith(".["):
        return f"{workspace_dir}{arg[1:]}"
    return arg


def _should_use_workspace_pip(install_args: list[str], workspace_dir: Path) -> bool:
    workspace_prefix = str(workspace_dir)
    for arg in install_args:
        if arg == workspace_prefix or arg.startswith(f"{workspace_prefix}["):
            return True
    return False


def _filter_workspace_pip_args(install_args: list[str]) -> list[str]:
    """Drop legacy pip flags that current host pip no longer accepts."""

    unsupported_flags = {"--no-use-pep517"}
    return [arg for arg in install_args if arg not in unsupported_flags]


def _ensure_setuptools_compat_install(installs: list[list[str]]) -> list[list[str]]:
    """Keep historical pkg_resources imports available under modern uv seeds."""

    for install_args in installs:
        if any(arg.split("==", 1)[0].lower() == "setuptools" for arg in install_args):
            return installs
    return [["setuptools==70.0.0"], *installs]


def _install_args_include_package(installs: list[list[str]], package_name: str) -> bool:
    normalized = package_name.lower().replace("_", "-")
    for install_args in installs:
        for arg in install_args:
            if arg.startswith("-") or "/" in arg:
                continue
            candidate = re.split(r"[<>=!~\[]+", arg, maxsplit=1)[0].lower().replace("_", "-")
            if candidate == normalized:
                return True
    return False


def _eval_invokes_pytest(test_spec: TestSpec) -> bool:
    for line in test_spec.eval_script_list:
        stripped = line.strip()
        try:
            tokens = shlex.split(stripped)
        except ValueError:
            # Some historical SWE-bench eval snippets contain unmatched shell
            # quotes but still expose the runner name plainly enough to detect.
            if re.search(r"(^|[\s;&|])(?:pytest|py\.test)($|[\s;&|])", stripped):
                return True
            if re.search(r"(^|[\s;&|])python\s+-m\s+pytest($|[\s;&|])", stripped):
                return True
            continue
        if "pytest" in tokens or "py.test" in tokens:
            return True
        for index, token in enumerate(tokens[:-2]):
            if token == "python" and tokens[index + 1 : index + 3] == ["-m", "pytest"]:
                return True
    return False


def _ensure_pytest_for_pytest_oracle(installs: list[list[str]], test_spec: TestSpec) -> list[list[str]]:
    """Install pytest when the official oracle command requires it but setup omitted it."""

    if not _eval_invokes_pytest(test_spec):
        return installs
    if _install_args_include_package(installs, "pytest"):
        return installs
    return [["pytest"], *installs]


def _requires_legacy_markupsafe(workspace_dir: Path) -> bool:
    """Detect historical Sphinx checkouts that cap MarkupSafe before editable install."""

    setup_py = workspace_dir / "setup.py"
    if not setup_py.exists():
        return False
    setup_text = setup_py.read_text(encoding="utf-8", errors="replace").lower()
    return "markupsafe<=2.0.1" in setup_text


def _pylint_astroid_requirement(workspace_dir: Path) -> str | None:
    """Return the checkout-local astroid constraint for historical PyLint tasks."""

    setup_cfg = workspace_dir / "setup.cfg"
    if not setup_cfg.exists():
        return None
    for line in setup_cfg.read_text(encoding="utf-8", errors="replace").splitlines():
        requirement = line.split("#", 1)[0].strip()
        if requirement.lower().startswith("astroid"):
            return requirement.replace(" ", "")
    return None


def _requires_legacy_astropy_build(workspace_dir: Path) -> bool:
    """Detect historical Astropy checkouts needing host compiler compatibility."""

    pyproject = workspace_dir / "pyproject.toml"
    if not pyproject.exists() or not (workspace_dir / "astropy" / "wcs").exists():
        return False
    text = pyproject.read_text(encoding="utf-8", errors="replace")
    return "extension-helpers" in text and "oldest-supported-numpy" in text


def _append_pip_flags(install_args: list[str], flags: list[str]) -> list[str]:
    """Append pip flags once, preserving the upstream install argument order."""

    patched = list(install_args)
    for flag in flags:
        if flag not in patched:
            patched.append(flag)
    return patched


def _append_cflag(env: dict[str, str], flag: str) -> dict[str, str]:
    patched = dict(env)
    current = patched.get("CFLAGS", "").strip()
    patched["CFLAGS"] = f"{current} {flag}".strip() if current else flag
    return patched


def _commit_workspace_setup_changes(workspace_dir: Path) -> None:
    """Commit tracked setup-script edits so agent diffs start from setup state."""

    if not (workspace_dir / ".git").exists():
        return
    completed = subprocess.run(
        ["git", "-c", "core.fileMode=false", "diff", "--quiet"],
        cwd=workspace_dir,
        check=False,
    )
    if completed.returncode == 0:
        return
    if completed.returncode != 1:
        completed.check_returncode()
    _run(["git", "add", "-u"], cwd=workspace_dir)
    _run(
        [
            "git",
            "-c",
            "user.email=setup@swebench.config",
            "-c",
            "user.name=SWE-bench",
            "commit",
            "-m",
            "SWE-bench workspace setup",
        ],
        cwd=workspace_dir,
    )


@dataclass(frozen=True)
class WorkspaceEnvResult:
    """Record of the prepared workspace Python environment."""

    workspace_dir: str
    venv_dir: str
    python_path: str
    python_version: str | None
    package_installs: list[list[str]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "workspace_dir": self.workspace_dir,
            "venv_dir": self.venv_dir,
            "python_path": self.python_path,
            "python_version": self.python_version,
            "package_installs": [list(item) for item in self.package_installs],
        }


def prepare_workspace_env(
    *,
    workspace_dir: Path,
    test_spec: TestSpec,
    output_path: Path,
    venv_name: str = ".pilot-venv",
) -> Path:
    """Create a workspace-local venv and install the upstream Python deps."""

    venv_dir = workspace_dir / venv_name
    python_path = venv_dir / "bin" / "python"
    python_version = _extract_python_version(test_spec.env_script_list)
    venv_cmd = _build_venv_command(venv_dir, python_version)
    _run(venv_cmd)

    installs = _extract_conda_create_installs(test_spec.env_script_list)
    installs.extend(_extract_pip_installs(test_spec.env_script_list))
    installs.extend(_extract_pip_installs(test_spec.repo_script_list))
    installs = _ensure_setuptools_compat_install(installs)
    installs = _ensure_pytest_for_pytest_oracle(installs, test_spec)
    workspace_setup_commands = _extract_workspace_setup_commands(test_spec.env_script_list)
    workspace_setup_commands.extend(_extract_workspace_setup_commands(test_spec.repo_script_list))
    inline_requirement_files = _extract_inline_requirement_files(test_spec.env_script_list)
    inline_requirement_files.update(_extract_inline_requirement_files(test_spec.repo_script_list))
    generated_dir = workspace_dir / ".pilot-env"
    generated_dir.mkdir(parents=True, exist_ok=True)

    for command in workspace_setup_commands:
        subprocess.run(command, shell=True, check=True, cwd=str(workspace_dir))
    if workspace_setup_commands:
        _commit_workspace_setup_changes(workspace_dir)

    for install_args in installs:
        resolved_args: list[str] = []
        for index, arg in enumerate(install_args):
            if (
                arg in inline_requirement_files
                and index > 0
                and install_args[index - 1] in {"-r", "--requirement"}
            ):
                generated_path = generated_dir / Path(arg).name
                generated_path.write_text(inline_requirement_files[arg], encoding="utf-8")
                resolved_args.append(str(generated_path))
                continue
            resolved_args.append(_resolve_local_install_arg(arg, workspace_dir))
        if _should_use_workspace_pip(resolved_args, workspace_dir):
            if _requires_legacy_markupsafe(workspace_dir):
                _run(
                    ["uv", "pip", "install", "--python", str(python_path), "markupsafe==2.0.1"],
                    cwd=workspace_dir,
                )
            astroid_requirement = _pylint_astroid_requirement(workspace_dir)
            if astroid_requirement is not None:
                _run(
                    ["uv", "pip", "install", "--python", str(python_path), astroid_requirement],
                    cwd=workspace_dir,
                )
            install_env = None
            if _requires_legacy_astropy_build(workspace_dir):
                _run(
                    [
                        "uv",
                        "pip",
                        "install",
                        "--python",
                        str(python_path),
                        "cython==0.29.30",
                        "extension-helpers",
                        "setuptools_scm>=6.2",
                        "wheel",
                    ],
                    cwd=workspace_dir,
                )
                resolved_args = _append_pip_flags(
                    resolved_args,
                    ["--no-build-isolation", "--no-deps"],
                )
                install_env = _append_cflag(os.environ, "-std=gnu17 -Wno-error=incompatible-pointer-types")
            install_command = [
                str(python_path),
                "-m",
                "pip",
                "install",
                *_filter_workspace_pip_args(resolved_args),
            ]
        else:
            install_command = ["uv", "pip", "install", "--python", str(python_path), *resolved_args]
            install_env = None
        _run(install_command, cwd=workspace_dir, env=install_env)

    result = WorkspaceEnvResult(
        workspace_dir=str(workspace_dir),
        venv_dir=str(venv_dir),
        python_path=str(python_path),
        python_version=python_version,
        package_installs=installs,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(result.to_dict(), handle, indent=2)
    return output_path


def prepend_workspace_env(path: str, venv_dir: Path) -> str:
    """Prepend the workspace venv bin dir to PATH."""

    return os.pathsep.join([str(venv_dir / "bin"), path])
