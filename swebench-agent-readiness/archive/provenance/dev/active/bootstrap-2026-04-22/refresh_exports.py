from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
RQ1_JSON = ROOT / "results/rq1_comparisons_2026-04-26.json"
RQ1_CSV = ROOT / "results/rq1_comparisons_2026-04-26.csv"
RQ2_JSON = ROOT / "results/rq2_phase_metrics_2026-04-26.json"
RQ2_CSV = ROOT / "results/rq2_phase_metrics_2026-04-26.csv"

TEST_RE = re.compile(
    r"(^|[\s'\"])(pytest|py\.test|tox)([\s'\"]|$)|python\s+-m\s+(pytest|unittest)"
)


def _join(values: list[str] | None) -> str:
    return "|".join(values or [])


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def _metrics(comparison: dict[str, Any], side: str) -> dict[str, Any]:
    return comparison.get("agent_metrics", {}).get(side, {})


def _corrected_total(metrics: dict[str, Any]) -> int | None:
    input_tokens = metrics.get("input_tokens")
    output_tokens = metrics.get("output_tokens")
    if input_tokens is None or output_tokens is None:
        return metrics.get("total_tokens")
    return int(input_tokens) + int(output_tokens)


def _rq1_row(path: Path, comparison: dict[str, Any]) -> dict[str, Any]:
    clean = comparison["clean"]
    degraded = comparison["degraded"]
    clean_metrics = _metrics(comparison, "clean")
    degraded_metrics = _metrics(comparison, "degraded")
    clean_changed = set(clean.get("changed_files") or [])
    degraded_changed = set(degraded.get("changed_files") or [])
    clean_total = _corrected_total(clean_metrics)
    degraded_total = _corrected_total(degraded_metrics)
    deltas = comparison.get("deltas", {})

    return {
        "comparison_file": path.name,
        "instance_id": comparison["instance_id"],
        "repo": comparison["repo"],
        "condition": comparison.get("chosen_condition") or degraded.get("condition"),
        "replication_index": comparison.get("replication_index"),
        "clean_success": clean.get("target_success"),
        "degraded_success": degraded.get("target_success"),
        "clean_fail_to_pass_failed_count": clean.get("fail_to_pass_failed_count"),
        "degraded_fail_to_pass_failed_count": degraded.get("fail_to_pass_failed_count"),
        "clean_pass_to_pass_failed_count": clean.get("pass_to_pass_failed_count"),
        "degraded_pass_to_pass_failed_count": degraded.get("pass_to_pass_failed_count"),
        "target_success_changed": deltas.get("target_success_changed"),
        "fail_to_pass_failed_count_delta": deltas.get("fail_to_pass_failed_count_delta"),
        "pass_to_pass_failed_count_delta": deltas.get("pass_to_pass_failed_count_delta"),
        "clean_files_opened_before_first_edit": clean.get("files_opened_before_first_edit"),
        "degraded_files_opened_before_first_edit": degraded.get("files_opened_before_first_edit"),
        "files_opened_before_first_edit_delta": deltas.get("files_opened_before_first_edit_delta"),
        "clean_exploration_efficiency": clean.get("exploration_efficiency"),
        "degraded_exploration_efficiency": degraded.get("exploration_efficiency"),
        "exploration_efficiency_delta": deltas.get("exploration_efficiency_delta"),
        "clean_total_tokens_corrected": clean_total,
        "degraded_total_tokens_corrected": degraded_total,
        "total_tokens_corrected_delta": None
        if clean_total is None or degraded_total is None
        else degraded_total - clean_total,
        "clean_input_tokens": clean_metrics.get("input_tokens"),
        "degraded_input_tokens": degraded_metrics.get("input_tokens"),
        "clean_cached_input_tokens": clean_metrics.get("cached_input_tokens"),
        "degraded_cached_input_tokens": degraded_metrics.get("cached_input_tokens"),
        "clean_output_tokens": clean_metrics.get("output_tokens"),
        "degraded_output_tokens": degraded_metrics.get("output_tokens"),
        "clean_changed_file_count": len(clean_changed),
        "degraded_changed_file_count": len(degraded_changed),
        "changed_file_count_delta": len(degraded_changed) - len(clean_changed),
        "changed_file_overlap_count": len(clean_changed & degraded_changed),
        "clean_only_changed_file_count": len(clean_changed - degraded_changed),
        "degraded_only_changed_file_count": len(degraded_changed - clean_changed),
        "clean_changed_files": _join(clean.get("changed_files")),
        "degraded_changed_files": _join(degraded.get("changed_files")),
        "clean_opened_files_before_first_edit": _join(
            clean_metrics.get("opened_files_before_first_edit")
        ),
        "degraded_opened_files_before_first_edit": _join(
            degraded_metrics.get("opened_files_before_first_edit")
        ),
        "clean_dead_end_file_opens": clean_metrics.get("dead_end_file_opens"),
        "degraded_dead_end_file_opens": degraded_metrics.get("dead_end_file_opens"),
        "dead_end_file_opens_delta": None
        if clean_metrics.get("dead_end_file_opens") is None
        or degraded_metrics.get("dead_end_file_opens") is None
        else degraded_metrics.get("dead_end_file_opens")
        - clean_metrics.get("dead_end_file_opens"),
    }


