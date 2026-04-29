"""Execute Stage 5 agent runs against materialized Stage 4 workspaces."""

from __future__ import annotations

import copy
import json
import os
import re
import shutil
import signal
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.deep_eval.preflight import (
    _apply_patch,
    _build_install_commands,
    _ensure_preflight_venv,
    _install_project,
    _looks_like_pytest_execution_error,
    _python_module_available,
    build_probe_environment,
)
from src.deep_eval.repo_manager import ensure_clone
from src.profiles import load_repo_profile
from src.scraper.models import _is_executable_test_file
from src.workflow.stage4_executor import _materialize_one_run, materialize_stage4_runs


@dataclass
class HarnessRunResult:
    harness_id: str
    runner: str
    command: list[str]
    started_at: str
    completed_at: str
    duration_seconds: float
    exit_code: int
    stdout_path: str
    stderr_path: str
    final_message_path: str | None
    parsed_response: dict[str, Any] | None

def execute_stage5_runs(
    *,
    repo: str,
    run_plan_dir: Path,
    clones_dir: Path,
    output_dir: Path,
    run_ids: list[str] | None = None,
    conditions: list[str] | None = None,
    harnesses: list[str] | None = None,
    limit: int | None = None,
    overwrite: bool = False,
    agent_timeout_seconds: int = 1800,
) -> Path:
    """Execute selected Stage 5 runs and write normalized result artifacts."""
    repo_short = repo.split("/")[-1]
    run_plan_path = run_plan_dir / f"{repo_short}_run_plan.json"
    if not run_plan_path.exists():
        raise FileNotFoundError(f"Run plan not found: {run_plan_path}")

    with open(run_plan_path) as f:
        plan = json.load(f)

    stage5_status = plan.get("stage5_status", {}).get("status")
    if stage5_status == "BLOCKED":
        raise ValueError(f"Run plan is BLOCKED and should not be executed: {run_plan_path}")

    selected_runs = _select_runs(
        plan.get("runs", []),
        run_ids=run_ids,
        conditions=conditions,
        harnesses=harnesses,
        limit=limit,
    )

    materialize_stage4_runs(
        repo=repo,
        run_plan_dir=run_plan_dir,
        clones_dir=clones_dir,
        output_dir=output_dir,
        run_ids=[run["run_id"] for run in selected_runs],
        conditions=None,
        harnesses=None,
        limit=None,
        overwrite=overwrite,
    )

    results: list[dict[str, Any]] = []
    for run in selected_runs:
        results.append(
            _execute_one_run(
                run=run,
                clones_dir=clones_dir,
                output_dir=output_dir,
                overwrite=overwrite,
                agent_timeout_seconds=agent_timeout_seconds,
            )
        )

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo": repo,
        "repo_short": repo_short,
        "run_plan": {
            "path": str(run_plan_path),
            "stage5_status": stage5_status,
        },
        "selection": {
            "requested_run_ids": run_ids or [],
            "requested_conditions": sorted(conditions or []),
            "requested_harnesses": sorted(harnesses or []),
            "limit": limit,
            "selected_runs": len(selected_runs),
        },
        "results": results,
        "summary": {
            "success": sum(1 for result in results if result["status"] == "SUCCESS"),
            "failed": sum(1 for result in results if result["status"] == "FAIL"),
            "error": sum(1 for result in results if result["status"] == "ERROR"),
            "skipped": sum(1 for result in results if result["status"] == "SKIPPED"),
        },
    }

    summary_path = output_dir / f"{repo_short}_stage5_execution.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    markdown_path = output_dir / f"{repo_short}_stage5_execution.md"
    markdown_path.write_text(_render_execution_markdown(summary), encoding="utf-8")
    return summary_path


def _select_runs(
    runs: list[dict[str, Any]],
    *,
    run_ids: list[str] | None,
    conditions: list[str] | None,
    harnesses: list[str] | None,
    limit: int | None,
) -> list[dict[str, Any]]:
    selected = runs
    if run_ids:
        run_id_set = set(run_ids)
        selected = [run for run in selected if run.get("run_id") in run_id_set]
    if conditions:
        condition_set = set(conditions)
        selected = [run for run in selected if run.get("condition") in condition_set]
    if harnesses:
        harness_set = set(harnesses)
        selected = [
            run
            for run in selected
            if run.get("harness", {}).get("runner") in harness_set
            or run.get("harness", {}).get("id") in harness_set
        ]
    if limit is not None:
        selected = selected[:limit]
    return selected


