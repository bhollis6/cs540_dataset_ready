"""Mechanical pre-flight validation: FAIL_TO_PASS test checks."""

from __future__ import annotations

from dataclasses import dataclass
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

from src.deep_eval.models import PreflightResult
from src.scraper.models import _is_executable_test_file

if TYPE_CHECKING:
    from src.profiles import RepoProfile


@dataclass
class PreflightInstallResult:
    success: bool
    output: str = ""
    attempts: list[dict[str, Any]] | None = None


@dataclass
class PytestRunResult:
    passed: set[str]
    failed: set[str]
    output: str
    execution_error: bool = False


def run_preflight(
    worktree: Path,
    candidate_id: str,
    patch_diff: str,
    test_diff: str,
    test_files: list[str],
    repo_profile: RepoProfile | None = None,
) -> PreflightResult:
    """Run SWE-bench style FAIL_TO_PASS validation.

    1. Apply test_diff at base_commit → run tests → expect some FAIL
    2. Apply patch_diff (gold fix) → run tests → expect PASS
    3. Tests that go FAIL→PASS are the ground truth signal
    """
    start = time.time()
    python_executable, venv_output = _ensure_preflight_venv(worktree)
    if python_executable is None:
        return PreflightResult(
            candidate_id=candidate_id,
            status="ERROR",
            reason="Failed to create isolated preflight virtualenv",
            base_test_output=venv_output[:2000],
            install_success=False,
            elapsed_seconds=time.time() - start,
        )

    # Step 0: Install the project so tests can import it
    install_result = _install_project(
        worktree,
        python_executable=python_executable,
        repo_profile=repo_profile,
    )
    if not install_result.success:
        return PreflightResult(
            candidate_id=candidate_id,
            status="ERROR",
            reason="Failed to install project in worktree",
            base_test_output=install_result.output[:2000],
            install_success=False,
            elapsed_seconds=time.time() - start,
        )

    # Step 1: Apply test patch
    test_method = _apply_patch(worktree, test_diff)
    if test_method is None:
        return PreflightResult(
            candidate_id=candidate_id,
            status="FAIL",
            reason="Test patch does not apply cleanly",
            install_success=install_result.success,
            elapsed_seconds=time.time() - start,
        )

    # Step 2: Run tests at base_commit + test_patch (expect failures)
    base_results = _run_pytest(
        worktree,
        test_files,
        python_executable=python_executable,
        repo_profile=repo_profile,
    )
    if base_results.execution_error:
        if _looks_like_expected_collection_failure(base_results.output):
            fix_method = _apply_patch(worktree, patch_diff)
            if fix_method is not None:
                fixed_results = _run_pytest(
                    worktree,
                    test_files,
                    python_executable=python_executable,
                    repo_profile=repo_profile,
                )
                if (
                    not fixed_results.execution_error
                    and fixed_results.passed
                    and not fixed_results.failed
                ):
                    return PreflightResult(
                        candidate_id=candidate_id,
                        status="PASS",
                        reason=(
                            f"{len(fixed_results.passed)} tests went "
                            "COLLECTION_ERROR→PASS"
                        ),
                        fail_to_pass_tests=sorted(fixed_results.passed),
                        pass_to_pass_tests=[],
                        base_test_output=base_results.output[:2000],
                        fixed_test_output=fixed_results.output[:2000],
                        patch_apply_method=f"test:{test_method}, fix:{fix_method}",
                        install_success=True,
                        elapsed_seconds=time.time() - start,
                    )
        return PreflightResult(
            candidate_id=candidate_id,
            status="ERROR",
            reason="pytest failed to execute at base commit",
            base_test_output=base_results.output[:2000],
            install_success=install_result.success,
            elapsed_seconds=time.time() - start,
        )

    base_passed = base_results.passed
    base_failed = base_results.failed
    base_output = base_results.output

    if not base_failed:
        return PreflightResult(
            candidate_id=candidate_id,
            status="FAIL",
            reason="No failing tests at base commit — no FAIL_TO_PASS signal",
            base_test_output=base_output[:2000],
            patch_apply_method=test_method,
            install_success=install_result.success,
            elapsed_seconds=time.time() - start,
        )

    # Step 3: Apply gold patch (source fix)
    fix_method = _apply_patch(worktree, patch_diff)
    if fix_method is None:
        return PreflightResult(
            candidate_id=candidate_id,
            status="FAIL",
            reason="Gold patch does not apply cleanly",
            base_test_output=base_output[:2000],
            patch_apply_method=test_method,
            install_success=install_result.success,
            elapsed_seconds=time.time() - start,
        )

    # Step 4: Run tests again (expect pass)
    fixed_results = _run_pytest(
        worktree,
        test_files,
        python_executable=python_executable,
        repo_profile=repo_profile,
    )
    if fixed_results.execution_error:
        return PreflightResult(
            candidate_id=candidate_id,
            status="ERROR",
            reason="pytest failed to execute after gold patch",
            base_test_output=base_output[:2000],
            fixed_test_output=fixed_results.output[:2000],
            patch_apply_method=test_method,
            install_success=install_result.success,
            elapsed_seconds=time.time() - start,
        )

    fixed_passed = fixed_results.passed
    fixed_failed = fixed_results.failed
    fixed_output = fixed_results.output

    # Step 5: Compute FAIL_TO_PASS
    fail_to_pass = base_failed - fixed_failed  # tests that were failing, now pass
    pass_to_pass = base_passed & fixed_passed  # tests that stayed passing

    if not fail_to_pass:
        return PreflightResult(
            candidate_id=candidate_id,
            status="FAIL",
            reason="No tests went from FAIL to PASS after gold patch",
            base_test_output=base_output[:2000],
            fixed_test_output=fixed_output[:2000],
            patch_apply_method=f"test:{test_method}, fix:{fix_method}",
            install_success=install_result.success,
            elapsed_seconds=time.time() - start,
        )

    return PreflightResult(
        candidate_id=candidate_id,
        status="PASS",
        reason=f"{len(fail_to_pass)} tests went FAIL→PASS",
        fail_to_pass_tests=sorted(fail_to_pass),
        pass_to_pass_tests=sorted(pass_to_pass),
        base_test_output=base_output[:2000],
        fixed_test_output=fixed_output[:2000],
        patch_apply_method=f"test:{test_method}, fix:{fix_method}",
        install_success=True,
        elapsed_seconds=time.time() - start,
    )


