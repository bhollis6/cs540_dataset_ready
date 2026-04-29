"""Tests for Stage 5 run-plan assembly."""

from __future__ import annotations

import json
from pathlib import Path

from src.workflow.run_plan import build_repo_run_plan


def test_build_repo_run_plan_emits_runs_for_both_harnesses(tmp_path: Path):
    deep_results_dir = tmp_path / "deep_results"
    packets_dir = tmp_path / "packets"
    candidates_dir = tmp_path / "candidates"
    output_dir = tmp_path / "run_plans"

    deep_results_dir.mkdir()
    packets_dir.mkdir()
    candidates_dir.mkdir()

    (deep_results_dir / "httpx_verified_manifest.json").write_text(json.dumps({
        "repo": "encode/httpx",
        "verified_prs": [
            {
                "candidate_id": "httpx_pr_1",
                "pr_number": 1,
                "base_commit_sha": "base123",
                "env_commit_sha": "env123",
                "merge_commit_sha": "merge123",
                "head_commit_sha": "head123",
                "stage1_score": 20,
                "stage2_score": 27,
                "navigation_depth": 4,
                "fail_to_pass_tests": ["tests/test_api.py::test_fix"],
                "pass_to_pass_tests": ["tests/test_api.py::test_existing"],
                "degradation_targets": {
                    "type_hints": {"target_files": ["src/app.py"]},
                    "naming": {"target_files": ["src/app.py"]},
                    "comments_docstrings": {"target_files": ["src/app.py"]},
                    "remove_tests": {"delete_files": ["tests/test_api.py"], "preserve_files": []},
                },
            }
        ],
    }))
    (packets_dir / "httpx_experiment_packet.json").write_text(json.dumps({
        "suggested_decision": {"status": "GO", "reason": "ready"},
    }))
    (candidates_dir / "httpx_pr_1.json").write_text(json.dumps({
        "candidate_id": "httpx_pr_1",
        "title": "Fix connection reuse bug",
        "description": "Reproduce and fix the stale connection behavior.",
    }))

    plan_path = build_repo_run_plan(
        repo="encode/httpx",
        deep_results_dir=deep_results_dir,
        packet_dir=packets_dir,
        candidates_dir=candidates_dir,
        output_dir=output_dir,
        harnesses=None,
        replications=2,
    )

    plan = json.loads(plan_path.read_text())
    assert plan["stage5_status"]["status"] == "READY"
    assert plan["summary"]["verified_task_count"] == 1
    assert plan["summary"]["planned_runs"] == 20
    assert [h["id"] for h in plan["run_policy"]["harnesses"]] == ["claude_code", "codex_cli"]
    assert Path(str(plan_path).replace(".json", ".md")).exists()

    first_run = plan["runs"][0]
    assert first_run["task_prompt"]["title"] == "Fix connection reuse bug"
    assert first_run["stage4_plan"]["mode"] == "clean"
    assert first_run["workspace"]["env_commit_sha"] == "env123"
    assert first_run["output_paths"]["root"].startswith("runs/httpx/httpx_pr_1/")

    degraded = next(run for run in plan["runs"] if run["condition"] == "naming")
    assert degraded["stage4_plan"]["degradation"] == "naming"
    assert degraded["stage4_plan"]["targets"] == {"target_files": ["src/app.py"]}


def test_build_repo_run_plan_blocks_on_no_go_packet(tmp_path: Path):
    deep_results_dir = tmp_path / "deep_results"
    packets_dir = tmp_path / "packets"
    candidates_dir = tmp_path / "candidates"
    output_dir = tmp_path / "run_plans"

    deep_results_dir.mkdir()
    packets_dir.mkdir()
    candidates_dir.mkdir()

    (deep_results_dir / "httpx_verified_manifest.json").write_text(json.dumps({
        "repo": "encode/httpx",
        "verified_prs": [
            {
                "candidate_id": "httpx_pr_1",
                "pr_number": 1,
                "base_commit_sha": "base123",
                "degradation_targets": {},
            }
        ],
    }))
    (packets_dir / "httpx_experiment_packet.json").write_text(json.dumps({
        "suggested_decision": {"status": "NO_GO", "reason": "zero verified depth"},
    }))

    plan_path = build_repo_run_plan(
        repo="encode/httpx",
        deep_results_dir=deep_results_dir,
        packet_dir=packets_dir,
        candidates_dir=candidates_dir,
        output_dir=output_dir,
        harnesses=["claude-code"],
        replications=3,
    )

    plan = json.loads(plan_path.read_text())
    assert plan["stage5_status"]["status"] == "BLOCKED"
    assert plan["summary"]["planned_runs"] == 0
    assert plan["runs"] == []
