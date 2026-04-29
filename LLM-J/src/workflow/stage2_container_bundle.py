"""Prepare container-ready Stage 2 probe bundles from repo profiles and historical commits."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.profiles import load_repo_profile, repo_profile_to_dict
from src.workflow.stage2_probe import _resolve_probe_commits


def prepare_stage2_container_bundles(
    *,
    repo: str,
    clones_dir: Path,
    output_dir: Path,
    profiles_dir: Path = Path("repo_profiles"),
    commits: list[str] | None = None,
    sample_size: int = 1,
) -> Path:
    """Prepare one or more container probe bundles for a repo."""
    from src.deep_eval.repo_manager import ensure_clone

    output_dir.mkdir(parents=True, exist_ok=True)
    bare_repo = ensure_clone(repo, clones_dir)
    repo_profile = load_repo_profile(repo, profiles_dir)
    repo_short = repo.split("/")[-1]
    selected_commits = _resolve_probe_commits(
        bare_repo=bare_repo,
        commits=commits,
        sample_size=sample_size,
    )

    bundles: list[dict[str, Any]] = []
    for index, commit_sha in enumerate(selected_commits, start=1):
        bundle_dir = output_dir / f"{repo_short}_{commit_sha[:12]}"
        bundle_dir.mkdir(parents=True, exist_ok=True)
        repo_tar = bundle_dir / "repo.tar"
        _export_commit_archive(bare_repo=bare_repo, commit_sha=commit_sha, output_path=repo_tar)
        requirement_files = _detect_requirement_files(bare_repo=bare_repo, commit_sha=commit_sha)

        metadata = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "repo": repo,
            "repo_short": repo_short,
            "bundle_index": index,
            "commit_sha": commit_sha,
            "profile_loaded": repo_profile is not None,
            "profile_path": str(repo_profile.source_path) if repo_profile and repo_profile.source_path else None,
            "profile": repo_profile_to_dict(repo_profile) if repo_profile else None,
            "repo_files": {
                "requirement_files": requirement_files,
            },
            "runtime_contract": {
                "execution_mode": "container_bundle_prepared",
                "intended_stage": "stage2_probe",
                "target_runtime": "docker_or_compatible_container_engine",
            },
            "artifacts": {
                "bundle_dir": str(bundle_dir),
                "repo_tar": str(repo_tar),
                "dockerfile": str(bundle_dir / "Dockerfile"),
                "install_script": str(bundle_dir / "install.sh"),
                "probe_script": str(bundle_dir / "probe.sh"),
                "build_script": str(bundle_dir / "build_image.sh"),
                "run_script": str(bundle_dir / "run_probe.sh"),
                "default_results_dir": str(bundle_dir / "probe_results"),
                "default_probe_result": str(bundle_dir / "probe_results" / "probe_result.json"),
            },
        }

        _write_bundle_files(
            bundle_dir=bundle_dir,
            metadata=metadata,
            repo_profile=repo_profile,
            requirement_files=requirement_files,
        )
        bundles.append(
            {
                "commit_sha": commit_sha,
                "bundle_dir": str(bundle_dir),
                "dockerfile": str(bundle_dir / "Dockerfile"),
                "repo_tar": str(repo_tar),
                "default_results_dir": str(bundle_dir / "probe_results"),
                "default_probe_result": str(bundle_dir / "probe_results" / "probe_result.json"),
            }
        )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo": repo,
        "repo_short": repo_short,
        "profile_loaded": repo_profile is not None,
        "profile_path": str(repo_profile.source_path) if repo_profile and repo_profile.source_path else None,
        "selection": {
            "requested_commits": commits or [],
            "sample_size": sample_size,
            "selected_commits": selected_commits,
        },
        "bundles": bundles,
        "summary": {
            "bundle_count": len(bundles),
            "ready_for_external_container_runtime": True,
        },
    }

    output_path = output_dir / f"{repo_short}_stage2_container_bundles.json"
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    markdown_path = output_dir / f"{repo_short}_stage2_container_bundles.md"
    markdown_path.write_text(_render_bundle_markdown(report), encoding="utf-8")
    return output_path


def _export_commit_archive(*, bare_repo: Path, commit_sha: str, output_path: Path) -> None:
    with open(output_path, "wb") as f:
        subprocess.run(
            ["git", "-C", str(bare_repo), "archive", "--format=tar", commit_sha],
            check=True,
            stdout=f,
        )


def _detect_requirement_files(*, bare_repo: Path, commit_sha: str) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(bare_repo), "ls-tree", "-r", "--name-only", commit_sha],
        check=True,
        capture_output=True,
        text=True,
    )
    candidates = [
        "requirements.txt",
        "requirements-dev.txt",
        "requirements-test.txt",
        "test-requirements.txt",
        "requirements/dev.txt",
        "requirements/test.txt",
        "requirements/tests.txt",
        "tests/requirements.txt",
    ]
    files = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    return [path for path in candidates if path in files]


def _write_bundle_files(
    *,
    bundle_dir: Path,
    metadata: dict[str, Any],
    repo_profile: Any,
    requirement_files: list[str],
) -> None:
    dockerfile_path = bundle_dir / "Dockerfile"
    install_script_path = bundle_dir / "install.sh"
    probe_script_path = bundle_dir / "probe.sh"
    build_script_path = bundle_dir / "build_image.sh"
    run_script_path = bundle_dir / "run_probe.sh"
    metadata_path = bundle_dir / "metadata.json"
    profile_path = bundle_dir / "profile.json"

    install_script_path.write_text(
        _render_install_script(repo_profile, requirement_files=requirement_files),
        encoding="utf-8",
    )
    probe_script_path.write_text(_render_probe_script(repo_profile), encoding="utf-8")
    dockerfile_path.write_text(_render_dockerfile(repo_profile), encoding="utf-8")
    build_script_path.write_text(_render_build_script(metadata), encoding="utf-8")
    run_script_path.write_text(_render_run_script(metadata), encoding="utf-8")
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    profile_path.write_text(
        json.dumps(repo_profile_to_dict(repo_profile) if repo_profile else None, indent=2),
        encoding="utf-8",
    )

    for path in (install_script_path, probe_script_path, build_script_path, run_script_path):
        path.chmod(0o755)


def _render_dockerfile(repo_profile: Any) -> str:
    python_version = repo_profile.runtime.python if repo_profile else "3.10"
    package_manager = repo_profile.runtime.package_manager if repo_profile else "uv"
    system_packages = repo_profile.environment.system_packages if repo_profile else []
    apt_line = ""
    if system_packages:
        apt_line = (
            "RUN apt-get update && apt-get install -y --no-install-recommends "
            + " ".join(system_packages)
            + " && rm -rf /var/lib/apt/lists/*\n"
        )
    uv_line = ""
    if package_manager == "uv":
        uv_line = "RUN python -m pip install uv\n"

    return (
        f"FROM python:{python_version}-slim\n"
        "ENV UV_CACHE_DIR=/tmp/llmj-uv-cache\n"
        "ENV PIP_CACHE_DIR=/tmp/llmj-pip-cache\n"
        "WORKDIR /workspace\n"
        f"{apt_line}"
        f"{uv_line}"
        "COPY repo.tar /tmp/repo.tar\n"
        "RUN tar -xf /tmp/repo.tar -C /workspace\n"
        "COPY install.sh /opt/llmj/install.sh\n"
        "COPY probe.sh /opt/llmj/probe.sh\n"
        "RUN chmod +x /opt/llmj/install.sh /opt/llmj/probe.sh\n"
        'CMD ["/bin/bash", "/opt/llmj/probe.sh"]\n'
    )


def _render_install_script(repo_profile: Any, *, requirement_files: list[str]) -> str:
    env_vars = repo_profile.environment.env_vars if repo_profile else {}
    pre_install = repo_profile.environment.pre_install if repo_profile else []
    install_commands = repo_profile.environment.install_commands if repo_profile else []
    install_fallbacks = repo_profile.environment.install_fallbacks if repo_profile else []
    post_install = repo_profile.environment.post_install if repo_profile else []
    normalized_commands = [
        *_normalize_shell_commands(pre_install, package_manager=None),
        *_normalize_shell_commands(
            install_commands,
            package_manager=repo_profile.runtime.package_manager if repo_profile else None,
        ),
        *_normalize_shell_commands(
            install_fallbacks,
            package_manager=repo_profile.runtime.package_manager if repo_profile else None,
        ),
    ]
    if not normalized_commands:
        normalized_commands = ["python -m pip install -e ."]
    post_install_commands = [
        *_normalize_shell_commands(post_install, package_manager=None),
        *[f"python -m pip install -r {path}" for path in requirement_files],
    ]

    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "cd /workspace",
        *[f'export {key}="{value}"' for key, value in env_vars.items()],
        "FAILED=0",
        "run_install() {",
        '  local cmd=\"$1\"',
        '  echo \"[stage2-container] install: $cmd\"',
        "  if bash -lc \"$cmd\"; then",
        "    return 0",
        "  fi",
        "  return 1",
        "}",
        "",
    ]

    for command in normalized_commands:
        quoted = command.replace('"', '\\"')
        lines.extend(
            [
                'if [ "${PRIMARY_SUCCESS:-0}" != "1" ] && run_install '
                + f'"{quoted}"; then',
                "  PRIMARY_SUCCESS=1",
                "fi",
            ]
        )
    lines.extend(
        [
            'if [ "${PRIMARY_SUCCESS:-0}" != "1" ]; then',
            '  echo "[stage2-container] all install commands failed" >&2',
            "  exit 1",
            "fi",
        ]
    )
    for command in post_install_commands:
        quoted = command.replace('"', '\\"')
        lines.extend(
            [
                f'if ! run_install "{quoted}"; then',
                '  echo "[stage2-container] post-install command failed" >&2',
                "  exit 1",
                "fi",
            ]
        )
    lines.extend(
        [
            "exit 0",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_probe_script(repo_profile: Any) -> str:
    test_command = repo_profile.test.command if repo_profile else "pytest -q"
    env_vars = repo_profile.test.env_vars if repo_profile else {}
    plugin_policy = repo_profile.test.plugin_policy if repo_profile else None
    normalized_probe = _normalize_probe_command(test_command, plugin_policy)

    env_lines = [f'export {key}="{value}"' for key, value in env_vars.items()]

    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "cd /workspace",
        'RESULTS_DIR="${LLMJ_RESULTS_DIR:-/tmp/llmj-stage2-results}"',
        'mkdir -p "$RESULTS_DIR"',
        'export RESULTS_DIR',
        'export STAGE2_PROBE_COMMAND=' + shlex.quote(normalized_probe),
        'export STAGE2_PROBE_STARTED_AT="$(date --iso-8601=seconds)"',
        *env_lines,
        'INSTALL_STATUS="success"',
        'PROBE_STATUS="not_run"',
        'PROBE_EXIT_CODE=""',
        'if /opt/llmj/install.sh > >(tee "$RESULTS_DIR/install.stdout.log") 2> >(tee "$RESULTS_DIR/install.stderr.log" >&2); then',
        '  echo "[stage2-container] install completed"',
        "else",
        '  INSTALL_STATUS="failed"',
        "fi",
        'if [ "$INSTALL_STATUS" = "success" ]; then',
        f'  echo "[stage2-container] probe: {normalized_probe}"',
        f"  if bash -lc {shlex.quote(normalized_probe)} > >(tee \"$RESULTS_DIR/probe.stdout.log\") 2> >(tee \"$RESULTS_DIR/probe.stderr.log\" >&2); then",
        '    PROBE_STATUS="success"',
        '    PROBE_EXIT_CODE="0"',
        "  else",
        '    PROBE_STATUS="failed"',
        '    PROBE_EXIT_CODE="$?"',
        "  fi",
        "else",
        '  PROBE_EXIT_CODE=""',
        "fi",
        'export INSTALL_STATUS PROBE_STATUS PROBE_EXIT_CODE',
        'export STAGE2_PROBE_FINISHED_AT="$(date --iso-8601=seconds)"',
        'python -c \'import json, os, pathlib; result = {"install_status": os.environ["INSTALL_STATUS"], "probe_status": os.environ["PROBE_STATUS"], "probe_command": os.environ["STAGE2_PROBE_COMMAND"], "probe_exit_code": int(os.environ["PROBE_EXIT_CODE"]) if os.environ.get("PROBE_EXIT_CODE") else None, "started_at": os.environ["STAGE2_PROBE_STARTED_AT"], "finished_at": os.environ["STAGE2_PROBE_FINISHED_AT"], "artifacts": {"install_stdout": "install.stdout.log", "install_stderr": "install.stderr.log", "probe_stdout": "probe.stdout.log", "probe_stderr": "probe.stderr.log"}}; pathlib.Path(os.environ["RESULTS_DIR"], "probe_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")\'',
        'if [ "$INSTALL_STATUS" != "success" ] || [ "$PROBE_STATUS" != "success" ]; then',
        "  exit 1",
        "fi",
    ]
    return "\n".join(lines) + "\n"


def _render_build_script(metadata: dict[str, Any]) -> str:
    repo_short = metadata["repo_short"]
    commit_sha = metadata["commit_sha"][:12]
    tag = f"llmj-stage2-probe:{repo_short}-{commit_sha}"
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        f"docker build -t {tag} .\n"
    )


def _render_run_script(metadata: dict[str, Any]) -> str:
    repo_short = metadata["repo_short"]
    commit_sha = metadata["commit_sha"][:12]
    tag = f"llmj-stage2-probe:{repo_short}-{commit_sha}"
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'RESULTS_DIR="${1:-$(pwd)/probe_results}"\n'
        'mkdir -p "$RESULTS_DIR"\n'
        f'if docker run --rm -v "$RESULTS_DIR:/results" -e LLMJ_RESULTS_DIR=/results {tag} > >(tee "$RESULTS_DIR/container.stdout.log") 2> >(tee "$RESULTS_DIR/container.stderr.log" >&2); then\n'
        '  STATUS=0\n'
        "else\n"
        '  STATUS=$?\n'
        "fi\n"
        'printf "%s\\n" "$STATUS" > "$RESULTS_DIR/docker_exit_code.txt"\n'
        "exit $STATUS\n"
    )


def _normalize_shell_commands(commands: list[str], package_manager: str | None) -> list[str]:
    normalized: list[str] = []
    for command in commands:
        stripped = command.strip()
        if stripped:
            if package_manager == "uv" and stripped.startswith("uv pip install "):
                stripped = stripped.replace("uv pip install ", "uv pip install --system ", 1)
            normalized.append(stripped)
    return normalized


def _normalize_probe_command(command: str, plugin_policy: Any) -> str:
    tokens = shlex.split(command)
    if not tokens:
        tokens = ["pytest", "-q"]
    if tokens[0] == "pytest":
        tokens.insert(0, "-m")
        tokens.insert(0, "python")
    if "--collect-only" not in tokens:
        tokens.append("--collect-only")
    if plugin_policy and getattr(plugin_policy, "explicit_plugins", None):
        injected: list[str] = []
        for plugin in plugin_policy.explicit_plugins:
            injected.extend(["-p", plugin])
        tokens = tokens[:3] + injected + tokens[3:]
    if plugin_policy is None or getattr(plugin_policy, "mode", "default") in {"default", "explicit_only"}:
        return "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 " + " ".join(shlex.quote(token) for token in tokens)
    return " ".join(shlex.quote(token) for token in tokens)


def _render_bundle_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Stage 2 Container Bundles: {report['repo']}",
        "",
        f"- Generated: {report['generated_at']}",
        f"- Profile loaded: {report['profile_loaded']}",
        f"- Bundle count: {report['summary']['bundle_count']}",
        "",
        "## Bundles",
    ]
    for bundle in report["bundles"]:
        lines.extend(
            [
                "",
                f"### {bundle['commit_sha']}",
                f"- Bundle dir: {bundle['bundle_dir']}",
                f"- Dockerfile: {bundle['dockerfile']}",
                f"- Repo tar: {bundle['repo_tar']}",
                f"- Results dir: {bundle['default_results_dir']}",
                f"- Probe result: {bundle['default_probe_result']}",
            ]
        )
    return "\n".join(lines) + "\n"
