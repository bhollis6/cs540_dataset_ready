"""Profile-aware Stage 2 environment probing."""

from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.deep_eval.preflight import (
    _ensure_preflight_venv,
    _install_project,
    _looks_like_pytest_execution_error,
    build_probe_environment,
    build_probe_test_command,
)
from src.deep_eval.repo_manager import (
    cleanup_worktree,
    create_worktree,
    ensure_clone,
    sanitize_worktree,
    verify_commit_exists,
)
from src.profiles import load_repo_profile


def run_stage2_probe(
    *,
    repo: str,
    clones_dir: Path,
    output_dir: Path,
    profiles_dir: Path = Path("repo_profiles"),
    commits: list[str] | None = None,
    sample_size: int = 3,
    install_timeout_seconds: int = 60,
    probe_timeout_seconds: int = 60,
    keep_worktrees: bool = False,
) -> Path:
    """Probe historical environment viability for one repo under the Stage 2 contract."""
    output_dir.mkdir(parents=True, exist_ok=True)
    bare_repo = ensure_clone(repo, clones_dir)
    repo_short = repo.split("/")[-1]
    repo_profile = load_repo_profile(repo, profiles_dir)
    selected_commits = _resolve_probe_commits(
        bare_repo=bare_repo,
        commits=commits,
        sample_size=sample_size,
    )

    results: list[dict[str, Any]] = []
    for index, commit_sha in enumerate(selected_commits, start=1):
        worktree = clones_dir / "worktrees" / f"stage2_probe_{repo_short}_{index}"
        try:
            create_worktree(bare_repo, commit_sha, worktree)
            sanitize_worktree(worktree, commit_sha)
            results.append(
                _probe_one_commit(
                    repo=repo,
                    commit_sha=commit_sha,
                    worktree=worktree,
                    repo_profile=repo_profile,
                    install_timeout_seconds=install_timeout_seconds,
                    probe_timeout_seconds=probe_timeout_seconds,
                )
            )
        finally:
            if not keep_worktrees:
                cleanup_worktree(bare_repo, worktree)

    summary = _summarize_probe(results)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo": repo,
        "repo_short": repo_short,
        "execution_mode": "host_venv_profiled",
        "target_execution_mode": "containerized_stage2_probe",
        "profile": {
            "loaded": repo_profile is not None,
            "path": str(repo_profile.source_path) if repo_profile and repo_profile.source_path else None,
            "runtime": {
                "python": repo_profile.runtime.python if repo_profile else None,
                "package_manager": repo_profile.runtime.package_manager if repo_profile else None,
            },
            "test_command": repo_profile.test.command if repo_profile else None,
        },
        "selection": {
            "requested_commits": commits or [],
            "sample_size": sample_size,
            "install_timeout_seconds": install_timeout_seconds,
            "probe_timeout_seconds": probe_timeout_seconds,
            "probed_commits": selected_commits,
        },
        "results": results,
        "summary": summary,
    }

    output_path = output_dir / f"{repo_short}_stage2_probe.json"
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    markdown_path = output_dir / f"{repo_short}_stage2_probe.md"
    markdown_path.write_text(_render_probe_markdown(report), encoding="utf-8")
    return output_path


