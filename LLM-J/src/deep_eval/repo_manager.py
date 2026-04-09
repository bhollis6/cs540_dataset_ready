"""Clone management and git worktree operations."""

from __future__ import annotations

import subprocess
from pathlib import Path


def ensure_clone(repo: str, clones_dir: Path) -> Path:
    """Clone a repo as a bare clone if not already present. Returns the bare repo path."""
    repo_name = repo.split("/")[-1]
    bare_path = clones_dir / f"{repo_name}.git"

    if bare_path.exists():
        print(f"    Using existing clone: {bare_path}")
        return bare_path

    clones_dir.mkdir(parents=True, exist_ok=True)
    print(f"    Cloning {repo} (bare)...")
    subprocess.run(
        ["git", "clone", "--bare", f"https://github.com/{repo}.git", str(bare_path)],
        check=True,
        capture_output=True,
        text=True,
        timeout=300,
    )
    return bare_path


def verify_commit_exists(bare_repo: Path, commit_sha: str) -> bool:
    """Check if a commit SHA exists in the bare repo."""
    result = subprocess.run(
        ["git", "-C", str(bare_repo), "cat-file", "-t", commit_sha],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and result.stdout.strip() == "commit"


def create_worktree(bare_repo: Path, commit_sha: str, worktree_dir: Path) -> Path:
    """Create a detached worktree at the given commit. Returns the worktree path."""
    if worktree_dir.exists():
        cleanup_worktree(bare_repo, worktree_dir)

    worktree_dir.parent.mkdir(parents=True, exist_ok=True)
    # Must use absolute paths — git worktree add resolves relative to the repo, not CWD
    abs_worktree = str(worktree_dir.resolve())
    subprocess.run(
        ["git", "-C", str(bare_repo), "worktree", "add", "--detach",
         abs_worktree, commit_sha],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return worktree_dir


def cleanup_worktree(bare_repo: Path, worktree_dir: Path) -> None:
    """Remove a worktree and clean up."""
    abs_worktree = str(worktree_dir.resolve())
    if worktree_dir.exists():
        subprocess.run(
            ["git", "-C", str(bare_repo), "worktree", "remove", "--force",
             abs_worktree],
            capture_output=True,
            text=True,
        )
    # Prune stale worktree references
    subprocess.run(
        ["git", "-C", str(bare_repo), "worktree", "prune"],
        capture_output=True,
        text=True,
    )


def sanitize_worktree(worktree: Path, base_commit_sha: str) -> None:
    """SWE-bench style sanitization: remove remote, delete future tags, clean reflog.

    Ensures the agent (or anyone exploring the worktree) cannot see future commits.
    """
    git = ["git", "-C", str(worktree)]

    # Remove remote so agent can't fetch future commits
    subprocess.run(git + ["remote", "remove", "origin"], capture_output=True, text=True)

    # Get base commit timestamp
    result = subprocess.run(
        git + ["show", "-s", "--format=%ci", base_commit_sha],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return

    # Expire reflog and garbage collect
    subprocess.run(git + ["reflog", "expire", "--expire=now", "--all"],
                   capture_output=True, text=True)
    subprocess.run(git + ["gc", "--prune=now"],
                   capture_output=True, text=True)
