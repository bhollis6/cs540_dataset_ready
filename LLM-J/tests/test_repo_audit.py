"""Tests for repo-level naming audit orchestration."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.workflow import repo_audit


def test_run_repo_naming_audit_writes_wrapped_report(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    clones_dir = tmp_path / "clones"
    output_dir = tmp_path / "audit_results"
    bare_repo = clones_dir / "example.git"
    worktree = clones_dir / "worktrees" / "audit_example"

    monkeypatch.setattr(repo_audit, "ensure_clone", lambda repo, clones: bare_repo)
    monkeypatch.setattr(repo_audit, "_resolve_head_commit", lambda bare: "abc123")
    monkeypatch.setattr(repo_audit, "verify_commit_exists", lambda bare, sha: True)
    monkeypatch.setattr(repo_audit, "create_worktree", lambda bare, sha, path: path.mkdir(parents=True, exist_ok=True) or path)
    monkeypatch.setattr(repo_audit, "sanitize_worktree", lambda worktree, sha: None)

    cleaned: list[Path] = []
    monkeypatch.setattr(repo_audit, "cleanup_worktree", lambda bare, path: cleaned.append(path))

    def fake_child(*, worktree: Path, output_path: Path, sample_limit: int, live: bool) -> None:
        output_path.write_text(json.dumps({
            "generated_at": "2026-04-21T00:00:00Z",
            "repo_path": str(worktree),
            "dry_run": {
                "candidate_symbol_count": 12,
                "rename_counts": {"classes": 1, "functions": 4, "variables": 7, "total": 12},
            },
        }))

    monkeypatch.setattr(repo_audit, "_run_child_naming_audit", fake_child)

    report_path = repo_audit.run_repo_naming_audit(
        repo="owner/example",
        clones_dir=clones_dir,
        output_dir=output_dir,
        sample_limit=5,
        live=False,
    )

    report = json.loads(report_path.read_text())
    assert report["repo"] == "owner/example"
    assert report["repo_short"] == "example"
    assert report["audited_commit"] == "abc123"
    assert report["audit_mode"] == "dry-run"
    assert report["audit"]["dry_run"]["candidate_symbol_count"] == 12
    assert cleaned == [worktree]


def test_run_repo_naming_audit_can_keep_worktree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    clones_dir = tmp_path / "clones"
    output_dir = tmp_path / "audit_results"
    bare_repo = clones_dir / "example.git"

    monkeypatch.setattr(repo_audit, "ensure_clone", lambda repo, clones: bare_repo)
    monkeypatch.setattr(repo_audit, "_resolve_head_commit", lambda bare: "abc123")
    monkeypatch.setattr(repo_audit, "verify_commit_exists", lambda bare, sha: True)
    monkeypatch.setattr(repo_audit, "create_worktree", lambda bare, sha, path: path.mkdir(parents=True, exist_ok=True) or path)
    monkeypatch.setattr(repo_audit, "sanitize_worktree", lambda worktree, sha: None)
    monkeypatch.setattr(repo_audit, "_run_child_naming_audit", lambda **kwargs: kwargs["output_path"].write_text(json.dumps({"dry_run": {}})))

    cleaned: list[Path] = []
    monkeypatch.setattr(repo_audit, "cleanup_worktree", lambda bare, path: cleaned.append(path))

    repo_audit.run_repo_naming_audit(
        repo="owner/example",
        clones_dir=clones_dir,
        output_dir=output_dir,
        keep_worktree=True,
    )

    assert cleaned == []


def test_build_audit_command_uses_uv_for_live(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(repo_audit.shutil, "which", lambda cmd: "/usr/bin/uv")

    command = repo_audit._build_audit_command(
        script_path=Path("/tmp/naming_audit.py"),
        worktree=Path("/tmp/worktree"),
        output_path=Path("/tmp/report.json"),
        sample_limit=3,
        live=True,
    )

    assert command[:5] == ["uv", "run", "--with", "rope", "python"]
    assert command[-1] == "--live"


def test_build_audit_command_requires_uv_for_live(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(repo_audit.shutil, "which", lambda cmd: None)

    with pytest.raises(RuntimeError):
        repo_audit._build_audit_command(
            script_path=Path("/tmp/naming_audit.py"),
            worktree=Path("/tmp/worktree"),
            output_path=Path("/tmp/report.json"),
            sample_limit=3,
            live=True,
        )


def test_build_audit_environment_sets_writable_uv_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("UV_CACHE_DIR", raising=False)

    env = repo_audit._build_audit_environment(
        output_path=tmp_path / "audit_results" / "report.json",
        live=True,
    )

    assert env is not None
    assert env["UV_CACHE_DIR"] == str(tmp_path / "audit_results" / ".uv-cache")


def test_build_audit_environment_is_none_for_dry_run(tmp_path: Path):
    env = repo_audit._build_audit_environment(
        output_path=tmp_path / "audit_results" / "report.json",
        live=False,
    )

    assert env is None
