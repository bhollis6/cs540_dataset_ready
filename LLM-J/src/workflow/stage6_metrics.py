"""Parse Stage 5 run artifacts into richer Stage 6 metrics."""

from __future__ import annotations

import json
import re
import shlex
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EDIT_COMMAND_HINTS = (
    "apply_patch",
    "sed -i",
    "perl -0pi",
    "python - <<",
    "python3 - <<",
    "cat <<",
    "tee ",
    ">>",
    " > ",
)


def parse_stage6_metrics(
    *,
    repo: str,
    execution_dir: Path,
    run_ids: list[str] | None = None,
    conditions: list[str] | None = None,
    harnesses: list[str] | None = None,
    limit: int | None = None,
    write_back: bool = True,
) -> Path:
    """Enrich Stage 5 run artifacts with Stage 6 bootstrap/execution metrics."""
    repo_short = repo.split("/")[-1]
    summary_path = execution_dir / f"{repo_short}_stage5_execution.json"
    if not summary_path.exists():
        raise FileNotFoundError(f"Stage 5 execution summary not found: {summary_path}")

    with open(summary_path) as f:
        summary = json.load(f)

    selected_results = _select_results(
        summary.get("results", []),
        run_ids=run_ids,
        conditions=conditions,
        harnesses=harnesses,
        limit=limit,
    )

    parsed_runs: list[dict[str, Any]] = []
    for item in selected_results:
        parsed_runs.append(_parse_one_run(item, write_back=write_back))

    stage6_summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo": repo,
        "repo_short": repo_short,
        "source_execution_summary": str(summary_path),
        "selection": {
            "requested_run_ids": run_ids or [],
            "requested_conditions": sorted(conditions or []),
            "requested_harnesses": sorted(harnesses or []),
            "limit": limit,
            "selected_runs": len(selected_results),
        },
        "runs": parsed_runs,
        "coverage": {
            "time_to_first_edit_present": sum(
                1 for run in parsed_runs if run.get("bootstrap", {}).get("time_to_first_edit_seconds") is not None
            ),
            "files_opened_present": sum(
                1 for run in parsed_runs if run.get("bootstrap", {}).get("files_opened_before_first_edit") is not None
            ),
            "total_tokens_present": sum(
                1 for run in parsed_runs if run.get("execution", {}).get("total_tokens") is not None
            ),
            "total_cost_present": sum(
                1 for run in parsed_runs if run.get("execution", {}).get("total_cost_usd") is not None
            ),
        },
    }

    output_path = execution_dir / f"{repo_short}_stage6_metrics.json"
    with open(output_path, "w") as f:
        json.dump(stage6_summary, f, indent=2)
    markdown_path = execution_dir / f"{repo_short}_stage6_metrics.md"
    markdown_path.write_text(_render_stage6_markdown(stage6_summary), encoding="utf-8")
    return output_path


def _select_results(
    results: list[dict[str, Any]],
    *,
    run_ids: list[str] | None,
    conditions: list[str] | None,
    harnesses: list[str] | None,
    limit: int | None,
) -> list[dict[str, Any]]:
    selected = results
    if run_ids:
        allowed = set(run_ids)
        selected = [item for item in selected if item.get("run_id") in allowed]
    if conditions:
        allowed_conditions = set(conditions)
        filtered: list[dict[str, Any]] = []
        for item in selected:
            payload = _load_result_payload(item)
            if payload.get("condition") in allowed_conditions:
                filtered.append(item)
        selected = filtered
    if harnesses:
        allowed_harnesses = set(harnesses)
        filtered = []
        for item in selected:
            payload = _load_result_payload(item)
            harness = payload.get("harness", {})
            if harness.get("runner") in allowed_harnesses or harness.get("id") in allowed_harnesses:
                filtered.append(item)
        selected = filtered
    if limit is not None:
        selected = selected[:limit]
    return selected


