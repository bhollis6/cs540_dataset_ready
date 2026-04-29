"""Build a focused single-task experiment packet from Stage 7 analysis artifacts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def build_task_packet(
    *,
    repo: str,
    stage7_dir: Path,
    candidate_id: str,
    harness: str | None = None,
    output_dir: Path | None = None,
) -> Path:
    """Create a focused packet for one candidate task from Stage 7 analysis outputs."""
    repo_short = repo.split("/")[-1]
    stage7_path = stage7_dir / f"{repo_short}_stage7_analysis.json"
    if not stage7_path.exists():
        raise FileNotFoundError(f"Stage 7 analysis summary not found: {stage7_path}")

    with open(stage7_path) as f:
        analysis = json.load(f)

    runs = [
        run
        for run in analysis.get("runs", [])
        if run.get("candidate_id") == candidate_id
        and (harness is None or _matches_harness(run.get("harness", {}), harness))
    ]
    if not runs:
        raise ValueError(
            f"No Stage 7 runs found for candidate_id={candidate_id!r}"
            + (f" and harness={harness!r}" if harness else "")
        )

    deltas = [
        delta
        for delta in analysis.get("deltas_vs_clean", [])
        if delta.get("candidate_id") == candidate_id
        and (harness is None or delta.get("harness_id") == _normalize_harness(harness))
    ]

    condition_summaries = [_build_condition_summary(run) for run in sorted(runs, key=_condition_sort_key)]
    overview = {
        "total_conditions": len(condition_summaries),
        "success_count": sum(1 for item in condition_summaries if item["status"] == "SUCCESS"),
        "failure_count": sum(1 for item in condition_summaries if item["status"] == "FAIL"),
        "error_count": sum(1 for item in condition_summaries if item["status"] == "ERROR"),
        "conditions": [item["condition"] for item in condition_summaries],
    }

    packet = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo": repo,
        "repo_short": repo_short,
        "candidate_id": candidate_id,
        "harness": condition_summaries[0]["harness"]["id"],
        "source_stage7_summary": str(stage7_path),
        "overview": overview,
        "conditions": condition_summaries,
        "deltas_vs_clean": sorted(deltas, key=lambda item: _condition_rank(item.get("condition"))),
        "findings": _build_findings(condition_summaries, deltas),
    }

    packet_dir = output_dir or stage7_dir
    packet_dir.mkdir(parents=True, exist_ok=True)
    suffix = condition_summaries[0]["harness"]["id"]
    json_path = packet_dir / f"{candidate_id}_{suffix}_task_packet.json"
    with open(json_path, "w") as f:
        json.dump(packet, f, indent=2)
    markdown_path = packet_dir / f"{candidate_id}_{suffix}_task_packet.md"
    markdown_path.write_text(_render_task_packet_markdown(packet), encoding="utf-8")
    return json_path


def _matches_harness(harness_payload: dict[str, Any], harness: str) -> bool:
    normalized = _normalize_harness(harness)
    return harness_payload.get("id") == normalized or harness_payload.get("runner") == harness


def _normalize_harness(harness: str) -> str:
    return harness.replace("-", "_")


def _condition_sort_key(run: dict[str, Any]) -> tuple[int, str]:
    return (_condition_rank(run.get("condition")), run.get("condition") or "")


def _condition_rank(condition: str | None) -> int:
    order = {
        "clean": 0,
        "type_hints": 1,
        "naming": 2,
        "comments_docstrings": 3,
        "remove_tests": 4,
    }
    return order.get(condition or "", 99)


def _build_condition_summary(run: dict[str, Any]) -> dict[str, Any]:
    result_path = Path(run["result_path"])
    with open(result_path) as f:
        result_payload = json.load(f)

    oracle = result_payload.get("oracle", {})
    failure_details = {
        "fail_to_pass_failed_count": len(oracle.get("fail_to_pass_failed", [])),
        "pass_to_pass_failed_count": len(oracle.get("pass_to_pass_failed", [])),
        "missing_targets_count": len(oracle.get("missing_targets", [])),
        "fail_to_pass_failed": oracle.get("fail_to_pass_failed", [])[:10],
        "pass_to_pass_failed": oracle.get("pass_to_pass_failed", [])[:10],
        "missing_targets": oracle.get("missing_targets", [])[:10],
    }

    return {
        "condition": run.get("condition"),
        "status": run.get("status"),
        "completion_reason": run.get("completion_reason"),
        "task_success": run.get("task_success"),
        "harness": run.get("harness"),
        "bootstrap": {
            "files_opened_before_first_edit": run.get("bootstrap", {}).get("files_opened_before_first_edit"),
            "dead_end_file_opens": run.get("bootstrap", {}).get("dead_end_file_opens"),
            "relevant_files_opened": run.get("bootstrap", {}).get("relevant_files_opened"),
            "exploration_efficiency": run.get("bootstrap", {}).get("exploration_efficiency"),
            "time_to_first_edit_seconds": run.get("bootstrap", {}).get("time_to_first_edit_seconds"),
        },
        "execution": {
            "edits_applied": run.get("execution", {}).get("edits_applied"),
            "test_commands_run": run.get("execution", {}).get("test_commands_run"),
            "total_tokens": run.get("execution", {}).get("total_tokens"),
            "total_cost_usd": run.get("execution", {}).get("total_cost_usd"),
        },
        "durations": run.get("durations", {}),
        "oracle": {
            "reason": oracle.get("reason"),
            "task_success": oracle.get("task_success"),
            "fail_to_pass_total": len(oracle.get("fail_to_pass_tests", [])),
            "fail_to_pass_passed_count": len(oracle.get("fail_to_pass_passed", [])),
            "pass_to_pass_total": len(oracle.get("pass_to_pass_tests", [])),
            "pass_to_pass_passed_count": len(oracle.get("passed", [])) - len(oracle.get("fail_to_pass_passed", [])),
            **failure_details,
        },
        "result_path": run.get("result_path"),
    }


def _build_findings(
    conditions: list[dict[str, Any]],
    deltas: list[dict[str, Any]],
) -> list[str]:
    findings: list[str] = []
    clean = next((item for item in conditions if item["condition"] == "clean"), None)
    if clean and clean["status"] == "SUCCESS":
        findings.append(
            "Clean baseline passed with "
            f"{clean['bootstrap'].get('files_opened_before_first_edit')} pre-edit file opens and "
            f"exploration_efficiency={clean['bootstrap'].get('exploration_efficiency')}."
        )

    successful_degraded = [
        item["condition"]
        for item in conditions
        if item["condition"] != "clean" and item["status"] == "SUCCESS"
    ]
    if successful_degraded:
        findings.append(
            "Successful degraded conditions: " + ", ".join(f"`{condition}`" for condition in successful_degraded) + "."
        )

    failed_degraded = [item for item in conditions if item["condition"] != "clean" and item["status"] != "SUCCESS"]
    for item in failed_degraded:
        regressions = item["oracle"]["pass_to_pass_failed_count"]
        target_failures = item["oracle"]["fail_to_pass_failed_count"]
        findings.append(
            f"`{item['condition']}` failed with completion_reason={item['completion_reason']}; "
            f"FAIL_TO_PASS failures={target_failures}, PASS_TO_PASS regressions={regressions}."
        )

    for delta in sorted(deltas, key=lambda item: _condition_rank(item.get("condition"))):
        if delta.get("delta_success_rate") == -1.0:
            findings.append(
                f"`{delta['condition']}` reduced success_rate by 1.0 versus clean for this task."
            )
    return findings


def _render_task_packet_markdown(packet: dict[str, Any]) -> str:
    lines = [
        f"# Task Packet: {packet['repo']} / {packet['candidate_id']}",
        "",
        "## Overview",
        f"- Harness: `{packet['harness']}`",
        f"- Conditions: {packet['overview']['total_conditions']}",
        f"- Successes: {packet['overview']['success_count']}",
        f"- Failures: {packet['overview']['failure_count']}",
        f"- Errors: {packet['overview']['error_count']}",
        "",
        "## Findings",
    ]
    if packet["findings"]:
        lines.extend(f"- {finding}" for finding in packet["findings"])
    else:
        lines.append("- No findings generated.")

    lines.extend(["", "## Condition Outcomes"])
    for condition in packet["conditions"]:
        lines.append(
            "- "
            f"`{condition['condition']}`: status={condition['status']} "
            f"reason={condition['completion_reason']} "
            f"exploration_efficiency={condition['bootstrap'].get('exploration_efficiency')} "
            f"total_duration_seconds={condition['durations'].get('total_duration_seconds')}"
        )
        if condition["status"] != "SUCCESS":
            lines.append(
                "  "
                f"FAIL_TO_PASS failures={condition['oracle']['fail_to_pass_failed_count']} "
                f"PASS_TO_PASS regressions={condition['oracle']['pass_to_pass_failed_count']}"
            )

    lines.extend(["", "## Deltas Vs Clean"])
    if packet["deltas_vs_clean"]:
        for delta in packet["deltas_vs_clean"]:
            lines.append(
                "- "
                f"`{delta['condition']}`: "
                f"delta_success_rate={delta.get('delta_success_rate')} "
                f"delta_exploration_efficiency={delta.get('delta_exploration_efficiency')} "
                f"delta_total_duration_seconds={delta.get('delta_total_duration_seconds')}"
            )
    else:
        lines.append("- No clean baseline deltas available.")

    return "\n".join(lines) + "\n"
