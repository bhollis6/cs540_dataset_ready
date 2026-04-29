"""Tests for Stage 7 run analysis."""

from __future__ import annotations

import json
from pathlib import Path

from src.workflow.stage7_analysis import analyze_stage7_results


def test_analyze_stage7_results_builds_clean_vs_degraded_deltas(tmp_path: Path):
    stage6_dir = tmp_path / "stage6"
    stage6_dir.mkdir()
    runs_root = tmp_path / "runs"

    clean_root = runs_root / "clean"
    degraded_root = runs_root / "type_hints"
    clean_root.mkdir(parents=True)
    degraded_root.mkdir(parents=True)

    clean_result = {
        "run_id": "httpx__httpx_pr_1__codex_cli__clean__rep1",
        "candidate_id": "httpx_pr_1",
        "pr_number": 1,
    }
    degraded_result = {
        "run_id": "httpx__httpx_pr_1__codex_cli__type_hints__rep1",
        "candidate_id": "httpx_pr_1",
        "pr_number": 1,
    }
    (clean_root / "result.json").write_text(json.dumps(clean_result), encoding="utf-8")
    (degraded_root / "result.json").write_text(json.dumps(degraded_result), encoding="utf-8")

    clean_metrics = {
        "agent_duration_seconds": 100.0,
        "oracle_duration_seconds": 10.0,
        "total_duration_seconds": 110.0,
    }
    degraded_metrics = {
        "agent_duration_seconds": 140.0,
        "oracle_duration_seconds": 15.0,
        "total_duration_seconds": 155.0,
    }
    (clean_root / "metrics.json").write_text(json.dumps(clean_metrics), encoding="utf-8")
    (degraded_root / "metrics.json").write_text(json.dumps(degraded_metrics), encoding="utf-8")

    stage6_summary = {
        "repo": "encode/httpx",
        "runs": [
            {
                "run_id": clean_result["run_id"],
                "condition": "clean",
                "harness": {"id": "codex_cli", "runner": "codex-cli"},
                "status": "SUCCESS",
                "completion_reason": "oracle_pass",
                "result_path": str(clean_root / "result.json"),
                "metrics_path": str(clean_root / "metrics.json"),
                "bootstrap": {
                    "files_opened_before_first_edit": 10,
                    "dead_end_file_opens": 3,
                    "relevant_files_opened": 7,
                    "exploration_efficiency": 0.7,
                    "time_to_first_edit_seconds": None,
                },
                "execution": {
                    "task_success": True,
                    "total_tokens": None,
                    "total_cost_usd": None,
                    "edits_applied": 7,
                    "test_commands_run": 1,
                    "completion_reason": "oracle_pass",
                },
                "warnings": [],
            },
            {
                "run_id": degraded_result["run_id"],
                "condition": "type_hints",
                "harness": {"id": "codex_cli", "runner": "codex-cli"},
                "status": "FAIL",
                "completion_reason": "oracle_fail",
                "result_path": str(degraded_root / "result.json"),
                "metrics_path": str(degraded_root / "metrics.json"),
                "bootstrap": {
                    "files_opened_before_first_edit": 14,
                    "dead_end_file_opens": 6,
                    "relevant_files_opened": 8,
                    "exploration_efficiency": 0.5714,
                    "time_to_first_edit_seconds": None,
                },
                "execution": {
                    "task_success": False,
                    "total_tokens": None,
                    "total_cost_usd": None,
                    "edits_applied": 9,
                    "test_commands_run": 2,
                    "completion_reason": "oracle_fail",
                },
                "warnings": [],
            },
        ],
    }
    (stage6_dir / "httpx_stage6_metrics.json").write_text(json.dumps(stage6_summary), encoding="utf-8")

    output_path = analyze_stage7_results(repo="encode/httpx", stage6_dir=stage6_dir)
    analysis = json.loads(output_path.read_text())

    assert analysis["overview"]["success_count"] == 1
    assert analysis["overview"]["failure_count"] == 1
    assert analysis["aggregates"]["by_harness_condition"][0]["condition"] == "clean"
    assert analysis["aggregates"]["by_harness_condition"][1]["condition"] == "type_hints"
    delta = analysis["deltas_vs_clean"][0]
    assert delta["condition"] == "type_hints"
    assert delta["delta_success_rate"] == -1.0
    assert delta["delta_files_opened_before_first_edit"] == 4.0
    assert delta["delta_total_duration_seconds"] == 45.0
    assert any("reduced success_rate" in finding for finding in analysis["findings"])


def test_analyze_stage7_results_handles_baseline_only_slice(tmp_path: Path):
    stage6_dir = tmp_path / "stage6"
    stage6_dir.mkdir()
    run_root = tmp_path / "runs" / "clean"
    run_root.mkdir(parents=True)

    result_payload = {
        "run_id": "httpx__httpx_pr_1__codex_cli__clean__rep1",
        "candidate_id": "httpx_pr_1",
        "pr_number": 1,
    }
    metrics_payload = {
        "agent_duration_seconds": 100.0,
        "oracle_duration_seconds": 10.0,
        "total_duration_seconds": 110.0,
    }
    (run_root / "result.json").write_text(json.dumps(result_payload), encoding="utf-8")
    (run_root / "metrics.json").write_text(json.dumps(metrics_payload), encoding="utf-8")

    stage6_summary = {
        "repo": "encode/httpx",
        "runs": [
            {
                "run_id": result_payload["run_id"],
                "condition": "clean",
                "harness": {"id": "codex_cli", "runner": "codex-cli"},
                "status": "SUCCESS",
                "completion_reason": "oracle_pass",
                "result_path": str(run_root / "result.json"),
                "metrics_path": str(run_root / "metrics.json"),
                "bootstrap": {
                    "files_opened_before_first_edit": 10,
                    "dead_end_file_opens": 3,
                    "relevant_files_opened": 7,
                    "exploration_efficiency": 0.7,
                    "time_to_first_edit_seconds": None,
                },
                "execution": {
                    "task_success": True,
                    "total_tokens": None,
                    "total_cost_usd": None,
                    "edits_applied": 7,
                    "test_commands_run": 1,
                    "completion_reason": "oracle_pass",
                },
                "warnings": [],
            }
        ],
    }
    (stage6_dir / "httpx_stage6_metrics.json").write_text(json.dumps(stage6_summary), encoding="utf-8")

    output_path = analyze_stage7_results(repo="encode/httpx", stage6_dir=stage6_dir)
    analysis = json.loads(output_path.read_text())

    assert analysis["deltas_vs_clean"] == []
    assert any("No clean-vs-degraded comparison" in finding for finding in analysis["findings"])