def _parse_one_run(result_item: dict[str, Any], *, write_back: bool) -> dict[str, Any]:
    result_path = Path(result_item["result_path"])
    metrics_path = Path(result_item["metrics_path"])
    with open(result_path) as f:
        result_payload = json.load(f)
    with open(metrics_path) as f:
        metrics_payload = json.load(f)

    run_root = result_path.parent
    harness_runner = result_payload.get("harness", {}).get("runner")
    if harness_runner == "codex-cli":
        parsed = _parse_codex_run(run_root, result_payload)
    elif harness_runner == "claude-code":
        parsed = _parse_claude_run(run_root, result_payload)
    else:
        parsed = _empty_stage6_parse("Unsupported harness runner for Stage 6 parsing.")

    metrics_payload["bootstrap"] = {
        **metrics_payload.get("bootstrap", {}),
        **parsed["bootstrap"],
    }
    metrics_payload["execution"] = {
        **metrics_payload.get("execution", {}),
        **parsed["execution"],
    }
    metrics_payload["total_tokens"] = parsed["execution"]["total_tokens"]
    metrics_payload["total_cost_usd"] = parsed["execution"]["total_cost_usd"]
    metrics_payload["stage6"] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "parser": parsed["parser"],
        "warnings": parsed["warnings"],
        "details": parsed["details"],
    }

    if write_back:
        with open(metrics_path, "w") as f:
            json.dump(metrics_payload, f, indent=2)

    return {
        "run_id": result_payload["run_id"],
        "condition": result_payload.get("condition"),
        "harness": result_payload.get("harness"),
        "status": result_payload.get("status"),
        "completion_reason": result_payload.get("completion_reason"),
        "result_path": str(result_path),
        "metrics_path": str(metrics_path),
        "bootstrap": parsed["bootstrap"],
        "execution": parsed["execution"],
        "warnings": parsed["warnings"],
        "details": parsed["details"],
    }


def _parse_codex_run(run_root: Path, result_payload: dict[str, Any]) -> dict[str, Any]:
    stdout_path = run_root / "logs" / "agent_stdout.log"
    if not stdout_path.exists():
        return _empty_stage6_parse("Missing Codex stdout log.")

    relevant_file_set = _build_relevant_file_set(run_root, result_payload)
    metrics_path = run_root / "metrics.json"
    edits_applied = 0
    if metrics_path.exists():
        with open(metrics_path) as f:
            metrics_payload = json.load(f)
        relevant_file_set.update(path.replace("\\", "/") for path in metrics_payload.get("changed_files", []))
        edits_applied = int(metrics_payload.get("edits_applied", 0))

    events = _load_codex_events(stdout_path)
    first_edit_index = _first_codex_edit_index(events)
    pre_edit_events = events if first_edit_index is None else events[:first_edit_index]
    opened_files = _codex_opened_files(pre_edit_events, workspace_path=Path(result_payload["workspace"]))
    relevant_files = sorted(path for path in opened_files if path in relevant_file_set)
    dead_end_files = sorted(path for path in opened_files if path not in relevant_file_set)
    total_tokens, total_cost = _extract_token_cost(stdout_path)

    bootstrap = {
        "tokens_before_first_edit": None,
        "files_opened_before_first_edit": len(opened_files),
        "dead_end_file_opens": len(dead_end_files),
        "relevant_files_opened": len(relevant_files),
        "exploration_efficiency": (
            round(len(relevant_files) / len(opened_files), 4) if opened_files else None
        ),
        "time_to_first_edit_seconds": None,
        "opened_files_before_first_edit": opened_files,
        "relevant_opened_files": relevant_files,
        "dead_end_opened_files": dead_end_files,
        "first_edit_detected": first_edit_index is not None,
    }
    execution = {
        "task_success": result_payload.get("oracle", {}).get("task_success"),
        "total_tokens": total_tokens,
        "total_cost_usd": total_cost,
        "edits_applied": edits_applied,
        "test_commands_run": len(result_payload.get("oracle", {}).get("command", "").splitlines()) if result_payload.get("oracle", {}).get("command") else 0,
        "completion_reason": result_payload.get("completion_reason"),
    }
    warnings: list[str] = []
    if first_edit_index is None:
        warnings.append("Could not identify a Codex edit event in the JSONL stream.")
    if total_tokens is None:
        warnings.append("No Codex token usage was found in the current logs.")
    return {
        "parser": "codex_jsonl_v1",
        "bootstrap": bootstrap,
        "execution": execution,
        "warnings": warnings,
        "details": {},
    }