def _resolve_probe_commits(
    *,
    bare_repo: Path,
    commits: list[str] | None,
    sample_size: int,
) -> list[str]:
    if commits:
        unique_commits: list[str] = []
        seen: set[str] = set()
        for commit_sha in commits:
            if commit_sha in seen:
                continue
            if not verify_commit_exists(bare_repo, commit_sha):
                raise ValueError(f"Commit {commit_sha} is not reachable in {bare_repo}")
            seen.add(commit_sha)
            unique_commits.append(commit_sha)
        return unique_commits

    result = subprocess.run(
        [
            "git",
            "-C",
            str(bare_repo),
            "rev-list",
            "--first-parent",
            "--max-count",
            str(sample_size),
            "HEAD",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    commits_from_history = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not commits_from_history:
        raise ValueError(f"Could not sample probe commits from {bare_repo}")
    return commits_from_history


def _probe_one_commit(
    *,
    repo: str,
    commit_sha: str,
    worktree: Path,
    repo_profile: Any,
    install_timeout_seconds: int,
    probe_timeout_seconds: int,
) -> dict[str, Any]:
    started = time.time()
    python_executable, venv_output = _ensure_preflight_venv(worktree)
    if python_executable is None:
        return {
            "repo": repo,
            "commit_sha": commit_sha,
            "status": "ERROR",
            "reason": "Failed to create isolated probe virtualenv",
            "install_success": False,
            "probe_success": False,
            "venv_output": venv_output[:2000],
            "elapsed_seconds": time.time() - started,
        }

    install_result = _install_project(
        worktree,
        python_executable=python_executable,
        repo_profile=repo_profile,
        install_timeout_seconds=install_timeout_seconds,
    )
    if not install_result.success:
        return {
            "repo": repo,
            "commit_sha": commit_sha,
            "status": "ERROR",
            "reason": "Failed to install project for Stage 2 probe",
            "install_success": False,
            "probe_success": False,
            "install_attempts": install_result.attempts or [],
            "install_output": install_result.output[:2000],
            "elapsed_seconds": time.time() - started,
        }

    probe_command = build_probe_test_command(
        python_executable=python_executable,
        repo_profile=repo_profile,
    )
    env = build_probe_environment(repo_profile=repo_profile)
    try:
        probe_started = time.time()
        result = subprocess.run(
            probe_command,
            capture_output=True,
            text=True,
            timeout=probe_timeout_seconds,
            cwd=str(worktree),
            env=env,
        )
    except subprocess.TimeoutExpired:
        return {
            "repo": repo,
            "commit_sha": commit_sha,
            "status": "ERROR",
            "reason": "Stage 2 probe timed out",
            "install_success": True,
            "probe_success": False,
            "install_attempts": install_result.attempts or [],
            "probe_command": probe_command,
            "probe_elapsed_seconds": time.time() - probe_started,
            "elapsed_seconds": time.time() - started,
        }
    except FileNotFoundError:
        return {
            "repo": repo,
            "commit_sha": commit_sha,
            "status": "ERROR",
            "reason": "Probe command executable not found",
            "install_success": True,
            "probe_success": False,
            "install_attempts": install_result.attempts or [],
            "probe_command": probe_command,
            "elapsed_seconds": time.time() - started,
        }

    output = (result.stdout or "") + (result.stderr or "")
    if _looks_like_pytest_execution_error(output, result.returncode):
        return {
            "repo": repo,
            "commit_sha": commit_sha,
            "status": "ERROR",
            "reason": "Probe command failed to execute cleanly",
            "install_success": True,
            "probe_success": False,
            "install_attempts": install_result.attempts or [],
            "probe_command": probe_command,
            "probe_elapsed_seconds": time.time() - probe_started,
            "probe_output": output[:2000],
            "elapsed_seconds": time.time() - started,
        }

    if result.returncode != 0:
        return {
            "repo": repo,
            "commit_sha": commit_sha,
            "status": "FAIL",
            "reason": "Probe command returned a non-zero exit code",
            "install_success": True,
            "probe_success": False,
            "install_attempts": install_result.attempts or [],
            "probe_command": probe_command,
            "probe_elapsed_seconds": time.time() - probe_started,
            "probe_output": output[:2000],
            "elapsed_seconds": time.time() - started,
        }

    return {
        "repo": repo,
        "commit_sha": commit_sha,
        "status": "PASS",
        "reason": "Install and test collection probe passed",
        "install_success": True,
        "probe_success": True,
        "install_attempts": install_result.attempts or [],
        "probe_command": probe_command,
        "probe_elapsed_seconds": time.time() - probe_started,
        "elapsed_seconds": time.time() - started,
    }


def _summarize_probe(results: list[dict[str, Any]]) -> dict[str, Any]:
    passed = sum(1 for result in results if result["status"] == "PASS")
    failed = sum(1 for result in results if result["status"] == "FAIL")
    errored = sum(1 for result in results if result["status"] == "ERROR")

    if passed == len(results) and results:
        overall = "PASS"
        reason = "All sampled commits passed the profile-aware Stage 2 probe."
    elif passed > 0:
        overall = "REVIEW"
        reason = "Some sampled commits passed, but probe failures still need review."
    else:
        overall = "FAIL"
        reason = "No sampled commits passed the Stage 2 probe."

    return {
        "overall_status": overall,
        "reason": reason,
        "probed_commits": len(results),
        "passed": passed,
        "failed": failed,
        "errored": errored,
    }


def _render_probe_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Stage 2 Probe: {report['repo']}",
        "",
        f"- Generated: {report['generated_at']}",
        f"- Execution mode: {report['execution_mode']}",
        f"- Target mode: {report['target_execution_mode']}",
        f"- Profile loaded: {report['profile']['loaded']}",
        f"- Summary: {report['summary']['overall_status']} — {report['summary']['reason']}",
        "",
        "## Results",
    ]
    for result in report["results"]:
        lines.extend(
            [
                "",
                f"### {result['commit_sha']}",
                f"- Status: {result['status']}",
                f"- Reason: {result['reason']}",
                f"- Install success: {result['install_success']}",
                f"- Install attempts: {len(result.get('install_attempts', []))}",
                f"- Elapsed seconds: {result['elapsed_seconds']:.2f}",
            ]
        )
    return "\n".join(lines) + "\n"
