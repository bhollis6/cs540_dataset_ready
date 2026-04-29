"""Host-local oracle replay for a materialized SWE-bench pilot run."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from swebench.harness.constants import (
    END_TEST_OUTPUT,
    FAIL_TO_PASS,
    KEY_INSTANCE_ID,
    KEY_MODEL,
    KEY_PREDICTION,
    PASS_TO_PASS,
    START_TEST_OUTPUT,
)
from swebench.harness.grading import get_eval_report
from swebench.harness.test_spec.test_spec import TestSpec

from src.harness.pilot_run import ConditionWorkspacePlan
from src.harness.python_env import prepare_workspace_env
from src.substrate.swebench_verified import TaskSnapshot


ORACLE_SCHEMA_VERSION = "0.1.0"


def _run(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=True,
        cwd=str(cwd) if cwd else None,
        env=env,
        text=True,
        capture_output=capture_output,
    )


def _copy_oracle_workspace(source: Path, target: Path) -> Path:
    if target.exists():
        shutil.rmtree(target)

    def ignore(_: str, names: list[str]) -> set[str]:
        ignored: set[str] = set()
        for name in names:
            if name.startswith(".pilot-venv"):
                ignored.add(name)
            elif name in {
                ".codex",
                ".pytest_cache",
                ".ruff_cache",
                ".mypy_cache",
                "__pycache__",
            }:
                ignored.add(name)
        return ignored

    shutil.copytree(source, target, ignore=ignore)
    return target


def _extract_pip_installs(script_lines: list[str]) -> list[list[str]]:
    installs: list[list[str]] = []
    prefix = "python -m pip install "
    for line in script_lines:
        stripped = line.strip()
        if stripped.startswith(prefix):
            installs.append(shlex.split(stripped[len(prefix) :]))
    return installs


def extract_test_command(test_spec: TestSpec) -> str:
    """Extract the actual test invocation from a SWE-bench eval script."""

    saw_start = False
    for line in test_spec.eval_script_list:
        stripped = line.strip()
        if stripped == f": '{START_TEST_OUTPUT}'":
            saw_start = True
            continue
        if not saw_start:
            continue
        if stripped == f": '{END_TEST_OUTPUT}'":
            break
        if stripped:
            return stripped
    raise ValueError(f"Could not extract a test command for {test_spec.instance_id}")


def workspace_patch_text(workspace_dir: Path) -> str:
    """Return the current patch represented by a materialized workspace."""

    result = _run(
        ["git", "-c", "core.fileMode=false", "diff", "--binary"],
        cwd=workspace_dir,
        capture_output=True,
    )
    return result.stdout


def _seed_oracle_env_from_workspace(
    *,
    plan: ConditionWorkspacePlan,
    oracle_workspace_dir: Path,
    test_spec: TestSpec,
) -> Path | None:
    source_venv_dir = plan.workspace_dir / ".pilot-venv-py39"
    target_venv_dir = oracle_workspace_dir / ".pilot-venv-py39"
    if not source_venv_dir.exists():
        return None

    shutil.copytree(source_venv_dir, target_venv_dir, symlinks=True)
    python_path = target_venv_dir / "bin" / "python"
    for install_args in _extract_pip_installs(test_spec.repo_script_list):
        resolved_args = [
            str(oracle_workspace_dir) if arg == "." else arg
            for arg in install_args
        ]
        _run(["uv", "pip", "install", "--python", str(python_path), *resolved_args])
    return python_path


def _capture_test_file_state(
    *,
    workspace_dir: Path,
    relative_paths: list[str],
) -> dict[str, bytes | None]:
    state: dict[str, bytes | None] = {}
    for relative_path in relative_paths:
        path = workspace_dir / relative_path
        state[relative_path] = path.read_bytes() if path.exists() else None
    return state


def _restore_test_file_state(
    *,
    workspace_dir: Path,
    state: dict[str, bytes | None],
) -> None:
    for relative_path, contents in state.items():
        path = workspace_dir / relative_path
        if contents is None:
            path.unlink(missing_ok=True)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents)


@dataclass(frozen=True)
class OracleReplayResult:
    """Official-oracle replay result for one condition."""

    schema_version: str
    instance_id: str
    repo: str
    condition: str
    workspace_dir: str
    oracle_workspace_dir: str
    oracle_log_path: str
    oracle_report_path: str
    oracle_env_path: str
    test_command: str
    command_returncode: int
    duration_seconds: float
    task_success: bool
    fail_to_pass_passed: list[str]
    fail_to_pass_failed: list[str]
    pass_to_pass_passed: list[str]
    pass_to_pass_failed: list[str]
    changed_files: list[str]
    completion_reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "instance_id": self.instance_id,
            "repo": self.repo,
            "condition": self.condition,
            "workspace_dir": self.workspace_dir,
            "oracle_workspace_dir": self.oracle_workspace_dir,
            "oracle_log_path": self.oracle_log_path,
            "oracle_report_path": self.oracle_report_path,
            "oracle_env_path": self.oracle_env_path,
            "test_command": self.test_command,
            "command_returncode": self.command_returncode,
            "duration_seconds": self.duration_seconds,
            "task_success": self.task_success,
            "fail_to_pass_total": len(self.fail_to_pass_passed) + len(self.fail_to_pass_failed),
            "fail_to_pass_passed": list(self.fail_to_pass_passed),
            "fail_to_pass_failed": list(self.fail_to_pass_failed),
            "pass_to_pass_total": len(self.pass_to_pass_passed) + len(self.pass_to_pass_failed),
            "pass_to_pass_passed": list(self.pass_to_pass_passed),
            "pass_to_pass_failed": list(self.pass_to_pass_failed),
            "changed_files": list(self.changed_files),
            "completion_reason": self.completion_reason,
        }


def write_oracle_replay_result(result: OracleReplayResult, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(result.to_dict(), handle, indent=2)
    return path


def _oracle_paths(plan: ConditionWorkspacePlan) -> tuple[Path, Path, Path]:
    logs_dir = plan.logs_dir
    logs_dir.mkdir(parents=True, exist_ok=True)
    return (
        logs_dir / "oracle_test_output.txt",
        logs_dir / "oracle_report.json",
        logs_dir / "oracle_env.json",
    )


def _reset_and_apply_test_patch(
    *,
    snapshot: TaskSnapshot,
    oracle_workspace_dir: Path,
) -> None:
    if snapshot.test_files:
        _run(
            ["git", "checkout", snapshot.base_commit, "--", *snapshot.test_files],
            cwd=oracle_workspace_dir,
        )
    patch_path = oracle_workspace_dir / ".pilot-test.patch"
    patch_path.write_text(snapshot.test_patch, encoding="utf-8")
    try:
        _run(["git", "apply", "-v", patch_path.name], cwd=oracle_workspace_dir)
    finally:
        patch_path.unlink(missing_ok=True)


def _run_oracle_command(
    *,
    oracle_workspace_dir: Path,
    python_path: Path,
    test_command: str,
) -> tuple[int, float, str]:
    env = os.environ.copy()
    current_path = env.get("PATH", "")
    env["PATH"] = os.pathsep.join([str(python_path.parent), current_path]) if current_path else str(python_path.parent)
    env["VIRTUAL_ENV"] = str(python_path.parent.parent)

    started_at = time.monotonic()
    command_argv = shlex.split(test_command)
    while command_argv and "=" in command_argv[0] and not command_argv[0].startswith("-"):
        name, value = command_argv.pop(0).split("=", 1)
        if not name.isidentifier():
            command_argv.insert(0, f"{name}={value}")
            break
        env[name] = value
    if command_argv[:1] == ["pytest"]:
        command_argv = [str(python_path), "-m", "pytest", *command_argv[1:]]
    elif command_argv[:1] == ["tox"] and "--current-env" in command_argv and "--" in command_argv:
        test_args = command_argv[command_argv.index("--") + 1 :]
        command_argv = [str(python_path), "-X", "dev", "-m", "pytest", "-rA", "--durations", "25", *test_args]

    completed = subprocess.run(
        command_argv,
        cwd=str(oracle_workspace_dir),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    duration_seconds = round(time.monotonic() - started_at, 3)
    return completed.returncode, duration_seconds, completed.stdout


def replay_oracle(
    *,
    plan: ConditionWorkspacePlan,
    snapshot: TaskSnapshot,
    test_spec: TestSpec,
    changed_files: list[str] | None = None,
) -> OracleReplayResult:
    """Replay the official SWE-bench oracle against one finished workspace."""

    oracle_log_path, oracle_report_path, oracle_env_path = _oracle_paths(plan)
    source_python_path = plan.workspace_dir.resolve() / ".pilot-venv-py39" / "bin" / "python"
    in_place_state: dict[str, bytes | None] | None = None

    if source_python_path.exists():
        oracle_workspace_dir = plan.workspace_dir
        python_path = source_python_path
        in_place_state = _capture_test_file_state(
            workspace_dir=oracle_workspace_dir,
            relative_paths=snapshot.test_files,
        )
        oracle_env_path.write_text(
            json.dumps(
                {
                    "workspace_dir": str(oracle_workspace_dir),
                    "python_path": str(python_path),
                    "mode": "in_place_existing_workspace_env",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    else:
        oracle_workspace_dir = _copy_oracle_workspace(
            plan.workspace_dir,
            plan.oracle_workspace_dir,
        )
        python_path = _seed_oracle_env_from_workspace(
            plan=plan,
            oracle_workspace_dir=oracle_workspace_dir,
            test_spec=test_spec,
        )
    if not source_python_path.exists() and python_path is None:
        prepare_workspace_env(
            workspace_dir=oracle_workspace_dir,
            test_spec=test_spec,
            output_path=oracle_env_path,
            venv_name=".pilot-venv-py39",
        )
        python_path = oracle_workspace_dir / ".pilot-venv-py39" / "bin" / "python"
    elif not source_python_path.exists():
        oracle_env_path.write_text(
            json.dumps(
                {
                    "workspace_dir": str(oracle_workspace_dir),
                    "venv_dir": str(python_path.parent.parent),
                    "python_path": str(python_path),
                    "seeded_from": str(plan.workspace_dir / ".pilot-venv-py39"),
                    "mode": "seeded_from_workspace",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    try:
        _reset_and_apply_test_patch(snapshot=snapshot, oracle_workspace_dir=oracle_workspace_dir)
        test_command = extract_test_command(test_spec)
        command_returncode, duration_seconds, stdout = _run_oracle_command(
            oracle_workspace_dir=oracle_workspace_dir,
            python_path=python_path,
            test_command=test_command,
        )
    finally:
        if in_place_state is not None:
            _restore_test_file_state(
                workspace_dir=oracle_workspace_dir,
                state=in_place_state,
            )

    oracle_log_path.write_text(
        "\n".join(
            [
                ">>>>> Applied Patch",
                START_TEST_OUTPUT,
                stdout.rstrip(),
                END_TEST_OUTPUT,
                "",
            ]
        ),
        encoding="utf-8",
    )

    report_map = get_eval_report(
        test_spec=test_spec,
        prediction={
            KEY_INSTANCE_ID: snapshot.instance_id,
            KEY_MODEL: "codex-cli",
            KEY_PREDICTION: workspace_patch_text(plan.workspace_dir),
        },
        test_log_path=str(oracle_log_path),
        include_tests_status=True,
    )
    oracle_report_path.write_text(json.dumps(report_map, indent=2), encoding="utf-8")

    instance_report = report_map[snapshot.instance_id]
    tests_status = instance_report["tests_status"]
    fail_to_pass_passed = list(tests_status[FAIL_TO_PASS]["success"])
    fail_to_pass_failed = list(tests_status[FAIL_TO_PASS]["failure"])
    pass_to_pass_passed = list(tests_status[PASS_TO_PASS]["success"])
    pass_to_pass_failed = list(tests_status[PASS_TO_PASS]["failure"])
    observed_total = (
        len(fail_to_pass_passed)
        + len(fail_to_pass_failed)
        + len(pass_to_pass_passed)
        + len(pass_to_pass_failed)
    )
    expected_total = len(test_spec.FAIL_TO_PASS) + len(test_spec.PASS_TO_PASS)
    if expected_total > 0 and observed_total == 0:
        raise RuntimeError(
            f"Oracle replay for {snapshot.instance_id} parsed zero target tests from {oracle_log_path}"
        )
    task_success = bool(instance_report["resolved"])

    return OracleReplayResult(
        schema_version=ORACLE_SCHEMA_VERSION,
        instance_id=snapshot.instance_id,
        repo=snapshot.repo,
        condition=plan.condition,
        workspace_dir=str(plan.workspace_dir),
        oracle_workspace_dir=str(oracle_workspace_dir),
        oracle_log_path=str(oracle_log_path),
        oracle_report_path=str(oracle_report_path),
        oracle_env_path=str(oracle_env_path),
        test_command=test_command,
        command_returncode=command_returncode,
        duration_seconds=duration_seconds,
        task_success=task_success,
        fail_to_pass_passed=fail_to_pass_passed,
        fail_to_pass_failed=fail_to_pass_failed,
        pass_to_pass_passed=pass_to_pass_passed,
        pass_to_pass_failed=pass_to_pass_failed,
        changed_files=list(changed_files or []),
        completion_reason="oracle_pass" if task_success else "oracle_fail",
    )
