"""Repo-level naming audit orchestration."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.deep_eval.repo_manager import (
    cleanup_worktree,
    create_worktree,
    ensure_clone,
    sanitize_worktree,
    verify_commit_exists,
)


def run_repo_naming_audit(
    *,
    repo: str,
    clones_dir: Path,
    output_dir: Path,
    sample_limit: int = 10,
    live: bool = False,
    commit_sha: str | None = None,
    keep_worktree: bool = False,
) -> Path:
    """Create a disposable worktree and generate a naming-readiness report."""
    output_dir.mkdir(parents=True, exist_ok=True)

    bare_repo = ensure_clone(repo, clones_dir)
    audited_commit = commit_sha or _resolve_head_commit(bare_repo)
    if not verify_commit_exists(bare_repo, audited_commit):
        raise ValueError(f"Commit {audited_commit} is not reachable in {bare_repo}")

    repo_short = repo.split("/")[-1]
    worktree = clones_dir / "worktrees" / f"audit_{repo_short}"
    child_output = output_dir / f"{repo_short}_naming_audit_raw.json"
    final_output = output_dir / f"{repo_short}_naming_readiness.json"

    try:
        create_worktree(bare_repo, audited_commit, worktree)
        sanitize_worktree(worktree, audited_commit)
        _run_child_naming_audit(
            worktree=worktree,
            output_path=child_output,
            sample_limit=sample_limit,
            live=live,
        )
        with open(child_output) as f:
            audit = json.load(f)

        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "repo": repo,
            "repo_short": repo_short,
            "audited_commit": audited_commit,
            "audit_mode": "live" if live else "dry-run",
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


def _run_child_naming_audit(
    *,
    worktree: Path,
    output_path: Path,
    sample_limit: int,
    live: bool,
) -> None:
    script_path = _naming_audit_script_path()
    command = _build_audit_command(
        script_path=script_path,
        worktree=worktree,
        output_path=output_path,
        sample_limit=sample_limit,
        live=live,
    )
    if live:
        subprocess.run(command, check=True)
        return

    result = subprocess.run(command, check=True, capture_output=True, text=True)
    stdout_lines = [
        line for line in result.stdout.splitlines()
        if not line.startswith("Wrote naming audit to ")
    ]
    if stdout_lines:
        print("\n".join(stdout_lines))


def _build_audit_command(
    *,
    script_path: Path,
    worktree: Path,
    output_path: Path,
    sample_limit: int,
    live: bool,
) -> list[str]:
    if live:
        if shutil.which("uv") is None:
            raise RuntimeError(
                "Live naming audits require 'uv' so the audit can bootstrap rope. "
                "Install uv or run a dry-run audit instead."
            )
        return [
            "uv",
            "run",
            "--with",
            "rope",
            "python",
            str(script_path),
            str(worktree),
            "--sample-limit",
            str(sample_limit),
            "--output",
            str(output_path),
            "--live",
        ]

    return [
        sys.executable,
        str(script_path),
        str(worktree),
        "--sample-limit",
        str(sample_limit),
        "--output",
        str(output_path),
    ]


def _naming_audit_script_path() -> Path:
    return Path(__file__).resolve().parents[3] / "degradation" / "naming_audit.py"


def _resolve_head_commit(bare_repo: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(bare_repo), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()
