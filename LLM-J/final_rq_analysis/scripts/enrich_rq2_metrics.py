#!/usr/bin/env python3
"""Recover process metrics from preserved Codex JSONL logs."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MATRIX = ROOT / "final_rq_analysis/data/consolidated_matrix.csv"
DEFAULT_OUTPUT = ROOT / "final_rq_analysis/data/enriched_matrix_with_process_metrics.csv"
DEFAULT_JSON_OUTPUT = ROOT / "final_rq_analysis/data/enriched_matrix_with_process_metrics.json"

VALIDATION_RE = re.compile(
    r"(\bpytest\b|\bpy\.test\b|\bunittest\b|\btox\b|\bnox\b|scripts/test|"
    r"\bmake\s+test\b|\bjust\s+test\b|\bpoe\s+test\b|\bhatch\s+run\b.*\btest|"
    r"\buv\s+run\b.*\bpytest\b|\bcoverage\s+run\b)",
    re.IGNORECASE | re.DOTALL,
)


@dataclass(frozen=True)
class ProcessMetrics:
    agent_stdout_path: str
    agent_stdout_present: bool
    jsonl_event_count: int
    jsonl_parse_errors: int
    first_edit_event_index: int | None
    first_edit_detected_from_stdout: bool
    command_count_before_first_edit: int
    command_count_after_first_edit: int
    agent_message_count_before_first_edit: int
    agent_message_count_after_first_edit: int
    edit_event_count_before_first_edit: int
    edit_event_count_after_first_edit: int
    validation_test_command_count: int
    validation_test_command_count_before_first_edit: int
    validation_test_command_count_after_first_edit: int
    failed_validation_test_command_count: int
    failed_command_count: int
    edit_test_edit_loop_proxy_count: int
    failed_validation_followed_by_edit_count: int
    command_failure_rate: float | None
    validation_failure_rate: float | None


def _run_root_from_result_path(result_path: str) -> Path:
    return ROOT / result_path if not Path(result_path).is_absolute() else Path(result_path)


def _event_side(index: int, first_edit_index: int | None) -> str:
    if first_edit_index is None or index < first_edit_index:
        return "before"
    return "after"


def _is_edit_item(item: dict[str, Any]) -> bool:
    item_type = str(item.get("type") or "")
    return item_type in {"file_change", "patch_apply"} or "edit" in item_type


def _is_completed_command(event_type: str, item: dict[str, Any]) -> bool:
    return event_type == "item.completed" and item.get("type") == "command_execution"


def _is_completed_message(event_type: str, item: dict[str, Any]) -> bool:
    return event_type == "item.completed" and item.get("type") == "agent_message"


def _is_completed_edit(event_type: str, item: dict[str, Any]) -> bool:
    return event_type == "item.completed" and _is_edit_item(item)


def _command_failed(item: dict[str, Any]) -> bool:
    status = str(item.get("status") or "").lower()
    exit_code = item.get("exit_code")
    return status == "failed" or (exit_code is not None and exit_code != 0)


def _command_text(item: dict[str, Any]) -> str:
    command = item.get("command")
    if isinstance(command, list):
        return " ".join(str(part) for part in command)
    return str(command or "")


def _is_validation_command(item: dict[str, Any]) -> bool:
    return bool(VALIDATION_RE.search(_command_text(item)))


def parse_stdout(stdout_path: Path) -> ProcessMetrics:
    if not stdout_path.exists():
        return ProcessMetrics(
            agent_stdout_path=str(stdout_path.relative_to(ROOT)),
            agent_stdout_present=False,
            jsonl_event_count=0,
            jsonl_parse_errors=0,
            first_edit_event_index=None,
            first_edit_detected_from_stdout=False,
            command_count_before_first_edit=0,
            command_count_after_first_edit=0,
            agent_message_count_before_first_edit=0,
            agent_message_count_after_first_edit=0,
            edit_event_count_before_first_edit=0,
            edit_event_count_after_first_edit=0,
            validation_test_command_count=0,
            validation_test_command_count_before_first_edit=0,
            validation_test_command_count_after_first_edit=0,
            failed_validation_test_command_count=0,
            failed_command_count=0,
            edit_test_edit_loop_proxy_count=0,
            failed_validation_followed_by_edit_count=0,
            command_failure_rate=None,
            validation_failure_rate=None,
        )

    events: list[tuple[int, dict[str, Any]]] = []
    parse_errors = 0
    with stdout_path.open(encoding="utf-8", errors="replace") as handle:
        for index, line in enumerate(handle):
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                parse_errors += 1
                continue
            if isinstance(event, dict):
                events.append((index, event))

    first_edit_index: int | None = None
    for index, event in events:
        item = event.get("item") or {}
        if isinstance(item, dict) and _is_edit_item(item):
            first_edit_index = index
            break

    counts = {
        "command_before": 0,
        "command_after": 0,
        "message_before": 0,
        "message_after": 0,
        "edit_before": 0,
        "edit_after": 0,
        "validation_before": 0,
        "validation_after": 0,
    }
    command_total = 0
    failed_command_total = 0
    validation_total = 0
    failed_validation_total = 0
    completed_edit_indices: list[int] = []
    validation_indices: list[int] = []
    failed_validation_indices: list[int] = []

    for index, event in events:
        event_type = str(event.get("type") or "")
        item = event.get("item") or {}
        if not isinstance(item, dict):
            continue
        side = _event_side(index, first_edit_index)

        if _is_completed_command(event_type, item):
            command_total += 1
            counts[f"command_{side}"] += 1
            failed = _command_failed(item)
            if failed:
                failed_command_total += 1
            if _is_validation_command(item):
                validation_total += 1
                validation_indices.append(index)
                counts[f"validation_{side}"] += 1
                if failed:
                    failed_validation_total += 1
                    failed_validation_indices.append(index)
        elif _is_completed_message(event_type, item):
            counts[f"message_{side}"] += 1
        elif _is_completed_edit(event_type, item):
            counts[f"edit_{side}"] += 1
            completed_edit_indices.append(index)

    edit_test_edit = 0
    failed_validation_followed_by_edit = 0
    for validation_index in validation_indices:
        has_prior_edit = any(edit_index < validation_index for edit_index in completed_edit_indices)
        has_later_edit = any(edit_index > validation_index for edit_index in completed_edit_indices)
        if has_prior_edit and has_later_edit:
            edit_test_edit += 1
    for validation_index in failed_validation_indices:
        if any(edit_index > validation_index for edit_index in completed_edit_indices):
            failed_validation_followed_by_edit += 1

    rel_path = stdout_path.relative_to(ROOT) if stdout_path.is_relative_to(ROOT) else stdout_path
    return ProcessMetrics(
        agent_stdout_path=str(rel_path),
        agent_stdout_present=True,
        jsonl_event_count=len(events),
        jsonl_parse_errors=parse_errors,
        first_edit_event_index=first_edit_index,
        first_edit_detected_from_stdout=first_edit_index is not None,
        command_count_before_first_edit=counts["command_before"],
        command_count_after_first_edit=counts["command_after"],
        agent_message_count_before_first_edit=counts["message_before"],
        agent_message_count_after_first_edit=counts["message_after"],
        edit_event_count_before_first_edit=counts["edit_before"],
        edit_event_count_after_first_edit=counts["edit_after"],
        validation_test_command_count=validation_total,
        validation_test_command_count_before_first_edit=counts["validation_before"],
        validation_test_command_count_after_first_edit=counts["validation_after"],
        failed_validation_test_command_count=failed_validation_total,
        failed_command_count=failed_command_total,
        edit_test_edit_loop_proxy_count=edit_test_edit,
        failed_validation_followed_by_edit_count=failed_validation_followed_by_edit,
        command_failure_rate=(failed_command_total / command_total if command_total else None),
        validation_failure_rate=(failed_validation_total / validation_total if validation_total else None),
    )


def enrich_matrix(matrix_path: Path) -> pd.DataFrame:
    df = pd.read_csv(matrix_path)
    records: list[dict[str, Any]] = []
    for row in df.to_dict(orient="records"):
        result_path = _run_root_from_result_path(str(row["result_path"]))
        run_root = result_path.parent
        stdout_path = run_root / "logs" / "agent_stdout.log"
        records.append(parse_stdout(stdout_path).__dict__)

    enriched = pd.concat([df.reset_index(drop=True), pd.DataFrame(records)], axis=1)
    return enriched


def validate(enriched: pd.DataFrame) -> None:
    if len(enriched) != 150:
        raise SystemExit(f"Expected 150 rows, found {len(enriched)}")
    duplicate_count = enriched.duplicated(["repo", "candidate_id", "condition"]).sum()
    if duplicate_count:
        raise SystemExit(f"Duplicate repo/candidate/condition rows: {duplicate_count}")
    if int((enriched["status"] == "ERROR").sum()) != 0:
        raise SystemExit("Expected 0 harness ERROR rows")
    if int(enriched["total_tokens_including_cache"].notna().sum()) != len(enriched):
        raise SystemExit("Token usage coverage is incomplete")
    if int(enriched["agent_stdout_present"].sum()) != len(enriched):
        missing = enriched.loc[~enriched["agent_stdout_present"], "agent_stdout_path"].tolist()
        raise SystemExit(f"Missing agent_stdout.log for {len(missing)} rows: {missing[:5]}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    args = parser.parse_args()

    enriched = enrich_matrix(args.matrix)
    validate(enriched)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    enriched.to_csv(args.output, index=False)
    enriched.to_json(args.json_output, orient="records", indent=2)
    print(f"Wrote {args.output} ({len(enriched)} rows)")
    print(f"Wrote {args.json_output}")


if __name__ == "__main__":
    main()