def _ensure_preflight_venv(worktree: Path) -> tuple[Path | None, str]:
    """Create a disposable virtualenv inside the worktree for isolated installs/tests."""
    worktree = worktree.resolve()
    venv_dir = worktree / ".llmj-preflight-venv"
    python_executable = _venv_python_path(venv_dir)
    if python_executable.exists():
        return python_executable, ""

    result = subprocess.run(
        [sys.executable, "-m", "venv", str(venv_dir)],
        capture_output=True,
        text=True,
        cwd=str(worktree),
        timeout=120,
    )
    output = result.stdout + result.stderr
    if result.returncode != 0 or not python_executable.exists():
        return None, output
    return python_executable, output


def _install_project(
    worktree: Path,
    *,
    python_executable: Path,
    repo_profile: RepoProfile | None = None,
    install_timeout_seconds: int = 120,
) -> PreflightInstallResult:
    """Install the project in editable mode so tests can import it.

    Uses sys.executable to ensure we install into the active Python environment.
    Tries common historical test-environment patterns in order:
    - repo requirements files when present
    - editable installs with likely test/dev extras
    - bare editable install as the last fallback
    """
    worktree = worktree.resolve()
    install_commands = _build_install_commands(
        worktree,
        python_executable=python_executable,
        repo_profile=repo_profile,
    )

    last_output = ""
    attempts: list[dict[str, Any]] = []
    for cmd in install_commands:
        started = time.time()
        try:
            env = {
                **os.environ,
                "UV_CACHE_DIR": "/tmp/llmj-uv-cache",
                "PIP_CACHE_DIR": "/tmp/llmj-pip-cache",
                **(repo_profile.environment.env_vars if repo_profile else {}),
            }
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(worktree),
                timeout=install_timeout_seconds,
                env=env,
            )
            last_output = result.stdout + result.stderr
            attempts.append({
                "command": cmd,
                "status": "PASS" if result.returncode == 0 else "FAIL",
                "returncode": result.returncode,
                "elapsed_seconds": time.time() - started,
                "output": last_output[:2000],
            })
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            last_output = f"{stdout}{stderr}".strip() or "install command timed out"
            attempts.append({
                "command": cmd,
                "status": "TIMEOUT",
                "returncode": None,
                "elapsed_seconds": time.time() - started,
                "output": last_output[:2000],
            })
            continue
        if _is_terminal_install_error(last_output):
            return PreflightInstallResult(success=False, output=last_output, attempts=attempts)
        if result.returncode == 0:
            post_install_result = _run_post_install_commands(
                worktree,
                python_executable=python_executable,
                repo_profile=repo_profile,
                env=env,
                timeout_seconds=install_timeout_seconds,
            )
            attempts.extend(post_install_result.attempts or [])
            if not post_install_result.success:
                return PreflightInstallResult(
                    success=False,
                    output=post_install_result.output or last_output,
                    attempts=attempts,
                )
            return PreflightInstallResult(success=True, output=last_output, attempts=attempts)

    return PreflightInstallResult(success=False, output=last_output, attempts=attempts)