def _execute_one_run(
    *,
    run: dict[str, Any],
    clones_dir: Path,
    output_dir: Path,
    overwrite: bool,
    agent_timeout_seconds: int,
) -> dict[str, Any]:
    run_root = output_dir / run["output_paths"]["root"]
    metadata_path = run_root / "metadata.json"
    result_path = run_root / "result.json"
    metrics_path = run_root / "metrics.json"
    logs_dir = run_root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    if result_path.exists() and metrics_path.exists() and not overwrite:
        with open(result_path) as f:
            result = json.load(f)
        return {
            "run_id": run["run_id"],
            "status": "SKIPPED",
            "reason": "Run already has result.json and metrics.json",
            "run_root": str(run_root),
            "result_path": str(result_path),
            "metrics_path": str(metrics_path),
            "existing_result_status": result.get("status"),
        }

    if not metadata_path.exists():
        failure = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "run_id": run["run_id"],
            "status": "ERROR",
            "completion_reason": "missing_stage4_metadata",
            "reason": f"metadata.json not found under {run_root}",
        }
        with open(result_path, "w") as f:
            json.dump(failure, f, indent=2)
        return {
            "run_id": run["run_id"],
            "status": "ERROR",
            "reason": failure["reason"],
            "run_root": str(run_root),
        }

    with open(metadata_path) as f:
        metadata = json.load(f)

    workspace_path = Path(metadata["workspace"]["path"])
    prompt = _build_agent_prompt(metadata)
    prompt_path = logs_dir / "agent_prompt.md"
    prompt_path.write_text(prompt, encoding="utf-8")
    _ensure_stage4_baseline_commit(workspace_path)

    try:
        harness_result = _run_agent_harness(
            run=run,
            workspace_path=workspace_path,
            logs_dir=logs_dir,
            prompt=prompt,
            timeout_seconds=agent_timeout_seconds,
        )
        diff_path = _write_git_diff(workspace_path, logs_dir / "final_repo_diff.patch")
        changed_files = _changed_files(workspace_path)

        oracle = _run_post_run_oracle(
            run=run,
            run_root=run_root,
            clones_dir=clones_dir,
            workspace_path=workspace_path,
            candidate_path=(
                Path(source_candidate_path)
                if (source_candidate_path := metadata.get("task_prompt", {}).get("source_candidate_path"))
                else None
            ),
            fail_to_pass_tests=metadata.get("oracle", {}).get("fail_to_pass_tests", []),
            pass_to_pass_tests=metadata.get("oracle", {}).get("pass_to_pass_tests", []),
            output_path=logs_dir / "post_run_test_output.txt",
        )
    except Exception as exc:
        failure = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "run_id": run["run_id"],
            "repo": run["repo"],
            "candidate_id": run["candidate_id"],
            "condition": run["condition"],
            "replication": run["replication"],
            "status": "ERROR",
            "completion_reason": "runner_exception",
            "reason": f"{type(exc).__name__}: {exc}",
        }
        with open(result_path, "w") as f:
            json.dump(failure, f, indent=2)
        return {
            "run_id": run["run_id"],
            "status": "ERROR",
            "completion_reason": "runner_exception",
            "reason": failure["reason"],
            "run_root": str(run_root),
        }

    completion_reason = _completion_reason(harness_result.exit_code, oracle)
    status = _result_status(harness_result.exit_code, oracle)

    result_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_id": run["run_id"],
        "repo": run["repo"],
        "candidate_id": run["candidate_id"],
        "condition": run["condition"],
        "replication": run["replication"],
        "status": status,
        "completion_reason": completion_reason,
        "harness": run["harness"],
        "workspace": str(workspace_path),
        "stage4_condition": metadata.get("condition"),
        "agent": {
            "exit_code": harness_result.exit_code,
            "started_at": harness_result.started_at,
            "completed_at": harness_result.completed_at,
            "duration_seconds": harness_result.duration_seconds,
            "command": harness_result.command,
            "stdout_path": harness_result.stdout_path,
            "stderr_path": harness_result.stderr_path,
            "final_message_path": harness_result.final_message_path,
            "parsed_response": harness_result.parsed_response,
        },
        "oracle": oracle,
        "artifacts": {
            "metadata": str(metadata_path),
            "agent_prompt": str(prompt_path),
            "final_repo_diff": str(diff_path),
            "post_run_test_output": str(logs_dir / "post_run_test_output.txt"),
        },
    }
    with open(result_path, "w") as f:
        json.dump(result_payload, f, indent=2)

    metrics_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_id": run["run_id"],
        "task_success": oracle["task_success"],
        "total_tokens": None,
        "total_cost_usd": None,
        "edits_applied": len(changed_files),
        "changed_files": changed_files,
        "test_commands_run": [oracle["command"]],
        "completion_reason": completion_reason,
        "agent_duration_seconds": harness_result.duration_seconds,
        "oracle_duration_seconds": oracle["duration_seconds"],
        "total_duration_seconds": harness_result.duration_seconds + oracle["duration_seconds"],
        "bootstrap": {
            "tokens_before_first_edit": None,
            "files_opened_before_first_edit": None,
            "dead_end_file_opens": None,
            "relevant_files_opened": None,
            "exploration_efficiency": None,
            "time_to_first_edit_seconds": None,
        },
        "execution": {
            "task_success": oracle["task_success"],
            "total_tokens": None,
            "total_cost_usd": None,
            "edits_applied": len(changed_files),
            "test_commands_run": 1,
            "completion_reason": completion_reason,
        },
    }
    with open(metrics_path, "w") as f:
        json.dump(metrics_payload, f, indent=2)

    return {
        "run_id": run["run_id"],
        "status": status,
        "completion_reason": completion_reason,
        "run_root": str(run_root),
        "result_path": str(result_path),
        "metrics_path": str(metrics_path),
    }


