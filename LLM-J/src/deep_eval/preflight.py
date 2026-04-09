"""Mechanical pre-flight validation: FAIL_TO_PASS test checks."""

from __future__ import annotations

import subprocess
import tempfile
import time
from pathlib import Path

from src.deep_eval.models import PreflightResult


def run_preflight(
    worktree: Path,
    candidate_id: str,
    patch_diff: str,
    test_diff: str,
    test_files: list[str],
) -> PreflightResult:
    """Run SWE-bench style FAIL_TO_PASS validation.

    1. Apply test_diff at base_commit → run tests → expect some FAIL
    2. Apply patch_diff (gold fix) → run tests → expect PASS
    3. Tests that go FAIL→PASS are the ground truth signal
    """
    start = time.time()

    # Step 0: Install the project so tests can import it
    install_ok = _install_project(worktree)
    if not install_ok:
        return PreflightResult(
            candidate_id=candidate_id,
            status="ERROR",
            reason="Failed to install project in worktree",
            elapsed_seconds=time.time() - start,
        )

    # Step 1: Apply test patch
    test_method = _apply_patch(worktree, test_diff)
    if test_method is None:
        return PreflightResult(
            candidate_id=candidate_id,
            status="FAIL",
            reason="Test patch does not apply cleanly",
            elapsed_seconds=time.time() - start,
        )

    # Step 2: Run tests at base_commit + test_patch (expect failures)
    base_results = _run_pytest(worktree, test_files)
    if base_results is None:
        return PreflightResult(
            candidate_id=candidate_id,
            status="ERROR",
            reason="pytest failed to execute at base commit",
            elapsed_seconds=time.time() - start,
        )

    base_passed, base_failed, base_output = base_results

    if not base_failed:
        return PreflightResult(
            candidate_id=candidate_id,
            status="FAIL",
            reason="No failing tests at base commit — no FAIL_TO_PASS signal",
            base_test_output=base_output[:2000],
            patch_apply_method=test_method,
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
            elapsed_seconds=time.time() - start,
        )

    # Step 4: Run tests again (expect pass)
    fixed_results = _run_pytest(worktree, test_files)
    if fixed_results is None:
        return PreflightResult(
            candidate_id=candidate_id,
            status="ERROR",
            reason="pytest failed to execute after gold patch",
            base_test_output=base_output[:2000],
            patch_apply_method=test_method,
            elapsed_seconds=time.time() - start,
        )

    fixed_passed, fixed_failed, fixed_output = fixed_results

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


def _install_project(worktree: Path) -> bool:
    """Install the project in editable mode so tests can import it.

    Uses sys.executable to ensure we install into the active Python environment.
    Tries common install patterns in order.
    """
    import sys
    pip = [sys.executable, "-m", "pip"]

    install_commands = [
        pip + ["install", "-e", f"{worktree}[test,tests,dev]"],
        pip + ["install", "-e", str(worktree)],
    ]

    for cmd in install_commands:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            return True

    return False


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
    timeout: int = 120,
) -> tuple[set[str], set[str], str] | None:
    """Run pytest on specific test files and parse results.

    Returns (passed_tests, failed_tests, raw_output) or None on execution error.
    """
    # Filter to test files that actually exist in the worktree
    existing = [f for f in test_files if (worktree / f).exists()]
    if not existing:
        return set(), set(), "No test files found in worktree"

    import sys
    try:
        pytest_cmd = [
            sys.executable,
            "-m",
            "pytest",
            "--tb=no",
            "-v",
            "--no-header",
            "-p",
            "no:cacheprovider",
        ]
        result = subprocess.run(
            pytest_cmd + existing,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(worktree),
        )
    except subprocess.TimeoutExpired:
        return None
    except FileNotFoundError:
        return None

    output = result.stdout + result.stderr

    # Parse verbose pytest output: "tests/test_foo.py::test_bar PASSED"
    passed: set[str] = set()
    failed: set[str] = set()

    for line in output.splitlines():
        line = line.strip()
        if " PASSED" in line:
            test_id = line.split(" PASSED")[0].strip()
            if test_id:
                passed.add(test_id)
        elif " FAILED" in line:
            test_id = line.split(" FAILED")[0].strip()
            if test_id:
                failed.add(test_id)
        elif " ERROR" in line:
            test_id = line.split(" ERROR")[0].strip()
            if test_id:
                failed.add(test_id)

    return passed, failed, output