def _parse_claude_run(run_root: Path, result_payload: dict[str, Any]) -> dict[str, Any]:
    debug_path = run_root / "logs" / "claude_debug.log"
    if not debug_path.exists():
        return _empty_stage6_parse("Missing Claude debug log.")

    lines = debug_path.read_text(encoding="utf-8", errors="replace").splitlines()
    start_time = _parse_claude_timestamp(lines[0]) if lines else None
    first_edit_line = next((line for line in lines if "PreToolUse:Edit" in line), None)
    first_edit_time = _parse_claude_timestamp(first_edit_line) if first_edit_line else None
    changed_files = _extract_claude_edited_files(lines, workspace_path=Path(result_payload["workspace"]))
    first_write_index = next((index for index, line in enumerate(lines) if "Writing to temp file:" in line), None)
    first_write_time = _parse_claude_timestamp(lines[first_write_index]) if first_write_index is not None else None
    total_tokens, total_cost = _extract_claude_usage(result_payload, debug_path)
    shell_spawns = [line for line in lines if "Spawning shell without login" in line]
    read_tool_errors = [line for line in lines if "Read tool input error:" in line]
    edit_validation_errors = [line for line in lines if "Edit tool validation error:" in line]
    mcp_errors = [line for line in lines if "[ERROR] MCP server " in line]
    write_events = [line for line in lines if "Writing to temp file:" in line and "/workspace/" in line]

    pre_write_lines = lines if first_write_index is None else lines[:first_write_index]
    shell_spawns_before_first_write = [
        line for line in pre_write_lines if "Spawning shell without login" in line
    ]

    bootstrap = {
        "tokens_before_first_edit": None,
        "files_opened_before_first_edit": None,
        "dead_end_file_opens": None,
        "relevant_files_opened": None,
        "exploration_efficiency": None,
        "time_to_first_edit_seconds": (
            round((first_edit_time - start_time).total_seconds(), 3)
            if start_time is not None and first_edit_time is not None
            else None
        ),
        "opened_files_before_first_edit": None,
        "relevant_opened_files": None,
        "dead_end_opened_files": None,
        "first_edit_detected": first_edit_time is not None,
    }
    execution = {
        "task_success": result_payload.get("oracle", {}).get("task_success"),
        "total_tokens": total_tokens,
        "total_cost_usd": total_cost,
        "edits_applied": len(changed_files),
        "test_commands_run": len(result_payload.get("oracle", {}).get("command", "").splitlines()) if result_payload.get("oracle", {}).get("command") else 0,
        "completion_reason": result_payload.get("completion_reason"),
    }
    warnings: list[str] = []
    if first_edit_time is None:
        warnings.append("Could not identify a Claude edit event in the debug log.")
    if total_tokens is None:
        warnings.append("No Claude token usage was found in the current logs.")
    if not changed_files:
        warnings.append("Claude debug parsing did not recover concrete edited file paths.")
    return {
        "parser": "claude_debug_v2",
        "bootstrap": bootstrap,
        "execution": execution,
        "warnings": warnings,
        "details": {
            "claude_debug": {
                "shell_spawn_count": len(shell_spawns),
                "shell_spawn_count_before_first_write": len(shell_spawns_before_first_write),
                "write_event_count": len(write_events),
                "first_write_detected": first_write_index is not None,
                "time_to_first_write_seconds": (
                    round((first_write_time - start_time).total_seconds(), 3)
                    if start_time is not None and first_write_time is not None
                    else None
                ),
                "tool_error_count": len(read_tool_errors) + len(edit_validation_errors),
                "read_tool_error_count": len(read_tool_errors),
                "edit_validation_error_count": len(edit_validation_errors),
                "mcp_error_count": len(mcp_errors),
                "edited_files_recovered": changed_files,
            }
        },
    }


