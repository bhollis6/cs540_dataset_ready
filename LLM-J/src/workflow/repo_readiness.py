"""Repo-level degradation readiness orchestration."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from src.deep_eval.repo_manager import (
    cleanup_worktree,
    create_worktree,
    ensure_clone,
    sanitize_worktree,
    verify_commit_exists,
)


def run_repo_readiness_audit(
    *,
    repo: str,
    clones_dir: Path,
    output_dir: Path,
    sample_limit: int = 10,
    commit_sha: str | None = None,
    keep_worktree: bool = False,
) -> Path:
    """Create a disposable worktree and generate a repo-level readiness report."""
    output_dir.mkdir(parents=True, exist_ok=True)

    bare_repo = ensure_clone(repo, clones_dir)
    audited_commit = commit_sha or _resolve_head_commit(bare_repo)
    if not verify_commit_exists(bare_repo, audited_commit):
        raise ValueError(f"Commit {audited_commit} is not reachable in {bare_repo}")

    repo_short = repo.split("/")[-1]
    worktree = clones_dir / "worktrees" / f"readiness_{repo_short}"
    child_output = output_dir / f"{repo_short}_repo_readiness_raw.json"
    final_output = output_dir / f"{repo_short}_repo_readiness.json"

    try:
        create_worktree(bare_repo, audited_commit, worktree)
        sanitize_worktree(worktree, audited_commit)
        _run_child_repo_readiness(
            worktree=worktree,
            output_path=child_output,
            sample_limit=sample_limit,
        )
        with open(child_output) as f:
            audit = json.load(f)

        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "repo": repo,
            "repo_short": repo_short,
            "audited_commit": audited_commit,
            "worktree_path": str(worktree),
            "audit": audit,
        }

        with open(final_output, "w") as f:
            json.dump(report, f, indent=2)
    finally:
        if child_output.exists():
            child_output.unlink()
        if not keep_worktree:
            cleanup_worktree(bare_repo, worktree)

    return final_output


def _run_child_repo_readiness(
    *,
    worktree: Path,
    output_path: Path,
    sample_limit: int,
) -> None:
    script_path = _repo_readiness_script_path()
    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            str(worktree),
            "--sample-limit",
            str(sample_limit),
            "--output",
            str(output_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    stdout_lines = [
        line for line in result.stdout.splitlines()
        if not line.startswith("Wrote repo readiness to ")
    ]
    if stdout_lines:
        print("\n".join(stdout_lines))


def _repo_readiness_script_path() -> Path:
    return Path(__file__).resolve().parents[3] / "degradation" / "repo_readiness.py"


def _resolve_head_commit(bare_repo: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(bare_repo), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()
