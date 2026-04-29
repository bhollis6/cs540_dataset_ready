"""Tests for Stage 2 deep evaluation orchestration."""

from __future__ import annotations

import json
from pathlib import Path

from src.config import Config
from src.deep_eval import deep_judge
from src.deep_eval.models import ContextStats, PreflightResult


def test_deep_evaluate_repo_passes_repo_profile_to_preflight(
    tmp_path: Path,
    monkeypatch,
) -> None:
    candidates_dir = tmp_path / "candidates"
    clones_dir = tmp_path / "clones"
    candidates_dir.mkdir()
    clones_dir.mkdir()

    candidate_id = "httpx_pr_1"
    (candidates_dir / f"{candidate_id}.json").write_text(json.dumps({
        "candidate_id": candidate_id,
        "patch_diff": "patch",
        "test_diff": "tests",
        "test_files": ["tests/test_auth.py"],
        "source_files": ["httpx/_auth.py"],
    }))

    config = Config()
    config.clones_dir = clones_dir
    config.preflight_only = True
    config.context_budget_chars = None
    config.profiles_dir = tmp_path / "repo_profiles"

    bare_repo = clones_dir / "httpx.git"
    worktree = clones_dir / "worktrees" / candidate_id

    monkeypatch.setattr(deep_judge, "ensure_clone", lambda repo, clones: bare_repo)
    monkeypatch.setattr(deep_judge, "verify_commit_exists", lambda bare, sha: True)
    monkeypatch.setattr(
        deep_judge,
        "create_worktree",
        lambda bare, sha, path: path.mkdir(parents=True, exist_ok=True) or path,
    )
    monkeypatch.setattr(deep_judge, "sanitize_worktree", lambda worktree, sha: None)
    monkeypatch.setattr(deep_judge, "cleanup_worktree", lambda bare, worktree: None)
    monkeypatch.setattr(
        deep_judge,
        "collect_context_files",
        lambda worktree, source_files, max_chars=None: ({"httpx/_auth.py": "x = 1\n"}, {}, False),
    )

    captured: dict[str, object] = {}
    fake_profile = object()
    monkeypatch.setattr(deep_judge, "load_repo_profile", lambda repo, profiles_dir: fake_profile)

    def fake_run_preflight(**kwargs):
        captured.update(kwargs)
        return PreflightResult(
            candidate_id=kwargs["candidate_id"],
            status="PASS",
            reason="1 tests went FAIL→PASS",
            fail_to_pass_tests=["tests/test_auth.py::test_fix"],
            pass_to_pass_tests=["tests/test_auth.py::test_existing"],
            install_success=True,
        )

    monkeypatch.setattr(deep_judge, "run_preflight", fake_run_preflight)

    results = deep_judge.deep_evaluate_repo(
        repo="encode/httpx",
        accepted_prs=[{
            "candidate_id": candidate_id,
            "pr_number": 1,
            "base_commit_sha": "base123",
            "total_score": 22,
        }],
        candidates_dir=candidates_dir,
        config=config,
    )

    assert len(results) == 1
    assert isinstance(results[0].context_stats, ContextStats)
    assert captured["repo_profile"] is fake_profile
    assert captured["test_files"] == ["tests/test_auth.py"]
    assert captured["worktree"] == worktree
