"""Tests for the profile-aware Stage 2 probe helpers."""

from __future__ import annotations

from pathlib import Path

from src.profiles import repo_profile_from_dict
from src.workflow import stage2_probe


def test_resolve_probe_commits_uses_explicit_commits(tmp_path: Path, monkeypatch) -> None:
    bare_repo = tmp_path / "repo.git"
    bare_repo.mkdir()

    monkeypatch.setattr(stage2_probe, "verify_commit_exists", lambda _repo, _sha: True)

    commits = stage2_probe._resolve_probe_commits(
        bare_repo=bare_repo,
        commits=["abc", "abc", "def"],
        sample_size=3,
    )

    assert commits == ["abc", "def"]


def test_summarize_probe_marks_partial_success_as_review() -> None:
    summary = stage2_probe._summarize_probe([
        {"status": "PASS"},
        {"status": "FAIL"},
        {"status": "ERROR"},
    ])

    assert summary["overall_status"] == "REVIEW"
    assert summary["passed"] == 1
    assert summary["failed"] == 1
    assert summary["errored"] == 1


def test_build_probe_command_uses_profile_pytest_command(tmp_path: Path) -> None:
    profile = repo_profile_from_dict({
        "repo": "encode/httpx",
        "test": {
            "command": "pytest -q",
            "plugin_policy": {"mode": "explicit_only", "explicit_plugins": ["anyio.pytest_plugin"]},
        },
    })
    python_executable = tmp_path / ".venv" / "bin" / "python"

    command = stage2_probe.build_probe_test_command(
        python_executable=python_executable,
        repo_profile=profile,
    )

    assert command[:3] == [str(python_executable), "-m", "pytest"]
    assert "anyio.pytest_plugin" in command
    assert "--collect-only" in command


def test_probe_summary_includes_timeout_configuration(tmp_path: Path, monkeypatch) -> None:
    clones_dir = tmp_path / "clones"
    output_dir = tmp_path / "probe_results"
    bare_repo = clones_dir / "repo.git"
    worktree = clones_dir / "worktrees" / "stage2_probe_example_1"

    monkeypatch.setattr(stage2_probe, "ensure_clone", lambda repo, clones: bare_repo)
    monkeypatch.setattr(stage2_probe, "_resolve_probe_commits", lambda **kwargs: ["abc123"])
    monkeypatch.setattr(stage2_probe, "create_worktree", lambda bare, sha, path: path.mkdir(parents=True, exist_ok=True) or path)
    monkeypatch.setattr(stage2_probe, "sanitize_worktree", lambda worktree, sha: None)
    monkeypatch.setattr(stage2_probe, "cleanup_worktree", lambda bare, path: None)
    monkeypatch.setattr(
        stage2_probe,
        "_probe_one_commit",
        lambda **kwargs: {
            "repo": "owner/example",
            "commit_sha": "abc123",
            "status": "PASS",
            "reason": "ok",
            "install_success": True,
            "probe_success": True,
            "install_attempts": [],
            "probe_command": ["python", "-m", "pytest", "--collect-only"],
            "probe_elapsed_seconds": 1.0,
            "elapsed_seconds": 2.0,
        },
    )

    report_path = stage2_probe.run_stage2_probe(
        repo="owner/example",
        clones_dir=clones_dir,
        output_dir=output_dir,
        sample_size=1,
        install_timeout_seconds=17,
        probe_timeout_seconds=23,
    )

    payload = __import__("json").loads(report_path.read_text())
    assert payload["selection"]["install_timeout_seconds"] == 17
    assert payload["selection"]["probe_timeout_seconds"] == 23
