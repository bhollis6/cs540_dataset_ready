"""Tests for repo experiment packet assembly."""

from __future__ import annotations

import json
from pathlib import Path

from src.workflow.repo_packet import build_repo_experiment_packet


def test_build_repo_experiment_packet_combines_artifacts(tmp_path: Path):
    results_dir = tmp_path / "results"
    deep_results_dir = tmp_path / "deep_results"
    readiness_dir = tmp_path / "audit_results"
    packets_dir = tmp_path / "packets"

    results_dir.mkdir()
    deep_results_dir.mkdir()
    readiness_dir.mkdir()

    (results_dir / "httpx_selected_prs.json").write_text(json.dumps({
        "repo": "encode/httpx",
        "accepted": 4,
        "review": 1,
        "rejected": 0,
        "total_candidates": 5,
        "selected_prs": [
            {"candidate_id": "httpx_pr_1"},
            {"candidate_id": "httpx_pr_2"},
            {"candidate_id": "httpx_pr_3"},
            {"candidate_id": "httpx_pr_4"},
        ],
    }))
    (deep_results_dir / "httpx_verified_manifest.json").write_text(json.dumps({
        "repo": "encode/httpx",
        "stage2_accepted": 3,
        "preflight_passed": 3,
        "llm_stage2_accepted": 3,
        "navigation_depth_threshold": 3,
        "verified_prs": [
            {"candidate_id": "httpx_pr_1"},
            {"candidate_id": "httpx_pr_2"},
            {"candidate_id": "httpx_pr_3"},
        ],
    }))
    (readiness_dir / "httpx_repo_readiness.json").write_text(json.dumps({
        "audit": {
            "overall": {"status": "PASS", "reason": "ready"},
            "readiness": {"type_hints": {"status": "PASS"}},
        }
    }))
    (readiness_dir / "httpx_naming_readiness.json").write_text(json.dumps({
        "audit": {
            "dry_run": {"candidate_symbol_count": 927, "files_with_renames": 48},
            "live_run": {
                "rates": {
                    "rename_success_rate": 0.82,
                    "refactoring_error_rate": 0.12,
                    "offset_not_found_rate": 0.06,
                },
                "top_skipped_names": [{"name": "response", "count": 4}],
            },
        }
    }))

    packet_path = build_repo_experiment_packet(
        repo="encode/httpx",
        results_dir=results_dir,
        deep_results_dir=deep_results_dir,
        readiness_dir=readiness_dir,
        naming_audit_dir=None,
        output_dir=packets_dir,
    )

    packet = json.loads(packet_path.read_text())
    assert packet["summary"]["stage1"]["status"] == "PASS"
    assert packet["summary"]["stage2"]["status"] == "PASS"
    assert packet["summary"]["repo_readiness"]["status"] == "PASS"
    assert packet["summary"]["naming_audit"]["status"] == "PASS"
    assert packet["suggested_decision"]["status"] == "GO"
    assert Path(str(packet_path).replace(".json", ".md")).exists()
    assert packet["admission_rubric"][0]["id"] == "repo_static_surface"
    assert packet["admission_rubric"][2]["status"] == "PASS"


def test_build_repo_experiment_packet_flags_missing_verified_tasks(tmp_path: Path):
    results_dir = tmp_path / "results"
    readiness_dir = tmp_path / "audit_results"
    packets_dir = tmp_path / "packets"

    results_dir.mkdir()
    readiness_dir.mkdir()

    (results_dir / "httpx_selected_prs.json").write_text(json.dumps({
        "repo": "encode/httpx",
        "accepted": 1,
        "review": 0,
        "rejected": 0,
        "total_candidates": 1,
        "selected_prs": [{"candidate_id": "httpx_pr_1"}],
    }))
    (readiness_dir / "httpx_repo_readiness.json").write_text(json.dumps({
        "audit": {
            "overall": {"status": "PASS", "reason": "ready"},
            "readiness": {},
        }
    }))
    (readiness_dir / "httpx_naming_readiness.json").write_text(json.dumps({
        "audit": {
            "dry_run": {"candidate_symbol_count": 927, "files_with_renames": 48},
        }
    }))

    packet_path = build_repo_experiment_packet(
        repo="encode/httpx",
        results_dir=results_dir,
        deep_results_dir=tmp_path / "deep_results",
        readiness_dir=readiness_dir,
        naming_audit_dir=None,
        output_dir=packets_dir,
    )

    packet = json.loads(packet_path.read_text())
    assert packet["summary"]["stage2"]["status"] == "MISSING"
    assert packet["summary"]["naming_audit"]["status"] == "REVIEW"
    assert packet["suggested_decision"]["status"] == "NO_GO"
    assert any(
        criterion["id"] == "stage2_verified_tasks" and criterion["status"] == "MISSING"
        for criterion in packet["admission_rubric"]
    )