def _build_install_commands(
    worktree: Path,
    *,
    python_executable: Path,
    repo_profile: RepoProfile | None = None,
) -> list[list[str]]:
    worktree = worktree.resolve()
    pip_install = [str(python_executable), "-m", "pip", "install"]
    commands: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()

    def add_command(command: list[str]) -> None:
        key = tuple(command)
        if key not in seen:
            commands.append(command)
            seen.add(key)

    if repo_profile is not None:
        for command in repo_profile.environment.install_commands:
            normalized = _normalize_profile_command(command, python_executable=python_executable)
            if normalized:
                add_command(normalized)
        for command in repo_profile.environment.install_fallbacks:
            normalized = _normalize_profile_command(command, python_executable=python_executable)
            if normalized:
                add_command(normalized)

    requirement_files = [
        "requirements.txt",
        "requirements-dev.txt",
        "requirements-test.txt",
        "test-requirements.txt",
        "requirements/dev.txt",
        "requirements/test.txt",
        "requirements/tests.txt",
        "tests/requirements.txt",
    ]
    for relative_path in requirement_files:
        path = worktree / relative_path
        if path.exists():
            add_command(pip_install + ["-r", str(path)])

    editable_targets = [
        f"{worktree}[test,tests,dev]",
        f"{worktree}[tests,dev]",
        f"{worktree}[test,dev]",
        f"{worktree}[test]",
        f"{worktree}[tests]",
        f"{worktree}[dev]",
        str(worktree),
    ]
    for target in editable_targets:
        add_command(pip_install + ["-e", target])

    return commands


def _run_post_install_commands(
    worktree: Path,
    *,
    python_executable: Path,
    repo_profile: RepoProfile | None,
    env: dict[str, str],
    timeout_seconds: int,
) -> PreflightInstallResult:
    commands = _build_post_install_commands(
        worktree,
        python_executable=python_executable,
        repo_profile=repo_profile,
    )
    attempts: list[dict[str, Any]] = []
    last_output = ""
    for cmd in commands:
        started = time.time()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(worktree),
                timeout=timeout_seconds,
                env=env,
            )
            last_output = result.stdout + result.stderr
            attempts.append({
                "command": cmd,
                "status": "PASS" if result.returncode == 0 else "FAIL",
                "returncode": result.returncode,
                "elapsed_seconds": time.time() - started,
                "output": last_output[:2000],
            })
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            last_output = f"{stdout}{stderr}".strip() or "post-install command timed out"
            attempts.append({
                "command": cmd,
                "status": "TIMEOUT",
                "returncode": None,
                "elapsed_seconds": time.time() - started,
                "output": last_output[:2000],
            })
            return PreflightInstallResult(success=False, output=last_output, attempts=attempts)

        if result.returncode != 0:
            return PreflightInstallResult(success=False, output=last_output, attempts=attempts)

    return PreflightInstallResult(success=True, output=last_output, attempts=attempts)