def _build_agent_prompt(metadata: dict[str, Any]) -> str:
    task_prompt = metadata.get("task_prompt", {})
    oracle = metadata.get("oracle", {})
    fail_to_pass = oracle.get("fail_to_pass_tests", [])
    pass_to_pass = oracle.get("pass_to_pass_tests", [])
    description = _condense_task_description(task_prompt.get("description") or "")
    lines = [
        "You are solving a historical GitHub task inside a local git worktree.",
        "You get one final submission for this task.",
        "Modify the repository directly so the listed FAIL_TO_PASS tests pass.",
        "You may inspect files, edit code, and run as many local checks as you want before you submit.",
        "Keep changes focused on the task. Do not rewrite unrelated parts of the repo.",
        "Work however you think is best. Read, test, and validate as much as you need before submitting.",
        "Submit only when you are ready.",
        "",
        f"# {task_prompt.get('title') or 'Historical Task'}",
        "",
        description,
        "",
        "## Required FAIL_TO_PASS Tests",
    ]
    if fail_to_pass:
        lines.extend(f"- `{test_name}`" for test_name in fail_to_pass)
    else:
        lines.append("- No explicit FAIL_TO_PASS tests were recorded.")

    if pass_to_pass:
        summarized = _summarize_test_targets(pass_to_pass, max_items=8)
        lines.extend([
            "",
            "## PASS_TO_PASS Regression Surface",
            "Final oracle evaluation will check the broader regression surface below.",
            "You do not need to run every listed regression locally; use a focused subset if needed.",
        ])
        lines.extend(summarized)

    lines.extend([
        "",
        "When you finish, return a short structured summary of what you changed and any blockers.",
    ])
    return "\n".join(lines).rstrip() + "\n"


def _condense_task_description(
    description: str,
    *,
    max_chars: int = 2800,
) -> str:
    stripped = description.strip()
    if not stripped:
        return "No issue or PR description was recorded."

    lines: list[str] = []
    in_code_block = False
    code_block_omitted = False
    for raw_line in stripped.splitlines():
        line = raw_line.rstrip()
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            if not code_block_omitted:
                lines.append("```")
            continue
        if in_code_block:
            if not code_block_omitted:
                lines.append("[code example omitted for brevity]")
                lines.append("```")
                code_block_omitted = True
            continue
        lines.append(line)

    collapsed: list[str] = []
    previous_blank = False
    for line in lines:
        is_blank = line.strip() == ""
        if is_blank and previous_blank:
            continue
        collapsed.append(line)
        previous_blank = is_blank

    condensed = "\n".join(collapsed).strip()
    if len(condensed) <= max_chars:
        return condensed

    truncated = condensed[:max_chars].rstrip()
    split_at = max(truncated.rfind("\n"), truncated.rfind(". "), truncated.rfind("; "))
    if split_at >= max_chars // 2:
        truncated = truncated[:split_at].rstrip()
    return truncated + "\n\n[description truncated for prompt efficiency]"


def _summarize_test_targets(test_targets: list[str], *, max_items: int) -> list[str]:
    if len(test_targets) <= max_items:
        return [f"- `{test_name}`" for test_name in test_targets]

    file_counts: dict[str, int] = {}
    for target in test_targets:
        file_target = target.split("::", 1)[0].strip() or target
        file_counts[file_target] = file_counts.get(file_target, 0) + 1

    lines = [f"- `{len(test_targets)}` regression checks across `{len(file_counts)}` files"]
    for file_target, count in sorted(file_counts.items()):
        label = "check" if count == 1 else "checks"
        lines.append(f"- `{file_target}` ({count} {label})")
    return lines


def _response_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "outcome": {
                "type": "string",
                "enum": ["completed", "blocked", "partial"],
            },
            "tests_run": {
                "type": "array",
                "items": {"type": "string"},
            },
            "files_changed": {
                "type": "array",
                "items": {"type": "string"},
            },
            "blockers": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": ["summary", "outcome", "tests_run", "files_changed", "blockers"],
        "additionalProperties": False,
    }


