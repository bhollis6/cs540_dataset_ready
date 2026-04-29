"""Tests for focused single-task packet generation."""

from __future__ import annotations

import json
from pathlib import Path

from src.workflow.task_packet import build_task_packet


def test_build_task_packet_summarizes_task_outcomes_and_failures(tmp_path: Path):
    stage7_dir = tmp_path / "stage7"
    stage7_dir.mkdir()
    runs_root = tmp_path / "runs"
    clean_root = runs_root / "clean"
    naming_root = runs_root / "naming"
    clean_root.mkdir(parents=True)
    naming_root.mkdir(parents=True)

    clean_result = {
        "candidate_id": "httpx_pr_2535",
        "oracle": {
            "reason": "oracle_pass",
            "task_success": True,
            "fail_to_pass_tests": ["a", "b", "c"],
            "fail_to_pass_passed": ["a", "b", "c"],
            "fail_to_pass_failed": [],
            "pass_to_pass_tests": ["x", "y"],
            "passed": ["x", "y", "a", "b", "c"],
            "pass_to_pass_failed": [],
            "missing_targets": [],
        },
    }
    naming_result = {
        "candidate_id": "httpx_pr_2535",
        "oracle": {
            "reason": "oracle_fail",
            "task_success": False,
            "fail_to_pass_tests": ["a", "b", "c"],
            "fail_to_pass_passed": ["a", "b", "c"],
            "fail_to_pass_failed": [],
            "pass_to_pass_tests": ["x", "y", "z"],
            "passed": ["a", "b", "c"],
            "pass_to_pass_failed": ["x", "y"],
            "missing_targets": [],
        },
    }
    (clean_root / "result.json").write_text(json.dumps(clean_result), encoding="utf-8")
    (naming_root / "result.json").write_text(json.dumps(naming_result), encoding="utf-8")

    stage7_summary = {
        "repo": "encode/httpx",
        "runs": [
            {
                "run_id": "httpx__httpx_pr_2535__codex_cli__clean__rep1",
                "candidate_id": "httpx_pr_2535",
                "condition": "clean",
                "harness": {"id": "codex_cli", "runner": "codex-cli"},
                "status": "SUCCESS",
                "completion_reason": "oracle_pass",
                "task_success": True,
                "bootstrap": {
                    "files_opened_before_first_edit": 10,
                    "dead_end_file_opens": 3,
                    "relevant_files_opened": 7,
                    "exploration_efficiency": 0.7,
                    "time_to_first_edit_seconds": None,
                },
                "execution": {
                    "edits_applied": 7,
                    "test_commands_run": 1,
                    "total_tokens": None,
                    "total_cost_usd": None,
                },
                "durations": {"total_duration_seconds": 455.3},
                "result_path": str(clean_root / "result.json"),
            },
            {
                "run_id": "httpx__httpx_pr_2535__codex_cli__naming__rep1",
                "candidate_id": "httpx_pr_2535",
                "condition": "naming",
                "harness": {"id": "codex_cli", "runner": "codex-cli"},
                "status": "FAIL",
                "completion_reason": "oracle_fail",
                "task_success": False,
                "bootstrap": {
                    "files_opened_before_first_edit": 11,
                    "dead_end_file_opens": 3,
                    "relevant_files_opened": 8,
                    "exploration_efficiency": 0.7273,
                    "time_to_first_edit_seconds": None,
                },
                "execution": {
                    "edits_applied": 7,
                    "test_commands_run": 1,
                    "total_tokens": None,
                    "total_cost_usd": None,
                },
                "durations": {"total_duration_seconds": 499.1},
                "result_path": str(naming_root / "result.json"),
            },
        ],
        "deltas_vs_clean": [
            {
                "harness_id": "codex_cli",
                "candidate_id": "httpx_pr_2535",
                "condition": "naming",
                "delta_success_rate": -1.0,
                "delta_exploration_efficiency": 0.0273,
                "delta_total_duration_seconds": 43.8,
            }
        ],
    }
    (stage7_dir / "httpx_stage7_analysis.json").write_text(json.dumps(stage7_summary), encoding="utf-8")

    output_path = build_task_packet(
        repo="encode/httpx",
        stage7_dir=stage7_dir,
        candidate_id="httpx_pr_2535",
        harness="codex-cli",
    )

    packet = json.loads(output_path.read_text())
    assert packet["overview"]["success_count"] == 1
    assert packet["overview"]["failure_count"] == 1
    assert packet["conditions"][1]["condition"] == "naming"
    assert packet["conditions"][1]["oracle"]["pass_to_pass_failed_count"] == 2
    assert all("Successful degraded conditions" not in finding for finding in packet["findings"])
    assert any("reduced success_rate by 1.0" in finding for finding in packet["findings"])

    markdown = output_path.with_suffix(".md").read_text(encoding="utf-8")
    assert "`naming`" in markdown
    assert "PASS_TO_PASS regressions=2" in markdown