def _build_post_install_commands(
    worktree: Path,
    *,
    python_executable: Path,
    repo_profile: RepoProfile | None,
) -> list[list[str]]:
    commands: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()

    def add_command(command: list[str]) -> None:
        key = tuple(command)
        if command and key not in seen:
            commands.append(command)
            seen.add(key)

    if repo_profile is not None:
        for command in repo_profile.environment.post_install:
            normalized = _normalize_profile_command(command, python_executable=python_executable)
            add_command(normalized)

    requirement_files = [
        "requirements.txt",
        "requirements-dev.txt",
        "requirements-test.txt",
        "test-requirements.txt",
        "requirements/dev.txt",
        "requirements/test.txt",
        "requirements/tests.txt",
        "tests/requirements.txt",
    ]
    for relative_path in requirement_files:
        path = worktree / relative_path
        if path.exists():
            add_command([str(python_executable), "-m", "pip", "install", "-r", str(path)])

    if not _python_module_available(python_executable, "pytest"):
        add_command([str(python_executable), "-m", "pip", "install", "pytest"])

    return commands


def build_probe_test_command(
    *,
    python_executable: Path,
    repo_profile: RepoProfile | None,
) -> list[str]:
    """Build a profile-aware pytest collection command for Stage 2 probing."""
    if repo_profile is not None:
        normalized = _normalize_profile_command(
            repo_profile.test.command,
            python_executable=python_executable,
        )
        if normalized[:3] == [str(python_executable), "-m", "pytest"]:
            args = normalized[3:]
            if "--collect-only" not in args:
                args.append("--collect-only")
            return _apply_profile_plugin_policy(
                [str(python_executable), "-m", "pytest", *args],
                repo_profile=repo_profile,
            )

    return [str(python_executable), "-m", "pytest", "-q", "--collect-only"]


def _is_terminal_install_error(output: str) -> bool:
    """Detect install failures where retrying alternate editable targets is not useful."""
    markers = [
        "Failed to establish a new connection",
        "No matching distribution found",
        "Could not find a version that satisfies the requirement",
        "Installing build dependencies: finished with status 'error'",
        "error: Could not acquire lock",
    ]
    return any(marker in output for marker in markers)


def build_probe_environment(
    *,
    repo_profile: RepoProfile | None,
) -> dict[str, str]:
    """Build environment variables for Stage 2 probe execution."""
    env = dict(os.environ)
    if repo_profile is None:
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        return env

    env.update(repo_profile.environment.env_vars)
    env.update(repo_profile.test.env_vars)
    if repo_profile.test.plugin_policy.mode in {"default", "explicit_only"}:
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    return env


def _normalize_profile_command(command: str, *, python_executable: Path) -> list[str]:
    tokens = shlex.split(command)
    if not tokens:
        return []
    if len(tokens) >= 3 and tokens[0] == "uv" and tokens[1] == "pip":
        return [str(python_executable), "-m", "pip", *tokens[2:]]
    if tokens[0] == "python":
        return [str(python_executable), *tokens[1:]]
    if tokens[0] == "pip":
        return [str(python_executable), "-m", "pip", *tokens[1:]]
    if tokens[0] == "pytest":
        return [str(python_executable), "-m", "pytest", *tokens[1:]]
    return tokens


def _apply_profile_plugin_policy(
    command: list[str],
    *,
    repo_profile: RepoProfile,
) -> list[str]:
    if command[:3] != [command[0], "-m", "pytest"]:
        return command

    plugin_args: list[str] = []
    for plugin in repo_profile.test.plugin_policy.explicit_plugins:
        plugin_args.extend(["-p", plugin])
    if not plugin_args:
        return command
    return [*command[:3], *plugin_args, *command[3:]]


