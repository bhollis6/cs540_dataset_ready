"""Tests for Stage 4 workspace materialization."""

from __future__ import annotations

import json
from pathlib import Path

from src.workflow import stage4_executor


def test_materialize_stage4_runs_writes_workspace_artifacts(tmp_path: Path, monkeypatch):
    clones_dir = tmp_path / "clones"
    run_plan_dir = tmp_path / "run_plans"
    output_dir = tmp_path / "materialized"
    bare_repo = clones_dir / "httpx.git"
    run_plan_dir.mkdir()

    (run_plan_dir / "httpx_run_plan.json").write_text(json.dumps({
        "repo": "encode/httpx",
        "repo_short": "httpx",
        "stage5_status": {"status": "READY"},
        "runs": [
            {
                "run_id": "httpx__httpx_pr_1__claude_code__remove_tests__rep1",
                "repo": "encode/httpx",
                "candidate_id": "httpx_pr_1",
                "pr_number": 1,
                "condition": "remove_tests",
                "replication": 1,
                "harness": {"id": "claude_code", "runner": "claude-code"},
                "workspace": {
                    "base_commit_sha": "base123",
                    "merge_commit_sha": "merge123",
                    "head_commit_sha": "head123",
                },
                "task_prompt": {
                    "title": "Fix flaky test behavior",
                    "description": "Recreate the failing historical state and repair it.",
                },
                "oracle": {
                    "fail_to_pass_tests": ["tests/test_api.py::test_fix"],
                    "pass_to_pass_tests": [],
                },
                "stage4_plan": {
                    "mode": "degraded",
                    "degradation": "remove_tests",
                    "targets": {
                        "delete_files": ["tests/test_api.py"],
                        "preserve_files": ["tests/conftest.py"],
                    },
                },
                "output_paths": {
                    "root": "runs/httpx/httpx_pr_1/claude_code/remove_tests/rep_1",
                },
            }
        ],
    }), encoding="utf-8")

    monkeypatch.setattr(stage4_executor, "ensure_clone", lambda repo, clones: bare_repo)
    monkeypatch.setattr(stage4_executor, "verify_commit_exists", lambda bare, sha: True)
    monkeypatch.setattr(stage4_executor, "sanitize_worktree", lambda workspace, sha: None)

    def fake_create_worktree(bare: Path, sha: str, workspace: Path) -> Path:
        (workspace / "tests").mkdir(parents=True, exist_ok=True)
        (workspace / "tests" / "test_api.py").write_text(
            "def test_api():\n    assert True\n",
            encoding="utf-8",
        )
        (workspace / "tests" / "conftest.py").write_text("VALUE = 1\n", encoding="utf-8")
        (workspace / "app.py").write_text("def app():\n    return 1\n", encoding="utf-8")
        return workspace

    monkeypatch.setattr(stage4_executor, "create_worktree", fake_create_worktree)

    summary_path = stage4_executor.materialize_stage4_runs(
        repo="encode/httpx",
        run_plan_dir=run_plan_dir,
        clones_dir=clones_dir,
        output_dir=output_dir,
    )

    summary = json.loads(summary_path.read_text())
    assert summary["summary"]["materialized"] == 1
    run_result = summary["results"][0]
    assert run_result["status"] == "PASS"

    run_root = output_dir / "runs/httpx/httpx_pr_1/claude_code/remove_tests/rep_1"
    metadata = json.loads((run_root / "metadata.json").read_text())
    assert metadata["stage4_result"]["summary"]["deleted_files"] == ["tests/test_api.py"]
    assert (run_root / "issue_prompt.md").exists()
    assert (run_root / "logs").is_dir()
    assert not (run_root / "workspace" / "tests" / "test_api.py").exists()
    assert (run_root / "workspace" / "tests" / "conftest.py").exists()
