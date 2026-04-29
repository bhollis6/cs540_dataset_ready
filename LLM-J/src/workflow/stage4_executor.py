"""Stage 4 workspace materialization from a Stage 5 run plan."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
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
from src.workflow.stage4_apply import apply_stage4_condition


def materialize_stage4_runs(
    *,
    repo: str,
    run_plan_dir: Path,
    clones_dir: Path,
    output_dir: Path,
    run_ids: list[str] | None = None,
    conditions: list[str] | None = None,
    harnesses: list[str] | None = None,
    limit: int | None = None,
    overwrite: bool = False,
) -> Path:
    """Materialize isolated Stage 4 workspaces for planned runs."""
    output_dir.mkdir(parents=True, exist_ok=True)

    repo_short = repo.split("/")[-1]
    run_plan_path = run_plan_dir / f"{repo_short}_run_plan.json"
    if not run_plan_path.exists():
        raise FileNotFoundError(f"Run plan not found: {run_plan_path}")

    with open(run_plan_path) as f:
        plan = json.load(f)

    stage5_status = plan.get("stage5_status", {}).get("status")
    if stage5_status == "BLOCKED":
        raise ValueError(f"Run plan is BLOCKED and should not be materialized: {run_plan_path}")

    selected_runs = _select_runs(
        plan.get("runs", []),
        run_ids=run_ids,
        conditions=conditions,
        harnesses=harnesses,
        limit=limit,
    )

    bare_repo = ensure_clone(repo, clones_dir)
    results: list[dict[str, Any]] = []
    for run in selected_runs:
        results.append(
            _materialize_one_run(
                bare_repo=bare_repo,
                run=run,
                output_dir=output_dir,
                overwrite=overwrite,
            )
        )

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo": repo,
        "repo_short": repo_short,
        "run_plan": {
            "path": str(run_plan_path),
            "stage5_status": stage5_status,
        },
        "selection": {
            "requested_run_ids": run_ids or [],
            "requested_conditions": sorted(conditions or []),
            "requested_harnesses": sorted(harnesses or []),
            "limit": limit,
            "selected_runs": len(selected_runs),
        },
        "results": results,
        "summary": {
            "materialized": sum(1 for result in results if result["status"] == "PASS"),
            "skipped": sum(1 for result in results if result["status"] == "SKIPPED"),
            "failed": sum(1 for result in results if result["status"] == "FAIL"),
        },
    }

    summary_path = output_dir / f"{repo_short}_stage4_materialization.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    markdown_path = output_dir / f"{repo_short}_stage4_materialization.md"
    markdown_path.write_text(_render_materialization_markdown(summary), encoding="utf-8")
    return summary_path


def _select_runs(
    runs: list[dict[str, Any]],
    *,
    run_ids: list[str] | None,
    conditions: list[str] | None,
    harnesses: list[str] | None,
    limit: int | None,
) -> list[dict[str, Any]]:
    selected = runs
    if run_ids:
        run_id_set = set(run_ids)
        selected = [run for run in selected if run.get("run_id") in run_id_set]
    if conditions:
        condition_set = set(conditions)
        selected = [run for run in selected if run.get("condition") in condition_set]
    if harnesses:
        harness_set = set(harnesses)
        selected = [
            run
            for run in selected
            if run.get("harness", {}).get("runner") in harness_set
            or run.get("harness", {}).get("id") in harness_set
        ]
    if limit is not None:
        selected = selected[:limit]
    return selected


def _materialize_one_run(
    *,
    bare_repo: Path,
    run: dict[str, Any],
    output_dir: Path,
    overwrite: bool,
) -> dict[str, Any]:
    run_root = output_dir / run["output_paths"]["root"]
    workspace_path = run_root / "workspace"

    if run_root.exists():
        if not overwrite:
            return {
                "run_id": run["run_id"],
                "status": "SKIPPED",
                "reason": f"Run root already exists: {run_root}",
                "run_root": str(run_root),
            }
        shutil.rmtree(run_root)

    base_commit_sha = run["workspace"]["base_commit_sha"]
    if not verify_commit_exists(bare_repo, base_commit_sha):
        return {
            "run_id": run["run_id"],
            "status": "FAIL",
            "reason": f"Base commit {base_commit_sha} is not reachable in {bare_repo}",
            "run_root": str(run_root),
        }

    try:
        cleanup_worktree(bare_repo, workspace_path)
        create_worktree(bare_repo, base_commit_sha, workspace_path)
        sanitize_worktree(workspace_path, base_commit_sha)
        run_root.mkdir(parents=True, exist_ok=True)
        (run_root / "logs").mkdir(parents=True, exist_ok=True)
        _write_issue_prompt(run_root / "issue_prompt.md", run)

        stage4_result = _apply_stage4(run_root, workspace_path, run)
        metadata = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "run_id": run["run_id"],
            "repo": run["repo"],
            "candidate_id": run["candidate_id"],
            "pr_number": run.get("pr_number"),
            "condition": run["condition"],
            "replication": run["replication"],
            "harness": run["harness"],
            "workspace": {
                **run["workspace"],
                "path": str(workspace_path),
            },
            "oracle": run.get("oracle", {}),
            "task_prompt": run.get("task_prompt", {}),
            "stage4_plan": run.get("stage4_plan", {}),
            "stage4_result": stage4_result,
        }
        with open(run_root / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        return {
            "run_id": run["run_id"],
            "status": "PASS",
            "condition": run["condition"],
            "run_root": str(run_root),
            "workspace": str(workspace_path),
            "stage4_result": stage4_result,
        }
    except Exception as exc:
        return {
            "run_id": run["run_id"],
            "status": "FAIL",
            "condition": run["condition"],
            "run_root": str(run_root),
            "reason": f"{type(exc).__name__}: {exc}",
        }


def _apply_stage4(run_root: Path, workspace_path: Path, run: dict[str, Any]) -> dict[str, Any]:
    condition = run["condition"]
    targets = run.get("stage4_plan", {}).get("targets")

    try:
        return apply_stage4_condition(workspace_path, condition, targets)
    except RuntimeError as exc:
        if condition not in {"type_hints", "naming"}:
            raise
        return _run_child_stage4_apply(
            run_root=run_root,
            workspace_path=workspace_path,
            condition=condition,
            targets=targets,
            reason=str(exc),
        )


def _run_child_stage4_apply(
    *,
    run_root: Path,
    workspace_path: Path,
    condition: str,
    targets: dict[str, Any] | None,
    reason: str,
) -> dict[str, Any]:
    if shutil.which("uv") is None:
        raise RuntimeError(
            f"{reason} Also could not find 'uv' for fallback environment bootstrapping."
        )

    dependency = "libcst" if condition == "type_hints" else "rope"
    child_script = Path(__file__).resolve().parent / "stage4_apply.py"
    targets_path = run_root / ".stage4_targets.json"
    output_path = run_root / ".stage4_result.json"
    with open(targets_path, "w") as f:
        json.dump(targets, f)

    command = [
        "uv",
        "run",
        "--with",
        dependency,
        "python",
        str(child_script),
        "--workspace",
        str(workspace_path),
        "--condition",
        condition,
        "--targets-file",
        str(targets_path),
        "--output",
        str(output_path),
    ]
    env = os.environ.copy()
    env.setdefault("UV_CACHE_DIR", "/tmp/llmj-uv-cache")
    try:
        subprocess.run(command, check=True, capture_output=True, text=True, env=env)
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        stdout = (exc.stdout or "").strip()
        detail = stderr or stdout or str(exc)
        raise RuntimeError(
            f"uv fallback failed for {condition}: {detail}"
        ) from exc
    with open(output_path) as f:
        result = json.load(f)
    result["fallback_runner"] = "uv"
    return result


def _write_issue_prompt(path: Path, run: dict[str, Any]) -> None:
    task_prompt = run.get("task_prompt", {})
    title = (task_prompt.get("title") or "Untitled historical task").strip()
    description = (task_prompt.get("description") or "").strip()
    fail_to_pass = run.get("oracle", {}).get("fail_to_pass_tests", [])

    lines = [f"# {title}", ""]
    if description:
        lines.extend([description, ""])
    if fail_to_pass:
        lines.append("## FAIL_TO_PASS Tests")
        lines.extend(f"- `{test_name}`" for test_name in fail_to_pass)
        lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _render_materialization_markdown(summary: dict[str, Any]) -> str:
    lines = [
        f"# Stage 4 Materialization: {summary['repo']}",
        "",
        "## Summary",
        f"- Selected runs: {summary['selection']['selected_runs']}",
        f"- Materialized: {summary['summary']['materialized']}",
        f"- Skipped: {summary['summary']['skipped']}",
        f"- Failed: {summary['summary']['failed']}",
        "",
        "## Run Results",
    ]
    for result in summary["results"]:
        detail = result.get("reason") or result.get("condition") or "ok"
        lines.append(f"- `{result['run_id']}`: `{result['status']}` ({detail})")
    return "\n".join(lines) + "\n"