def _apply_patch(worktree: Path, diff_text: str) -> str | None:
    """Apply a patch using the SWE-bench fallback cascade.

    Returns the method that succeeded, or None if all failed.
    """
    if not diff_text.strip():
        return "empty"

    # Write diff to a temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".patch", delete=False) as f:
        f.write(diff_text)
        patch_file = f.name

    try:
        # Try 1: git apply
        result = subprocess.run(
            ["git", "-C", str(worktree), "apply", "--verbose", patch_file],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return "git_apply"

        # Try 2: git apply --reject
        result = subprocess.run(
            ["git", "-C", str(worktree), "apply", "--verbose", "--reject", patch_file],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return "git_apply_reject"

        # Try 3: patch --fuzz=5
        result = subprocess.run(
            ["patch", "--batch", "--fuzz=5", "-p1", "-d", str(worktree), "-i", patch_file],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return "patch_fuzz"

        return None

    finally:
        Path(patch_file).unlink(missing_ok=True)


def _run_pytest(
    worktree: Path,
    test_files: list[str],
    *,
    python_executable: Path,
    repo_profile: RepoProfile | None = None,
    timeout: int = 120,
) -> PytestRunResult:
    """Run pytest on specific test files and parse results.

    Returns (passed_tests, failed_tests, raw_output) or None on execution error.
    """
    worktree = worktree.resolve()
    # Filter to test files that actually exist in the worktree
    existing = [
        f for f in test_files
        if _is_executable_test_file(f) and (worktree / f).exists()
    ]
    if not existing:
        return PytestRunResult(set(), set(), "No test files found in worktree")

    try:
        pytest_cmd = [
            str(python_executable),
            "-m",
            "pytest",
            "--tb=no",
            "-v",
            "--no-header",
            "-p",
            "no:cacheprovider",
        ]
        if _python_module_available(python_executable, "anyio.pytest_plugin"):
            pytest_cmd += ["-p", "anyio.pytest_plugin"]
        if repo_profile is not None:
            pytest_cmd = _apply_profile_plugin_policy(pytest_cmd, repo_profile=repo_profile)
        result = subprocess.run(
            pytest_cmd + existing,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(worktree),
            env=build_probe_environment(repo_profile=repo_profile),
        )
    except subprocess.TimeoutExpired:
        return PytestRunResult(set(), set(), "pytest timed out", execution_error=True)
    except FileNotFoundError:
        return PytestRunResult(set(), set(), "pytest executable not found", execution_error=True)

    output = result.stdout + result.stderr

    # Parse verbose pytest output: "tests/test_foo.py::test_bar PASSED"
    passed: set[str] = set()
    failed: set[str] = set()

    for line in output.splitlines():
        line = line.strip()
        test_id = _parse_pytest_result_line(line, "PASSED")
        if test_id:
            passed.add(test_id)
            continue
        test_id = _parse_pytest_result_line(line, "FAILED")
        if test_id:
            failed.add(test_id)
            continue
        test_id = _parse_pytest_result_line(line, "ERROR")
        if test_id:
            failed.add(test_id)

    if not passed and not failed and _looks_like_pytest_execution_error(output, result.returncode):
        return PytestRunResult(set(), set(), output, execution_error=True)

    return PytestRunResult(passed, failed, output)


_PYTEST_XDIST_RESULT_RE = re.compile(
    r"^\[[^\]]+\]\s+\[\s*\d+%\]\s+(?P<status>PASSED|FAILED|ERROR)\s+(?P<target>\S.*)$"
)


def _parse_pytest_result_line(line: str, status: str) -> str | None:
    xdist_match = _PYTEST_XDIST_RESULT_RE.match(line)
    if xdist_match and xdist_match.group("status") == status:
        return xdist_match.group("target").strip()

    marker = f" {status}"
    if marker not in line:
        return None
    test_id = line.split(marker, 1)[0].strip()
    return test_id or None


def _looks_like_expected_collection_failure(output: str) -> bool:
    """Detect test-patch failures that gold code can legitimately fix."""
    return "ERROR collecting" in output or (
        "collected 0 items" in output
        and "error during collection" in output
    )


def _looks_like_pytest_execution_error(output: str, returncode: int) -> bool:
    """Detect config/collection crashes that should not be treated as 0 failing tests."""
    if returncode not in (0, 1, 5):
        return True
    if "collected 0 items" in output:
        return False

    markers = [
        "Traceback (most recent call last):",
        "PytestConfigWarning",
        "INTERNALERROR>",
        "ERROR: usage:",
        "ImportError while loading conftest",
        "ModuleNotFoundError:",
        "No module named pytest",
    ]
    return any(marker in output for marker in markers)


def _venv_python_path(venv_dir: Path) -> Path:
    if sys.platform.startswith("win"):
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _python_module_available(python_executable: Path, module_name: str) -> bool:
    result = subprocess.run(
        [
            str(python_executable),
            "-c",
            (
                "import importlib.util, sys; "
                f"sys.exit(0 if importlib.util.find_spec({module_name!r}) else 1)"
            ),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.returncode == 0