def _item_type(event: dict[str, Any]) -> str | None:
    return (event.get("item") or {}).get("type")


def _is_completed_command(event: dict[str, Any]) -> bool:
    return event.get("type") == "item.completed" and _item_type(event) == "command_execution"


def _command_text(event: dict[str, Any]) -> str:
    return (event.get("item") or {}).get("command") or ""


def _is_edit_event(event: dict[str, Any]) -> bool:
    return event.get("type") in {"item.started", "item.completed"} and _item_type(event) == "file_change"


def _is_agent_message(event: dict[str, Any]) -> bool:
    return event.get("type") == "item.completed" and _item_type(event) == "agent_message"


def _failed_command(event: dict[str, Any]) -> bool:
    code = (event.get("item") or {}).get("exit_code")
    return code not in (0, None)


def _phase_counts(events: list[dict[str, Any]]) -> dict[str, Any]:
    commands = [event for event in events if _is_completed_command(event)]
    test_commands = [event for event in commands if TEST_RE.search(_command_text(event))]
    failed_test_commands = [event for event in test_commands if _failed_command(event)]
    return {
        "event_count": len(events),
        "command_count": len(commands),
        "failed_command_count": sum(1 for event in commands if _failed_command(event)),
        "edit_event_count": sum(1 for event in events if _is_edit_event(event)),
        "agent_message_count": sum(1 for event in events if _is_agent_message(event)),
        "test_command_count": len(test_commands),
        "failed_test_command_count": len(failed_test_commands),
        "test_commands": _join([_command_text(event) for event in test_commands]),
        "failed_test_commands": _join([_command_text(event) for event in failed_test_commands]),
    }


def _summarize_log(path: Path) -> dict[str, Any]:
    events = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    first_edit = next((index for index, event in enumerate(events) if _is_edit_event(event)), None)
    bootstrap = events if first_edit is None else events[:first_edit]
    execution = [] if first_edit is None else events[first_edit:]
    bootstrap_counts = _phase_counts(bootstrap)
    execution_counts = _phase_counts(execution)
    commands = [event for event in events if _is_completed_command(event)]
    test_commands = [event for event in commands if TEST_RE.search(_command_text(event))]
    return {
        "event_count": len(events),
        "first_edit_event_index": first_edit,
        "first_edit_observed": first_edit is not None,
        "bootstrap_event_count": bootstrap_counts["event_count"],
        "bootstrap_command_count": bootstrap_counts["command_count"],
        "bootstrap_failed_command_count": bootstrap_counts["failed_command_count"],
        "bootstrap_edit_event_count": bootstrap_counts["edit_event_count"],
        "bootstrap_agent_message_count": bootstrap_counts["agent_message_count"],
        "bootstrap_test_command_count": bootstrap_counts["test_command_count"],
        "bootstrap_failed_test_command_count": bootstrap_counts["failed_test_command_count"],
        "bootstrap_test_commands": bootstrap_counts["test_commands"],
        "bootstrap_failed_test_commands": bootstrap_counts["failed_test_commands"],
        "execution_event_count": execution_counts["event_count"],
        "execution_command_count": execution_counts["command_count"],
        "execution_failed_command_count": execution_counts["failed_command_count"],
        "execution_edit_event_count": execution_counts["edit_event_count"],
        "execution_agent_message_count": execution_counts["agent_message_count"],
        "execution_test_command_count": execution_counts["test_command_count"],
        "execution_failed_test_command_count": execution_counts["failed_test_command_count"],
        "execution_test_commands": execution_counts["test_commands"],
        "execution_failed_test_commands": execution_counts["failed_test_commands"],
        "total_command_count": len(commands),
        "total_test_command_count": len(test_commands),
        "total_failed_test_command_count": sum(1 for event in test_commands if _failed_command(event)),
    }