def _build_relevant_file_set(run_root: Path, result_payload: dict[str, Any]) -> set[str]:
    relevant: set[str] = set()
    metrics_path = run_root / "metrics.json"
    if metrics_path.exists():
        with open(metrics_path) as f:
            metrics_payload = json.load(f)
        relevant.update(path.replace("\\", "/") for path in metrics_payload.get("changed_files", []))

    metadata_path = run_root / "metadata.json"
    if metadata_path.exists():
        with open(metadata_path) as f:
            metadata = json.load(f)
        for key in ("fail_to_pass_tests", "pass_to_pass_tests"):
            for target in metadata.get("oracle", {}).get(key, []):
                relevant.add(target.split("::", 1)[0].replace("\\", "/"))
        source_candidate_path = metadata.get("task_prompt", {}).get("source_candidate_path")
        if source_candidate_path:
            candidate_path = Path(source_candidate_path)
            if not candidate_path.is_absolute():
                candidate_path = Path.cwd() / candidate_path
            if candidate_path.exists():
                with open(candidate_path) as f:
                    candidate = json.load(f)
                for key in ("source_files", "test_files", "test_support_files"):
                    for path in candidate.get(key) or []:
                        relevant.add(str(path).replace("\\", "/"))
    return relevant


def _empty_stage6_parse(reason: str) -> dict[str, Any]:
    return {
        "parser": "none",
        "bootstrap": {
            "tokens_before_first_edit": None,
            "files_opened_before_first_edit": None,
            "dead_end_file_opens": None,
            "relevant_files_opened": None,
            "exploration_efficiency": None,
            "time_to_first_edit_seconds": None,
            "opened_files_before_first_edit": None,
            "relevant_opened_files": None,
            "dead_end_opened_files": None,
            "first_edit_detected": False,
        },
        "execution": {
            "task_success": None,
            "total_tokens": None,
            "total_cost_usd": None,
            "edits_applied": 0,
            "test_commands_run": 0,
            "completion_reason": None,
        },
        "warnings": [reason],
        "details": {},
    }


def _load_result_payload(item: dict[str, Any]) -> dict[str, Any]:
    with open(item["result_path"]) as f:
        return json.load(f)


