"""Tests for Stage 2 runtime comparison and authority rules."""

from __future__ import annotations

import json
from pathlib import Path

from src.workflow.stage2_runtime import (
    build_stage2_runtime_comparison_matrix,
    summarize_stage2_runtime,
)


def test_summarize_stage2_runtime_prefers_container_success(tmp_path: Path) -> None:
    host_root = tmp_path / "host"
    container_root = tmp_path / "container"
    host_dir = host_root / "httpx"
    host_dir.mkdir(parents=True)
    container_root.mkdir(parents=True)

    (host_dir / "httpx_stage2_probe.json").write_text(json.dumps({
        "summary": {"overall_status": "FAIL", "reason": "host failed", "probed_commits": 1},
        "results": [
            {
                "commit_sha": "abc123",
                "status": "ERROR",
                "reason": "install failed",
                "install_output": "No solution found when resolving: hatchling",
            }
        ],
    }))

    probe_result_path = tmp_path / "httpx_probe_result.json"
    probe_result_path.write_text(json.dumps({
        "install_status": "success",
        "probe_status": "success",
        "probe_exit_code": 0,
        "probe_command": "python -m pytest -q --collect-only",
    }))
    (container_root / "httpx_stage2_container_bundles.json").write_text(json.dumps({
        "bundles": [
            {
                "commit_sha": "abc123",
                "default_probe_result": str(probe_result_path),
                "bundle_dir": str(tmp_path / "httpx_bundle"),
            }
        ]
    }))

    summary = summarize_stage2_runtime(
        repo="encode/httpx",
        host_probe_root=host_root,
        container_bundle_root=container_root,
    )

    assert summary["status"] == "PASS"
    assert summary["authority_source"] == "container_probe"
    assert summary["container_probe"]["overall_status"] == "PASS"
    assert summary["host_probe"]["overall_status"] == "FAIL"
    assert summary["compared_commits"][0]["host_failure_signature"] == "hatchling"


def test_summarize_stage2_runtime_marks_host_only_success_as_review(tmp_path: Path) -> None:
    host_root = tmp_path / "host"
    host_dir = host_root / "httpx"
    host_dir.mkdir(parents=True)

    (host_dir / "httpx_stage2_probe.json").write_text(json.dumps({
        "summary": {"overall_status": "PASS", "reason": "host passed", "probed_commits": 1},
        "results": [{"commit_sha": "abc123", "status": "PASS", "reason": "ok"}],
    }))

    summary = summarize_stage2_runtime(
        repo="encode/httpx",
        host_probe_root=host_root,
        container_bundle_root=tmp_path / "missing_container",
    )

    assert summary["status"] == "REVIEW"
    assert summary["authority_source"] == "host_probe_only"
    assert "container-backed" in summary["reason"]


def test_build_stage2_runtime_comparison_matrix_writes_markdown_and_json(tmp_path: Path) -> None:
    host_root = tmp_path / "host"
    container_root = tmp_path / "container"
    output_dir = tmp_path / "reports"
    host_dir = host_root / "httpx"
    host_dir.mkdir(parents=True)
    container_root.mkdir(parents=True)

    (host_dir / "httpx_stage2_probe.json").write_text(json.dumps({
        "summary": {"overall_status": "FAIL", "reason": "host failed", "probed_commits": 1},
        "results": [{"commit_sha": "abc123", "status": "ERROR", "reason": "install failed"}],
    }))
    probe_result_path = tmp_path / "probe_result.json"
    probe_result_path.write_text(json.dumps({
        "install_status": "success",
        "probe_status": "success",
    }))
    (container_root / "httpx_stage2_container_bundles.json").write_text(json.dumps({
        "bundles": [{"commit_sha": "abc123", "default_probe_result": str(probe_result_path)}]
    }))

    output_path = build_stage2_runtime_comparison_matrix(
        repos=["encode/httpx"],
        host_probe_root=host_root,
        container_bundle_root=container_root,
        output_dir=output_dir,
    )

    payload = json.loads(output_path.read_text())
    assert payload["summary"]["pass"] == 1
    assert payload["repos"][0]["status"] == "PASS"
    assert Path(str(output_path).replace(".json", ".md")).exists()