def _rq2_rows(path: Path, comparison: dict[str, Any]) -> list[dict[str, Any]]:
    condition = comparison.get("chosen_condition") or comparison["degraded"].get("condition")
    rows = []
    for side in ("clean", "degraded"):
        arm = comparison[side]
        log_path = (
            ROOT
            / "runs"
            / comparison["instance_id"]
            / "codex-cli"
            / arm["condition"]
            / f"rep_{comparison.get('replication_index')}"
            / "logs"
            / "agent_stdout.jsonl"
        )
        rows.append(
            {
                "comparison_file": path.name,
                "side": side,
                "instance_id": comparison["instance_id"],
                "repo": comparison["repo"],
                "condition": arm["condition"],
                "chosen_condition": condition,
                "replication_index": comparison.get("replication_index"),
                "target_success": arm.get("target_success"),
                "fail_to_pass_failed_count": arm.get("fail_to_pass_failed_count"),
                "pass_to_pass_failed_count": arm.get("pass_to_pass_failed_count"),
                "log_path": str(log_path),
                **_summarize_log(log_path),
            }
        )
    return rows


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def refresh(comparison_path: Path) -> dict[str, Any]:
    comparison = _load_json(comparison_path)
    rq1_rows = [row for row in _load_json(RQ1_JSON) if row.get("comparison_file") != comparison_path.name]
    rq1_rows.append(_rq1_row(comparison_path, comparison))
    RQ1_JSON.write_text(json.dumps(rq1_rows, indent=2) + "\n")
    _write_csv(RQ1_CSV, rq1_rows)

    rq2_rows = [row for row in _load_json(RQ2_JSON) if row.get("comparison_file") != comparison_path.name]
    rq2_rows.extend(_rq2_rows(comparison_path, comparison))
    RQ2_JSON.write_text(json.dumps(rq2_rows, indent=2) + "\n")
    _write_csv(RQ2_CSV, rq2_rows)

    token_deltas = [
        row["total_tokens_corrected_delta"]
        for row in rq1_rows
        if row.get("total_tokens_corrected_delta") is not None
    ]
    return {
        "rq1_rows": len(rq1_rows),
        "rq2_rows": len(rq2_rows),
        "tasks": len({row["instance_id"] for row in rq1_rows}),
        "repos": len({row["repo"] for row in rq1_rows}),
        "transitions": sum(1 for row in rq1_rows if row["clean_success"] and not row["degraded_success"]),
        "ptp_damage": sum(1 for row in rq1_rows if (row.get("pass_to_pass_failed_count_delta") or 0) > 0),
        "degraded_tokens_higher": sum(delta > 0 for delta in token_deltas),
        "degraded_tokens_lower": sum(delta < 0 for delta in token_deltas),
        "mean_token_delta": round(statistics.mean(token_deltas)),
        "median_token_delta": round(statistics.median(token_deltas)),
        "latest": rq1_rows[-1],
        "latest_rq2": rq2_rows[-2:],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("comparison_json", type=Path)
    args = parser.parse_args()
    summary = refresh(args.comparison_json.resolve())
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