def _load_codex_events(stdout_path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in stdout_path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def _first_codex_edit_index(events: list[dict[str, Any]]) -> int | None:
    for index, event in enumerate(events):
        item = event.get("item", {})
        item_type = item.get("type")
        if item_type == "patch":
            return index
        if item_type == "command_execution" and _looks_like_edit_command(item.get("command", "")):
            return index
    return None


def _looks_like_edit_command(command: str) -> bool:
    normalized = command.lower()
    return any(hint in normalized for hint in EDIT_COMMAND_HINTS)


def _codex_opened_files(events: list[dict[str, Any]], *, workspace_path: Path) -> list[str]:
    opened: list[str] = []
    seen: set[str] = set()
    for event in events:
        item = event.get("item", {})
        if item.get("type") != "command_execution" or event.get("type") != "item.completed":
            continue
        for relative_path in _extract_paths_from_command(item.get("command", ""), workspace_path=workspace_path):
            if relative_path in seen:
                continue
            seen.add(relative_path)
            opened.append(relative_path)
    return opened


def _extract_paths_from_command(command: str, *, workspace_path: Path) -> list[str]:
    inner = _extract_shell_command(command)
    if not inner:
        return []
    try:
        tokens = shlex.split(inner)
    except ValueError:
        return []
    candidates: list[str] = []
    for token in tokens:
        if token.startswith("-") or token in {"bash", "python", "python3", "rg", "sed", "cat", "head", "tail", "git"}:
            continue
        normalized = token.strip().strip("\"'").replace("\\", "/")
        if "::" in normalized:
            normalized = normalized.split("::", 1)[0]
        if normalized.startswith("/") or normalized.startswith(".") or "/" in normalized:
            path = workspace_path / normalized
            if path.exists() and path.is_file():
                candidates.append(normalized)
    return candidates


def _extract_shell_command(command: str) -> str:
    match = re.search(r"bash -lc (?P<quote>['\"])(?P<body>.*)(?P=quote)$", command)
    if match:
        return match.group("body")
    return command


def _parse_claude_timestamp(line: str | None) -> datetime | None:
    if not line:
        return None
    match = re.match(r"(?P<ts>\d{4}-\d{2}-\d{2}T[^ ]+)", line)
    if not match:
        return None
    try:
        return datetime.fromisoformat(match.group("ts").replace("Z", "+00:00"))
    except ValueError:
        return None


def _extract_claude_edited_files(lines: list[str], *, workspace_path: Path) -> list[str]:
    edited: list[str] = []
    seen: set[str] = set()
    pattern = re.compile(r"Writing to temp file: .*?/workspace/(?P<path>.+?)\.tmp\.")
    for line in lines:
        match = pattern.search(line)
        if not match:
            continue
        relative_path = match.group("path").replace("\\", "/")
        full_path = workspace_path / relative_path
        if not full_path.exists() or relative_path in seen:
            continue
        seen.add(relative_path)
        edited.append(relative_path)
    return edited


def _extract_token_cost(log_path: Path) -> tuple[int | None, float | None]:
    text = log_path.read_text(encoding="utf-8", errors="replace")
    for line in reversed(text.splitlines()):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        usage = event.get("usage") if isinstance(event, dict) else None
        if not isinstance(usage, dict):
            continue
        input_tokens = usage.get("input_tokens")
        output_tokens = usage.get("output_tokens")
        if input_tokens is not None or output_tokens is not None:
            # Codex reports cached input separately but includes it in input_tokens.
            return int(input_tokens or 0) + int(output_tokens or 0), None

    token_match = re.search(r"\"total_tokens\"\s*:\s*(\d+)", text)
    cost_match = re.search(r"\"total_cost_usd\"\s*:\s*([0-9]+(?:\.[0-9]+)?)", text)
    total_tokens = int(token_match.group(1)) if token_match else None
    total_cost = float(cost_match.group(1)) if cost_match else None
    return total_tokens, total_cost


def _extract_claude_usage(result_payload: dict[str, Any], log_path: Path) -> tuple[int | None, float | None]:
    parsed_response = result_payload.get("agent", {}).get("parsed_response") or {}
    usage = parsed_response.get("usage") or {}

    token_fields = (
        "input_tokens",
        "cache_creation_input_tokens",
        "cache_read_input_tokens",
        "output_tokens",
    )
    token_values = [usage.get(field) for field in token_fields]
    total_tokens = None
    if any(value is not None for value in token_values):
        total_tokens = sum(int(value or 0) for value in token_values)

    total_cost = parsed_response.get("total_cost_usd")
    if total_cost is not None:
        return total_tokens, float(total_cost)

    return _extract_token_cost(log_path)


def _render_stage6_markdown(summary: dict[str, Any]) -> str:
    lines = [
        f"# Stage 6 Metrics: {summary['repo']}",
        "",
        "## Coverage",
        f"- Selected runs: {summary['selection']['selected_runs']}",
        f"- Runs with time-to-first-edit: {summary['coverage']['time_to_first_edit_present']}",
        f"- Runs with file-exploration counts: {summary['coverage']['files_opened_present']}",
        f"- Runs with token totals: {summary['coverage']['total_tokens_present']}",
        f"- Runs with cost totals: {summary['coverage']['total_cost_present']}",
        "",
        "## Parsed Runs",
    ]
    for run in summary["runs"]:
        bootstrap = run["bootstrap"]
        execution = run["execution"]
        lines.append(
            "- "
            f"`{run['run_id']}`: parser=`{run['harness']['runner']}` "
            f"time_to_first_edit={bootstrap.get('time_to_first_edit_seconds')} "
            f"files_opened={bootstrap.get('files_opened_before_first_edit')} "
            f"total_tokens={execution.get('total_tokens')}"
        )
    return "\n".join(lines) + "\n"