def _run_agent_harness(
    *,
    run: dict[str, Any],
    workspace_path: Path,
    logs_dir: Path,
    prompt: str,
    timeout_seconds: int,
) -> HarnessRunResult:
    workspace_path = workspace_path.resolve()
    logs_dir = logs_dir.resolve()
    harness = run["harness"]
    runner = harness["runner"]
    stdout_path = logs_dir / "agent_stdout.log"
    stderr_path = logs_dir / "agent_stderr.log"
    final_message_path = logs_dir / "agent_final_message.json"
    schema = _response_schema()

    if runner == "claude-code":
        binary = shutil.which("claude")
        if binary is None:
            raise RuntimeError("Could not find local 'claude' binary for Stage 5 runs")
        command = [
            binary,
            "-p",
            prompt,
            "--effort",
            "medium",
            "--output-format",
            "json",
            "--json-schema",
            json.dumps(schema),
            "--permission-mode",
            "bypassPermissions",
            "--dangerously-skip-permissions",
            "--allowedTools",
            "Bash,Read,Edit,MultiEdit,Write,Glob,Grep,LS",
            "--add-dir",
            str(workspace_path),
            "--setting-sources",
            "local",
            "--disable-slash-commands",
            "--strict-mcp-config",
            "--no-session-persistence",
            "--debug-file",
            str(logs_dir / "claude_debug.log"),
        ]
    elif runner == "codex-cli":
        binary = shutil.which("codex")
        if binary is None:
            raise RuntimeError("Could not find local 'codex' binary for Stage 5 runs")
        schema_path = logs_dir / "response_schema.json"
        schema_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
        command = [
            binary,
            "exec",
            prompt,
            "--full-auto",
            "--json",
            "-C",
            str(workspace_path),
            "--ignore-user-config",
            "--ignore-rules",
            "-o",
            str(final_message_path),
            "--output-schema",
            str(schema_path),
        ]
    else:
        raise ValueError(f"Unsupported Stage 5 harness runner: {runner}")

    started = datetime.now(timezone.utc)
    start_time = time.time()
    completed = started
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    if runner == "codex-cli":
        env["CODEX_HOME"] = str(_prepare_codex_home())

    try:
        exit_code, stdout, stderr = _run_process_with_timeout(
            command,
            cwd=str(workspace_path),
            timeout=timeout_seconds,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = _coerce_text(exc.stdout)
        stderr = _coerce_text(exc.stderr)
        stdout_path.write_text(stdout, encoding="utf-8")
        stderr_path.write_text(stderr, encoding="utf-8")
        completed = datetime.now(timezone.utc)
        return HarnessRunResult(
            harness_id=harness["id"],
            runner=runner,
            command=command,
            started_at=started.isoformat(),
            completed_at=completed.isoformat(),
            duration_seconds=time.time() - start_time,
            exit_code=124,
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
            final_message_path=None,
            parsed_response={
                "summary": "Agent timed out before producing a structured final message.",
                "outcome": "blocked",
                "tests_run": [],
                "files_changed": [],
                "blockers": [f"timeout after {timeout_seconds} seconds"],
            },
        )
    completed = datetime.now(timezone.utc)
    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")

    parsed_response = _parse_agent_response(
        runner=runner,
        stdout=stdout,
        final_message_path=final_message_path if final_message_path.exists() else None,
    )
    if final_message_path.exists() and runner == "claude-code":
        final_message_path.write_text(json.dumps(parsed_response, indent=2), encoding="utf-8")

    return HarnessRunResult(
        harness_id=harness["id"],
        runner=runner,
        command=command,
        started_at=started.isoformat(),
        completed_at=completed.isoformat(),
        duration_seconds=time.time() - start_time,
        exit_code=exit_code,
        stdout_path=str(stdout_path),
        stderr_path=str(stderr_path),
        final_message_path=str(final_message_path) if final_message_path.exists() else None,
        parsed_response=parsed_response,
    )


def _run_process_with_timeout(
    command: list[str],
    *,
    cwd: str,
    timeout: int,
    env: dict[str, str],
) -> tuple[int, str, str]:
    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        _terminate_process_group(process)
        stdout = _coerce_text(exc.stdout)
        stderr = _coerce_text(exc.stderr)
        raise subprocess.TimeoutExpired(command, timeout, output=stdout, stderr=stderr) from None
    return process.returncode, stdout, stderr


def _terminate_process_group(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=5)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    process.wait(timeout=5)


def _parse_agent_response(
    *,
    runner: str,
    stdout: str,
    final_message_path: Path | None,
) -> dict[str, Any] | None:
    if runner == "codex-cli" and final_message_path is not None:
        try:
            return json.loads(final_message_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None

    if runner == "claude-code":
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            return None
    return None


def _run_post_run_oracle(
    *,
    run: dict[str, Any],
    run_root: Path,
    clones_dir: Path,
    workspace_path: Path,
    candidate_path: Path | None,
    fail_to_pass_tests: list[str],
    pass_to_pass_tests: list[str],
    output_path: Path,
    timeout_seconds: int = 300,
) -> dict[str, Any]:
    started = time.time()
    evaluation = _prepare_oracle_evaluation_workspace(
        run=run,
        run_root=run_root,
        clones_dir=clones_dir,
        agent_workspace=workspace_path,
        candidate_path=candidate_path,
    )
    if not evaluation["success"]:
        output_path.write_text(evaluation["output"], encoding="utf-8")
        return {
            "task_success": False,
            "execution_error": True,
            "reason": evaluation["reason"],
            "duration_seconds": time.time() - started,
            "command": "",
            "passed": [],
            "failed": [],
            "fail_to_pass_tests": fail_to_pass_tests,
            "pass_to_pass_tests": pass_to_pass_tests,
            "fail_to_pass_passed": [],
            "fail_to_pass_failed": fail_to_pass_tests,
            "pass_to_pass_failed": [],
            "missing_targets": [],
            "output_path": str(output_path),
            "oracle_setup": evaluation,
        }

    oracle_workspace = Path(evaluation["workspace"])
    oracle_setup = _prepare_oracle_tests(oracle_workspace, candidate_path)
    if not oracle_setup["success"]:
        output_path.write_text(oracle_setup["output"], encoding="utf-8")
        return {
            "task_success": False,
            "execution_error": True,
            "reason": oracle_setup["reason"],
            "duration_seconds": time.time() - started,
            "command": "",
            "passed": [],
            "failed": [],
            "fail_to_pass_tests": fail_to_pass_tests,
            "pass_to_pass_tests": pass_to_pass_tests,
            "fail_to_pass_passed": [],
            "fail_to_pass_failed": fail_to_pass_tests,
            "pass_to_pass_failed": [],
            "missing_targets": [],
            "output_path": str(output_path),
            "oracle_setup": {
                **oracle_setup,
                "evaluation": evaluation,
            },
        }

    python_executable, venv_output = _ensure_preflight_venv(oracle_workspace)
    if python_executable is None:
        output_path.write_text(venv_output, encoding="utf-8")
        return {
            "task_success": False,
            "execution_error": True,
            "reason": "failed_to_create_stage5_venv",
            "duration_seconds": time.time() - started,
            "command": "",
            "passed": [],
            "failed": [],
            "fail_to_pass_tests": fail_to_pass_tests,
            "pass_to_pass_tests": pass_to_pass_tests,
            "fail_to_pass_passed": [],
            "fail_to_pass_failed": fail_to_pass_tests,
            "pass_to_pass_failed": [],
            "missing_targets": [],
            "output_path": str(output_path),
            "oracle_setup": {
                **oracle_setup,
                "evaluation": evaluation,
            },
        }

    repo_profile = load_repo_profile(run["repo"])
    install_success, install_output = _install_workspace(
        oracle_workspace,
        python_executable=python_executable,
        repo_profile=repo_profile,
    )
    targets = sorted(dict.fromkeys([*fail_to_pass_tests, *pass_to_pass_tests]))
    pytest_targets = _pytest_file_targets(targets)
    command = _pytest_command_display(python_executable, pytest_targets)
    if not install_success:
        output_path.write_text(install_output, encoding="utf-8")
        return {
            "task_success": False,
            "execution_error": True,
            "reason": "failed_to_install_project_for_stage5_oracle",
            "duration_seconds": time.time() - started,
            "command": command,
            "passed": [],
            "failed": [],
            "fail_to_pass_tests": fail_to_pass_tests,
            "pass_to_pass_tests": pass_to_pass_tests,
            "fail_to_pass_passed": [],
            "fail_to_pass_failed": fail_to_pass_tests,
            "pass_to_pass_failed": pass_to_pass_tests,
            "missing_targets": [],
            "output_path": str(output_path),
            "oracle_setup": {
                **oracle_setup,
                "evaluation": evaluation,
            },
        }

    oracle = _run_pytest_targets(
        oracle_workspace,
        pytest_targets,
        python_executable=python_executable,
        timeout_seconds=timeout_seconds,
        repo_profile=repo_profile,
    )
    output_path.write_text(oracle["output"], encoding="utf-8")

    target_evaluation = _evaluate_expected_targets(
        expected_targets=targets,
        passed_targets=oracle["passed"],
        failed_targets=oracle["failed"],
    )
    fail_to_pass_passed = sorted(
        test_name for test_name in fail_to_pass_tests if target_evaluation["status_by_target"].get(test_name) == "passed"
    )
    fail_to_pass_failed = sorted(
        test_name for test_name in fail_to_pass_tests if target_evaluation["status_by_target"].get(test_name) != "passed"
    )
    pass_to_pass_failed = sorted(
        test_name for test_name in pass_to_pass_tests if target_evaluation["status_by_target"].get(test_name) == "failed"
    )

    task_success = (
        not oracle["execution_error"]
        and not fail_to_pass_failed
        and not pass_to_pass_failed
        and not target_evaluation["missing_targets"]
    )
    reason = "oracle_pass" if task_success else "oracle_fail"
    if oracle["execution_error"]:
        reason = "oracle_targets_not_found" if oracle["missing_targets"] else "oracle_execution_error"
    elif target_evaluation["missing_targets"]:
        reason = "oracle_targets_not_found"
    return {
        "task_success": task_success,
        "execution_error": oracle["execution_error"],
        "reason": reason,
        "duration_seconds": time.time() - started,
        "command": command,
        "passed": oracle["passed"],
        "failed": oracle["failed"],
        "fail_to_pass_tests": fail_to_pass_tests,
        "pass_to_pass_tests": pass_to_pass_tests,
        "fail_to_pass_passed": fail_to_pass_passed,
        "fail_to_pass_failed": fail_to_pass_failed,
        "pass_to_pass_failed": pass_to_pass_failed,
        "missing_targets": target_evaluation["missing_targets"] or oracle["missing_targets"],
        "output_path": str(output_path),
        "oracle_setup": {
            **oracle_setup,
            "evaluation": evaluation,
        },
    }


def _prepare_oracle_evaluation_workspace(
    *,
    run: dict[str, Any],
    run_root: Path,
    clones_dir: Path,
    agent_workspace: Path,
    candidate_path: Path | None,
) -> dict[str, Any]:
    oracle_output_dir = run_root / ".oracle_eval"
    oracle_run = copy.deepcopy(run)
    oracle_run["output_paths"] = {"root": ".oracle_eval"}

    bare_repo = ensure_clone(run["repo"], clones_dir)
    materialized = _materialize_one_run(
        bare_repo=bare_repo,
        run=oracle_run,
        output_dir=run_root,
        overwrite=True,
    )
    if materialized.get("status") != "PASS":
        return {
            "success": False,
            "reason": "failed_to_materialize_oracle_workspace",
            "output": materialized.get("reason", "Could not materialize fresh oracle workspace."),
        }

    oracle_workspace = oracle_output_dir / "workspace"
    source_patch, untracked_source_files = _capture_agent_source_changes(
        agent_workspace=agent_workspace,
        candidate_path=candidate_path,
    )
    patch_apply_method = _apply_patch(oracle_workspace, source_patch)
    if patch_apply_method is None:
        return {
            "success": False,
            "reason": "failed_to_apply_agent_source_patch",
            "output": "Could not replay non-test agent changes into the oracle workspace.",
            "workspace": str(oracle_workspace),
        }

    copied_untracked: list[str] = []
    for relative_path in untracked_source_files:
        src = agent_workspace / relative_path
        dst = oracle_workspace / relative_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied_untracked.append(relative_path)

    return {
        "success": True,
        "reason": "oracle_workspace_prepared",
        "output": "",
        "workspace": str(oracle_workspace),
        "source_patch_apply_method": patch_apply_method,
        "untracked_source_files": copied_untracked,
    }


def _prepare_oracle_tests(workspace_path: Path, candidate_path: Path | None) -> dict[str, Any]:
    if candidate_path is None:
        return {
            "success": False,
            "reason": "missing_candidate_metadata",
            "output": "Missing source_candidate_path; cannot restore hidden oracle tests.",
            "patch_apply_method": None,
            "restored_test_files": [],
        }
    if not candidate_path.exists():
        return {
            "success": False,
            "reason": "candidate_metadata_not_found",
            "output": f"Candidate metadata file not found: {candidate_path}",
            "patch_apply_method": None,
            "restored_test_files": [],
        }

    with open(candidate_path) as f:
        candidate = json.load(f)

    test_files = [str(path) for path in candidate.get("test_files", [])]
    restored: list[str] = []
    restore_messages: list[str] = []
    for relative_path in test_files:
        result = subprocess.run(
            ["git", "-C", str(workspace_path), "checkout", "--", relative_path],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            restored.append(relative_path)
        elif result.stderr.strip():
            restore_messages.append(f"{relative_path}: {result.stderr.strip()}")

    patch_apply_method = _apply_patch(workspace_path, candidate.get("test_diff", ""))
    if patch_apply_method is None:
        return {
            "success": False,
            "reason": "test_patch_did_not_apply",
            "output": "\n".join([
                "Failed to apply hidden oracle test patch.",
                *restore_messages,
            ]).strip(),
            "patch_apply_method": None,
            "restored_test_files": restored,
        }

    return {
        "success": True,
        "reason": "oracle_tests_prepared",
        "output": "\n".join(restore_messages),
        "patch_apply_method": patch_apply_method,
        "restored_test_files": restored,
    }


def _install_workspace(
    workspace_path: Path,
    *,
    python_executable: Path,
    repo_profile: Any | None = None,
) -> tuple[bool, str]:
    install_result = _install_project(
        workspace_path,
        python_executable=python_executable,
        repo_profile=repo_profile,
        install_timeout_seconds=180,
    )
    return install_result.success, install_result.output


def _build_dependency_only_install_commands(install_commands: list[list[str]]) -> list[list[str]]:
    commands: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()
    for command in install_commands:
        if "-r" not in command:
            continue
        requirement_path = Path(command[command.index("-r") + 1])
        filtered_path = _write_filtered_requirements_copy(requirement_path)
        if filtered_path is None:
            continue
        filtered_command = command.copy()
        filtered_command[filtered_command.index("-r") + 1] = str(filtered_path)
        key = tuple(filtered_command)
        if key not in seen:
            commands.append(filtered_command)
            seen.add(key)
    return commands


def _write_filtered_requirements_copy(requirement_path: Path) -> Path | None:
    requirement_path = requirement_path.resolve()
    lines = requirement_path.read_text(encoding="utf-8").splitlines()
    filtered_lines = [line for line in lines if not _is_self_requirement_line(line)]
    if filtered_lines == lines:
        return None

    filtered_path = requirement_path.with_name(f".llmj-{requirement_path.stem}-oracle.txt")
    filtered_path.write_text("\n".join(filtered_lines) + "\n", encoding="utf-8")
    return filtered_path


def _is_self_requirement_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return False
    return bool(re.match(r"^(?:-e\s+)?\.(?:\[.*\])?$", stripped))


def _run_pytest_targets(
    workspace_path: Path,
    test_targets: list[str],
    *,
    python_executable: Path,
    timeout_seconds: int,
    repo_profile: Any | None = None,
) -> dict[str, Any]:
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
        plugin_args: list[str] = []
        for plugin in repo_profile.test.plugin_policy.explicit_plugins:
            plugin_args.extend(["-p", plugin])
        if plugin_args:
            pytest_cmd = [*pytest_cmd[:3], *plugin_args, *pytest_cmd[3:]]

    try:
        pytest_env = {
            **build_probe_environment(repo_profile=repo_profile),
            "PIP_CACHE_DIR": "/tmp/llmj-pip-cache",
            "PYTHONUTF8": "1",
        }
        python_path_entries = [str(workspace_path), str(workspace_path / "src")]
        existing_pythonpath = pytest_env.get("PYTHONPATH")
        if existing_pythonpath:
            python_path_entries.append(existing_pythonpath)
        pytest_env["PYTHONPATH"] = os.pathsep.join(python_path_entries)
        result = subprocess.run(
            pytest_cmd + test_targets,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            cwd=str(workspace_path),
            env=pytest_env,
        )
    except subprocess.TimeoutExpired as exc:
        output = _coerce_text(exc.stdout) + _coerce_text(exc.stderr)
        parsed = _parse_pytest_target_results(output)
        return {
            "passed": parsed["passed"],
            "failed": parsed["failed"],
            "output": output or "pytest timed out",
            "execution_error": not parsed["passed"] and not parsed["failed"],
            "missing_targets": _parse_missing_pytest_targets(output),
        }
    except FileNotFoundError:
        return {
            "passed": [],
            "failed": [],
            "output": "pytest executable not found",
            "execution_error": True,
            "missing_targets": [],
        }
    output = result.stdout + result.stderr

    parsed_results = _parse_pytest_target_results(output)
    passed = set(parsed_results["passed"])
    failed = set(parsed_results["failed"])

    execution_error = False
    if not passed and not failed and _looks_like_pytest_execution_error(output, result.returncode):
        execution_error = True

    return {
        "passed": sorted(passed),
        "failed": sorted(failed),
        "output": output,
        "execution_error": execution_error,
        "missing_targets": _parse_missing_pytest_targets(output),
    }


def _parse_pytest_target_results(output: str) -> dict[str, list[str]]:
    passed: set[str] = set()
    failed: set[str] = set()
    for line in output.splitlines():
        parsed = _parse_pytest_target_result_line(line)
        if parsed is None:
            continue
        outcome, nodeid = parsed
        if outcome == "PASSED":
            passed.add(nodeid)
        else:
            failed.add(nodeid)

    return {
        "passed": sorted(passed),
        "failed": sorted(failed),
    }


_PYTEST_TARGET_RESULT_RE = re.compile(
    r"^(?:(?:\[[^\]]+\]\s+)?(?:\[\s*\d+%\]\s+)?)"
    r"(?P<outcome>PASSED|FAILED|ERROR)\s+"
    r"(?P<nodeid>.+?)(?:\s+\[[^\]]+\])?$"
)
_PYTEST_TARGET_TRAILING_RESULT_RE = re.compile(
    r"^(?P<nodeid>.+?)\s+(?P<outcome>PASSED|FAILED|ERROR)(?:\s+\[[^\]]+\])?$"
)


def _parse_pytest_target_result_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    match = _PYTEST_TARGET_RESULT_RE.match(stripped)
    if match is None:
        match = _PYTEST_TARGET_TRAILING_RESULT_RE.match(stripped)
    if match is None:
        return None
    nodeid = match.group("nodeid").strip()
    if not nodeid or "::" not in nodeid:
        return None
    return match.group("outcome"), nodeid


def _parse_missing_pytest_targets(output: str) -> list[str]:
    missing: list[str] = []
    for line in output.splitlines():
        line = line.strip()
        prefix = "ERROR: not found: "
        if not line.startswith(prefix):
            continue
        target = line[len(prefix):].split(" ", 1)[0].strip()
        if target:
            missing.append(target)
    return missing


def _coerce_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _prepare_codex_home() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    target = repo_root / ".codex-stage5-home"
    target.mkdir(parents=True, exist_ok=True)

    source = Path.home() / ".codex"
    _sync_codex_home_files(source=source, target=target)

    for dirname in ("tmp", "sessions", "log", "cache", "plugins"):
        (target / dirname).mkdir(parents=True, exist_ok=True)

    return target


def _sync_codex_home_files(*, source: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for filename in ("auth.json", "config.toml", "installation_id", "version.json", "AGENTS.md"):
        src = source / filename
        dst = target / filename
        if src.exists():
            shutil.copy2(src, dst)

    rules_src = source / "rules"
    rules_dst = target / "rules"
    if rules_src.exists() and not rules_dst.exists():
        shutil.copytree(rules_src, rules_dst)


def _pytest_command_display(python_executable: Path, test_targets: list[str]) -> str:
    cmd = [
        str(python_executable),
        "-m",
        "pytest",
        "--tb=no",
        "-v",
        "--no-header",
        "-p",
        "no:cacheprovider",
        *test_targets,
    ]
    return " ".join(cmd)


def _pytest_file_targets(test_targets: list[str]) -> list[str]:
    files: list[str] = []
    seen: set[str] = set()
    for target in test_targets:
        file_target = target.split("::", 1)[0].strip()
        if not file_target or file_target in seen:
            continue
        seen.add(file_target)
        files.append(file_target)
    return files


def _write_git_diff(workspace_path: Path, output_path: Path) -> Path:
    result = subprocess.run(
        ["git", "-C", str(workspace_path), "diff", "--binary", "HEAD"],
        capture_output=True,
        text=True,
    )
    output_path.write_text(result.stdout, encoding="utf-8")
    return output_path


def _ensure_stage4_baseline_commit(workspace_path: Path) -> str | None:
    entries = _workspace_status_entries(workspace_path)
    if not entries:
        return None

    subprocess.run(
        ["git", "-C", str(workspace_path), "config", "user.name", "LLM-J Stage5"],
        capture_output=True,
        text=True,
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(workspace_path), "config", "user.email", "llmj-stage5@example.com"],
        capture_output=True,
        text=True,
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(workspace_path), "add", "-A"],
        capture_output=True,
        text=True,
        check=True,
    )
    commit = subprocess.run(
        ["git", "-C", str(workspace_path), "commit", "-m", "LLM-J Stage4 baseline"],
        capture_output=True,
        text=True,
    )
    if commit.returncode != 0 and "nothing to commit" not in (commit.stdout + commit.stderr).lower():
        raise RuntimeError(
            "Failed to snapshot Stage 4 baseline before agent run: "
            + (commit.stdout + commit.stderr).strip()
        )

    head = subprocess.run(
        ["git", "-C", str(workspace_path), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return head.stdout.strip() or None


def _capture_agent_source_changes(
    *,
    agent_workspace: Path,
    candidate_path: Path | None,
) -> tuple[str, list[str]]:
    entries = _workspace_status_entries(agent_workspace)
    excluded = _oracle_excluded_paths(candidate_path)
    tracked_source_files: list[str] = []
    untracked_source_files: list[str] = []
    for entry in entries:
        relative_path = entry["path"]
        if _is_oracle_excluded_path(relative_path, excluded):
            continue
        if entry["status"] == "??":
            untracked_source_files.append(relative_path)
        else:
            tracked_source_files.append(relative_path)

    patch = ""
    if tracked_source_files:
        result = subprocess.run(
            ["git", "-C", str(agent_workspace), "diff", "--binary", "HEAD", "--", *tracked_source_files],
            capture_output=True,
            text=True,
        )
        patch = result.stdout

    return patch, sorted(untracked_source_files)


def _workspace_status_entries(workspace_path: Path) -> list[dict[str, str]]:
    result = subprocess.run(
        ["git", "-C", str(workspace_path), "status", "--short"],
        capture_output=True,
        text=True,
    )
    entries: list[dict[str, str]] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        status = line[:2]
        relative_path = line[3:].strip()
        if " -> " in relative_path:
            relative_path = relative_path.split(" -> ", 1)[1].strip()
        entries.append({
            "status": status,
            "path": relative_path,
        })
    return entries


def _changed_files(workspace_path: Path) -> list[str]:
    changed: list[str] = []
    for entry in _workspace_status_entries(workspace_path):
        relative_path = entry["path"]
        if _is_harness_artifact_path(relative_path):
            continue
        changed.append(relative_path)
    return changed


def _is_harness_artifact_path(relative_path: str) -> bool:
    normalized = relative_path.strip().replace("\\", "/")
    if not normalized:
        return False
    return normalized == ".codex" or normalized.startswith(".codex/") or normalized == ".claude" or normalized.startswith(".claude/")


def _oracle_excluded_paths(candidate_path: Path | None) -> set[str]:
    excluded: set[str] = set()
    if candidate_path is None or not candidate_path.exists():
        return excluded
    with open(candidate_path) as f:
        candidate = json.load(f)
    for key in ("test_files", "test_support_files"):
        for relative_path in candidate.get(key) or []:
            excluded.add(str(relative_path).replace("\\", "/"))
    return excluded


def _is_oracle_excluded_path(relative_path: str, excluded_paths: set[str]) -> bool:
    normalized = relative_path.strip().replace("\\", "/")
    if not normalized or normalized in excluded_paths:
        return True
    if _is_executable_test_file(normalized):
        return True
    filename = Path(normalized).name
    return filename == "conftest.py"


def _evaluate_expected_targets(
    *,
    expected_targets: list[str],
    passed_targets: list[str],
    failed_targets: list[str],
) -> dict[str, Any]:
    passed_exact = set(passed_targets)
    failed_exact = set(failed_targets)
    normalized_outcomes: dict[str, set[str]] = {}
    for target in passed_targets:
        normalized_outcomes.setdefault(_normalize_nodeid(target), set()).add("passed")
    for target in failed_targets:
        normalized_outcomes.setdefault(_normalize_nodeid(target), set()).add("failed")

    status_by_target: dict[str, str] = {}
    missing_targets: list[str] = []
    for target in expected_targets:
        if target in passed_exact:
            status_by_target[target] = "passed"
            continue
        if target in failed_exact:
            status_by_target[target] = "failed"
            continue
        outcomes = normalized_outcomes.get(_normalize_nodeid(target), set())
        if "failed" in outcomes:
            status_by_target[target] = "failed"
        elif "passed" in outcomes:
            status_by_target[target] = "passed"
        else:
            status_by_target[target] = "missing"
            missing_targets.append(target)
    return {
        "status_by_target": status_by_target,
        "missing_targets": sorted(missing_targets),
    }


def _normalize_nodeid(target: str) -> str:
    nodeid = target.strip().replace("\\", "/")
    if not nodeid:
        return ""
    if "::" not in nodeid:
        return nodeid
    file_part, remainder = nodeid.split("::", 1)
    test_name = remainder.split("[", 1)[0]
    return f"{file_part}::{test_name}"


def _completion_reason(exit_code: int, oracle: dict[str, Any]) -> str:
    if exit_code != 0 and oracle["execution_error"]:
        return "agent_and_oracle_error"
    if exit_code != 0:
        return "agent_error"
    if oracle["execution_error"]:
        return "oracle_error"
    if oracle["task_success"]:
        return "oracle_pass"
    return "oracle_fail"


def _result_status(exit_code: int, oracle: dict[str, Any]) -> str:
    if exit_code == 0 and oracle["task_success"]:
        return "SUCCESS"
    if oracle["execution_error"] or exit_code != 0:
        return "ERROR"
    return "FAIL"


def _render_execution_markdown(summary: dict[str, Any]) -> str:
    lines = [
        f"# Stage 5 Execution: {summary['repo']}",
        "",
        "## Summary",
        f"- Selected runs: {summary['selection']['selected_runs']}",
        f"- Success: {summary['summary']['success']}",
        f"- Fail: {summary['summary']['failed']}",
        f"- Error: {summary['summary']['error']}",
        f"- Skipped: {summary['summary']['skipped']}",
        "",
        "## Run Results",
    ]
    for result in summary["results"]:
        detail = result.get("completion_reason") or result.get("reason") or "ok"
        lines.append(f"- `{result['run_id']}`: `{result['status']}` ({detail})")
    return "\n".join(lines) + "\n"
