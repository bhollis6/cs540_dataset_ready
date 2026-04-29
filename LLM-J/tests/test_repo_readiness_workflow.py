"""Tests for repo-level readiness orchestration."""

from __future__ import annotations

import json
from pathlib import Path

from src.workflow import repo_readiness


def test_run_repo_readiness_audit_writes_wrapped_report(tmp_path: Path, monkeypatch):
    clones_dir = tmp_path / "clones"
    output_dir = tmp_path / "audit_results"
    bare_repo = clones_dir / "example.git"
    worktree = clones_dir / "worktrees" / "readiness_example"

    monkeypatch.setattr(repo_readiness, "ensure_clone", lambda repo, clones: bare_repo)
    monkeypatch.setattr(repo_readiness, "_resolve_head_commit", lambda bare: "abc123")
    monkeypatch.setattr(repo_readiness, "verify_commit_exists", lambda bare, sha: True)
    monkeypatch.setattr(repo_readiness, "create_worktree", lambda bare, sha, path: path.mkdir(parents=True, exist_ok=True) or path)
    monkeypatch.setattr(repo_readiness, "sanitize_worktree", lambda worktree, sha: None)

    cleaned: list[Path] = []
    monkeypatch.setattr(repo_readiness, "cleanup_worktree", lambda bare, path: cleaned.append(path))

    def fake_child(*, worktree: Path, output_path: Path, sample_limit: int) -> None:
        output_path.write_text(json.dumps({
            "overall": {"status": "REVIEW"},
            "readiness": {"naming": {"status": "PASS"}},
        }))

    monkeypatch.setattr(repo_readiness, "_run_child_repo_readiness", fake_child)

    report_path = repo_readiness.run_repo_readiness_audit(
        repo="owner/example",
        clones_dir=clones_dir,
        output_dir=output_dir,
        sample_limit=5,
    )

    report = json.loads(report_path.read_text())
    assert report["repo"] == "owner/example"
    assert report["repo_short"] == "example"
    assert report["audited_commit"] == "abc123"
    assert report["audit"]["overall"]["status"] == "REVIEW"
    assert cleaned == [worktree]
