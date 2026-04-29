"""Aggregate Stage 6 run metrics into Stage 7 experiment analysis artifacts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


NUMERIC_FIELDS = (
    "files_opened_before_first_edit",
    "dead_end_file_opens",
    "relevant_files_opened",
    "exploration_efficiency",
    "time_to_first_edit_seconds",
    "edits_applied",
    "test_commands_run",
    "total_tokens",
    "total_cost_usd",
    "agent_duration_seconds",
    "oracle_duration_seconds",
    "total_duration_seconds",
)


def analyze_stage7_results(
    *,
    repo: str,
    stage6_dir: Path,
    run_ids: list[str] | None = None,
    conditions: list[str] | None = None,
    harnesses: list[str] | None = None,
    limit: int | None = None,
) -> Path:
    """Aggregate parsed Stage 6 metrics into a Stage 7 analysis report."""
    repo_short = repo.split("/")[-1]
    stage6_path = stage6_dir / f"{repo_short}_stage6_metrics.json"
    if not stage6_path.exists():
        raise FileNotFoundError(f"Stage 6 metrics summary not found: {stage6_path}")

    with open(stage6_path) as f:
        summary = json.load(f)

    selected_runs = _select_runs(
        summary.get("runs", []),
        run_ids=run_ids,
        conditions=conditions,
        harnesses=harnesses,
        limit=limit,
    )
    enriched_runs = [_enrich_run(run) for run in selected_runs]

    by_condition = _aggregate_groups(
        enriched_runs,
        key_fn=lambda run: (run["harness"]["id"], run["condition"]),
        key_names=("harness_id", "condition"),
    )
    by_candidate = _aggregate_groups(
        enriched_runs,
        key_fn=lambda run: (run["harness"]["id"], run["candidate_id"], run["condition"]),
        key_names=("harness_id", "candidate_id", "condition"),
    )
    deltas = _compute_clean_deltas(enriched_runs)

    stage7_summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo": repo,
        "repo_short": repo_short,
        "source_stage6_summary": str(stage6_path),
        "selection": {
            "requested_run_ids": run_ids or [],
            "requested_conditions": sorted(conditions or []),
            "requested_harnesses": sorted(harnesses or []),
            "limit": limit,
            "selected_runs": len(enriched_runs),
        },
        "overview": {
            "success_count": sum(1 for run in enriched_runs if run["task_success"] is True),
            "failure_count": sum(1 for run in enriched_runs if run["task_success"] is False),
            "error_count": sum(1 for run in enriched_runs if run["status"] == "ERROR"),
            "unique_candidates": sorted({run["candidate_id"] for run in enriched_runs if run["candidate_id"]}),
            "unique_harnesses": sorted({run["harness"]["id"] for run in enriched_runs if run.get("harness")}),
            "conditions": sorted({run["condition"] for run in enriched_runs if run.get("condition")}),
        },
        "runs": enriched_runs,
        "aggregates": {
            "by_harness_condition": by_condition,
            "by_harness_candidate_condition": by_candidate,
        },
        "deltas_vs_clean": deltas,
        "findings": _generate_findings(enriched_runs, by_condition, deltas),
    }

    output_path = stage6_dir / f"{repo_short}_stage7_analysis.json"
    with open(output_path, "w") as f:
        json.dump(stage7_summary, f, indent=2)
    markdown_path = stage6_dir / f"{repo_short}_stage7_analysis.md"
    markdown_path.write_text(_render_stage7_markdown(stage7_summary), encoding="utf-8")
    return output_path


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
        allowed = set(run_ids)
        selected = [run for run in selected if run.get("run_id") in allowed]
    if conditions:
        allowed_conditions = set(conditions)
        selected = [run for run in selected if run.get("condition") in allowed_conditions]
    if harnesses:
        allowed_harnesses = set(harnesses)
        selected = [
            run
            for run in selected
            if run.get("harness", {}).get("runner") in allowed_harnesses
            or run.get("harness", {}).get("id") in allowed_harnesses
        ]
    if limit is not None:
        selected = selected[:limit]
    return selected


def _enrich_run(run: dict[str, Any]) -> dict[str, Any]:
    result_path = Path(run["result_path"])
    metrics_path = Path(run["metrics_path"])
    with open(result_path) as f:
        result_payload = json.load(f)
    with open(metrics_path) as f:
        metrics_payload = json.load(f)

    return {
        "run_id": run["run_id"],
        "candidate_id": result_payload.get("candidate_id"),
        "pr_number": result_payload.get("pr_number"),
        "condition": run.get("condition"),
        "harness": run.get("harness"),
        "status": run.get("status"),
        "completion_reason": run.get("completion_reason"),
        "task_success": run.get("execution", {}).get("task_success"),
        "bootstrap": run.get("bootstrap", {}),
        "execution": run.get("execution", {}),
        "durations": {
            "agent_duration_seconds": metrics_payload.get("agent_duration_seconds"),
            "oracle_duration_seconds": metrics_payload.get("oracle_duration_seconds"),
            "total_duration_seconds": metrics_payload.get("total_duration_seconds"),
        },
        "result_path": run["result_path"],
        "metrics_path": run["metrics_path"],
        "warnings": run.get("warnings", []),
    }


def _aggregate_groups(
    runs: list[dict[str, Any]],
    *,
    key_fn,
    key_names: tuple[str, ...],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for run in runs:
        grouped.setdefault(tuple(key_fn(run)), []).append(run)

    aggregates: list[dict[str, Any]] = []
    for key, items in sorted(grouped.items()):
        entry = {name: value for name, value in zip(key_names, key)}
        entry.update(_aggregate_run_list(items))
        aggregates.append(entry)
    return aggregates


def _aggregate_run_list(runs: list[dict[str, Any]]) -> dict[str, Any]:
    numeric_values: dict[str, list[float]] = {field: [] for field in NUMERIC_FIELDS}
    completion_reasons: dict[str, int] = {}
    for run in runs:
        completion_reason = run.get("completion_reason") or "unknown"
        completion_reasons[completion_reason] = completion_reasons.get(completion_reason, 0) + 1

        bootstrap = run.get("bootstrap", {})
        execution = run.get("execution", {})
        durations = run.get("durations", {})
        field_sources = {
            "files_opened_before_first_edit": bootstrap.get("files_opened_before_first_edit"),
            "dead_end_file_opens": bootstrap.get("dead_end_file_opens"),
            "relevant_files_opened": bootstrap.get("relevant_files_opened"),
            "exploration_efficiency": bootstrap.get("exploration_efficiency"),
            "time_to_first_edit_seconds": bootstrap.get("time_to_first_edit_seconds"),
            "edits_applied": execution.get("edits_applied"),
            "test_commands_run": execution.get("test_commands_run"),
            "total_tokens": execution.get("total_tokens"),
            "total_cost_usd": execution.get("total_cost_usd"),
            "agent_duration_seconds": durations.get("agent_duration_seconds"),
            "oracle_duration_seconds": durations.get("oracle_duration_seconds"),
            "total_duration_seconds": durations.get("total_duration_seconds"),
        }
        for field, value in field_sources.items():
            if value is not None:
                numeric_values[field].append(float(value))

    averages = {
        field: round(sum(values) / len(values), 4) if values else None
        for field, values in numeric_values.items()
    }
    success_count = sum(1 for run in runs if run.get("task_success") is True)
    failure_count = sum(1 for run in runs if run.get("task_success") is False)
    return {
        "run_count": len(runs),
        "success_count": success_count,
        "failure_count": failure_count,
        "success_rate": round(success_count / len(runs), 4) if runs else None,
        "completion_reasons": completion_reasons,
        "averages": averages,
    }


def _compute_clean_deltas(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str | None, str | None], list[dict[str, Any]]] = {}
    for run in runs:
        grouped.setdefault((run.get("harness", {}).get("id"), run.get("candidate_id")), []).append(run)

    deltas: list[dict[str, Any]] = []
    for (harness_id, candidate_id), items in sorted(grouped.items()):
        by_condition = _aggregate_groups(
            items,
            key_fn=lambda run: (run["condition"],),
            key_names=("condition",),
        )
        clean = next((entry for entry in by_condition if entry["condition"] == "clean"), None)
        if clean is None:
            continue
        for entry in by_condition:
            condition = entry["condition"]
            if condition == "clean":
                continue
            deltas.append(
                {
                    "harness_id": harness_id,
                    "candidate_id": candidate_id,
                    "condition": condition,
                    "run_count": entry["run_count"],
                    "delta_success_rate": _delta(entry["success_rate"], clean["success_rate"]),
                    "delta_exploration_efficiency": _delta(
                        entry["averages"]["exploration_efficiency"],
                        clean["averages"]["exploration_efficiency"],
                    ),
                    "delta_files_opened_before_first_edit": _delta(
                        entry["averages"]["files_opened_before_first_edit"],
                        clean["averages"]["files_opened_before_first_edit"],
                    ),
                    "delta_edits_applied": _delta(
                        entry["averages"]["edits_applied"],
                        clean["averages"]["edits_applied"],
                    ),
                    "delta_total_duration_seconds": _delta(
                        entry["averages"]["total_duration_seconds"],
                        clean["averages"]["total_duration_seconds"],
                    ),
                    "clean_success_rate": clean["success_rate"],
                    "condition_success_rate": entry["success_rate"],
                }
            )
    return deltas


def _delta(value: float | None, baseline: float | None) -> float | None:
    if value is None or baseline is None:
        return None
    return round(value - baseline, 4)


def _generate_findings(
    runs: list[dict[str, Any]],
    by_condition: list[dict[str, Any]],
    deltas: list[dict[str, Any]],
) -> list[str]:
    findings: list[str] = []
    successful_runs = [run for run in runs if run.get("task_success") is True]
    if successful_runs:
        best = successful_runs[0]
        files_opened = best.get("bootstrap", {}).get("files_opened_before_first_edit")
        exploration = best.get("bootstrap", {}).get("exploration_efficiency")
        findings.append(
            f"{best['harness']['id']} reached a passing oracle run on {best['candidate_id']} "
            f"under `{best['condition']}` with files_opened_before_first_edit={files_opened} "
            f"and exploration_efficiency={exploration}."
        )
    else:
        findings.append("No selected runs achieved an oracle pass in the current analysis slice.")

    for delta in deltas:
        success_delta = delta.get("delta_success_rate")
        if success_delta is None:
            continue
        if success_delta < 0:
            findings.append(
                f"For {delta['harness_id']} on {delta['candidate_id']}, `{delta['condition']}` "
                f"reduced success_rate by {abs(success_delta):.4f} versus clean."
            )
        elif success_delta > 0:
            findings.append(
                f"For {delta['harness_id']} on {delta['candidate_id']}, `{delta['condition']}` "
                f"improved success_rate by {success_delta:.4f} versus clean."
            )

    if not deltas:
        findings.append("No clean-vs-degraded comparison was available in the selected runs yet.")

    return findings


def _render_stage7_markdown(summary: dict[str, Any]) -> str:
    lines = [
        f"# Stage 7 Analysis: {summary['repo']}",
        "",
        "## Overview",
        f"- Selected runs: {summary['selection']['selected_runs']}",
        f"- Successes: {summary['overview']['success_count']}",
        f"- Failures: {summary['overview']['failure_count']}",
        f"- Errors: {summary['overview']['error_count']}",
        "",
        "## Findings",
    ]
    lines.extend(f"- {finding}" for finding in summary["findings"])
    lines.extend([
        "",
        "## Aggregates By Harness / Condition",
    ])
    for entry in summary["aggregates"]["by_harness_condition"]:
        lines.append(
            "- "
            f"`{entry['harness_id']}` / `{entry['condition']}`: "
            f"runs={entry['run_count']} success_rate={entry['success_rate']} "
            f"avg_exploration_efficiency={entry['averages']['exploration_efficiency']} "
            f"avg_total_duration_seconds={entry['averages']['total_duration_seconds']}"
        )
    if summary["deltas_vs_clean"]:
        lines.extend([
            "",
            "## Deltas Vs Clean",
        ])
        for entry in summary["deltas_vs_clean"]:
            lines.append(
                "- "
                f"`{entry['harness_id']}` / `{entry['candidate_id']}` / `{entry['condition']}`: "
                f"delta_success_rate={entry['delta_success_rate']} "
                f"delta_exploration_efficiency={entry['delta_exploration_efficiency']} "
                f"delta_total_duration_seconds={entry['delta_total_duration_seconds']}"
            )
    return "\n".join(lines) + "\n"
