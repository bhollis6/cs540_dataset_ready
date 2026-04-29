"""Build Stage 5 run-plan artifacts from verified manifests and review packets."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_CONDITIONS = (
    "clean",
    "type_hints",
    "naming",
    "comments_docstrings",
    "remove_tests",
)

HARNESS_SPECS: dict[str, dict[str, str]] = {
    "claude-code": {
        "id": "claude_code",
        "family": "claude",
        "runner": "claude-code",
        "access_mode": "subscription_cli",
        "model_strategy": "subscription_default",
        "reason": "Frontier Claude agent runs using the user's Max subscription.",
    },
    "codex-cli": {
        "id": "codex_cli",
        "family": "codex",
        "runner": "codex-cli",
        "access_mode": "subscription_cli",
        "model_strategy": "subscription_default",
        "reason": "Frontier Codex agent runs using the user's subscription access.",
    },
}


def build_repo_run_plan(
    *,
    repo: str,
    deep_results_dir: Path,
    packet_dir: Path,
    candidates_dir: Path,
    output_dir: Path,
    harnesses: list[str] | None = None,
    replications: int = 3,
) -> Path:
    """Create a Stage 5 run-plan artifact for one repo."""
    output_dir.mkdir(parents=True, exist_ok=True)
    repo_short = repo.split("/")[-1]
    selected_harnesses = harnesses or ["claude-code", "codex-cli"]
    _validate_harnesses(selected_harnesses)
    if replications < 1:
        raise ValueError("replications must be at least 1")

    verified_path = deep_results_dir / f"{repo_short}_verified_manifest.json"
    packet_path = packet_dir / f"{repo_short}_experiment_packet.json"
    verified = _load_json(verified_path)
    packet = _load_json(packet_path)

    plan_status = _summarize_plan_status(verified, packet)
    task_catalog = _build_task_catalog(verified, candidates_dir, plan_status["warnings"])
    runs = _build_runs(
        repo=repo,
        repo_short=repo_short,
        tasks=task_catalog,
        harnesses=selected_harnesses,
        replications=replications,
        runnable=plan_status["runnable"],
    )

    harness_specs = [HARNESS_SPECS[name] for name in selected_harnesses]
    plan = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo": repo,
        "repo_short": repo_short,
        "artifacts": {
            "verified_manifest": _artifact_ref(verified_path, verified),
            "experiment_packet": _artifact_ref(packet_path, packet),
            "candidates_dir": {
                "path": str(candidates_dir),
                "exists": candidates_dir.exists(),
            },
        },
        "stage5_status": plan_status,
        "run_policy": {
            "conditions": list(DEFAULT_CONDITIONS),
            "replications": replications,
            "harnesses": harness_specs,
            "comparison_design": (
                "Run each verified historical task across the clean condition and each "
                "single-degradation condition for both Claude and Codex harnesses."
            ),
        },
        "run_layout": {
            "root_template": "runs/{repo_short}/{candidate_id}/{harness_id}/{condition}/rep_{replication}/",
            "expected_files": {
                "metadata": "metadata.json",
                "task_prompt": "issue_prompt.md",
                "workspace": "workspace/",
                "logs": "logs/",
                "result": "result.json",
                "metrics": "metrics.json",
            },
        },
        "metrics_contract": {
            "bootstrap": [
                "tokens_before_first_edit",
                "files_opened_before_first_edit",
                "dead_end_file_opens",
                "relevant_files_opened",
                "exploration_efficiency",
                "time_to_first_edit_seconds",
            ],
            "execution": [
                "task_success",
                "total_tokens",
                "total_cost_usd",
                "edits_applied",
                "test_commands_run",
                "completion_reason",
            ],
            "artifacts": [
                "agent_log",
                "applied_patch",
                "post_run_test_output",
                "final_repo_diff",
            ],
        },
        "task_catalog": task_catalog,
        "summary": {
            "verified_task_count": len(task_catalog),
            "conditions_per_task": len(DEFAULT_CONDITIONS),
            "harness_count": len(harness_specs),
            "replications": replications,
            "planned_runs": len(runs),
        },
        "runs": runs,
    }

    output_path = output_dir / f"{repo_short}_run_plan.json"
    with open(output_path, "w") as f:
        json.dump(plan, f, indent=2)
    markdown_path = output_dir / f"{repo_short}_run_plan.md"
    markdown_path.write_text(_render_run_plan_markdown(plan), encoding="utf-8")
    return output_path


def _validate_harnesses(harnesses: list[str]) -> None:
    unknown = [name for name in harnesses if name not in HARNESS_SPECS]
    if unknown:
        raise ValueError(f"Unsupported harnesses: {', '.join(sorted(unknown))}")


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def _artifact_ref(path: Path, payload: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": payload is not None,
    }


def _summarize_plan_status(
    verified: dict[str, Any] | None,
    packet: dict[str, Any] | None,
) -> dict[str, Any]:
    warnings: list[str] = []
    if verified is None:
        return {
            "status": "BLOCKED",
            "reason": "No verified Stage 2 manifest exists for this repo.",
            "packet_decision": packet.get("suggested_decision", {}).get("status") if packet else None,
            "runnable": False,
            "warnings": warnings,
        }

    verified_count = len(verified.get("verified_prs", []))
    if verified_count == 0:
        return {
            "status": "BLOCKED",
            "reason": "Stage 2 has zero verified tasks, so no Stage 5 runs should be scheduled.",
            "packet_decision": packet.get("suggested_decision", {}).get("status") if packet else None,
            "runnable": False,
            "warnings": warnings,
        }

    if packet is None:
        warnings.append("No experiment packet found; Stage 5 planning should still receive human review.")
        return {
            "status": "REVIEW_REQUIRED",
            "reason": "Verified tasks exist, but no repo admission packet was found.",
            "packet_decision": None,
            "runnable": True,
            "warnings": warnings,
        }

    decision = packet.get("suggested_decision", {}).get("status")
    reason = packet.get("suggested_decision", {}).get("reason", "Packet review is incomplete.")
    if decision == "NO_GO":
        return {
            "status": "BLOCKED",
            "reason": f"Repo packet is NO_GO: {reason}",
            "packet_decision": decision,
            "runnable": False,
            "warnings": warnings,
        }
    if decision == "REVIEW":
        warnings.append("Packet decision is REVIEW; human approval should happen before live runs.")
        return {
            "status": "REVIEW_REQUIRED",
            "reason": f"Repo packet still needs guided human approval: {reason}",
            "packet_decision": decision,
            "runnable": True,
            "warnings": warnings,
        }
    return {
        "status": "READY",
        "reason": "Verified tasks and repo packet are ready for Stage 5 run scheduling.",
        "packet_decision": decision,
        "runnable": True,
        "warnings": warnings,
    }


def _build_task_catalog(
    verified: dict[str, Any] | None,
    candidates_dir: Path,
    warnings: list[str],
) -> list[dict[str, Any]]:
    if verified is None:
        return []

    catalog: list[dict[str, Any]] = []
    for task in verified.get("verified_prs", []):
        candidate_path = candidates_dir / f"{task['candidate_id']}.json"
        candidate = _load_json(candidate_path)
        if candidate is None:
            warnings.append(
                f"Candidate metadata missing for {task['candidate_id']}; run plan will lack issue text."
            )

        catalog.append({
            "candidate_id": task["candidate_id"],
            "pr_number": task.get("pr_number"),
            "base_commit_sha": task.get("base_commit_sha"),
            "env_commit_sha": task.get("env_commit_sha", task.get("base_commit_sha")),
            "merge_commit_sha": task.get("merge_commit_sha"),
            "head_commit_sha": task.get("head_commit_sha"),
            "stage1_score": task.get("stage1_score"),
            "stage2_score": task.get("stage2_score"),
            "navigation_depth": task.get("navigation_depth"),
            "task_prompt": {
                "title": candidate.get("title") if candidate else None,
                "description": candidate.get("description") if candidate else None,
                "source_candidate_path": str(candidate_path),
            },
            "oracle": {
                "fail_to_pass_tests": task.get("fail_to_pass_tests", []),
                "pass_to_pass_tests": task.get("pass_to_pass_tests", []),
            },
            "degradation_targets": task.get("degradation_targets", {}),
        })
    return catalog


def _build_runs(
    *,
    repo: str,
    repo_short: str,
    tasks: list[dict[str, Any]],
    harnesses: list[str],
    replications: int,
    runnable: bool,
) -> list[dict[str, Any]]:
    if not runnable:
        return []

    runs: list[dict[str, Any]] = []
    for task in tasks:
        for harness_name in harnesses:
            harness = HARNESS_SPECS[harness_name]
            for condition in DEFAULT_CONDITIONS:
                for replication in range(1, replications + 1):
                    relative_root = (
                        f"runs/{repo_short}/{task['candidate_id']}/"
                        f"{harness['id']}/{condition}/rep_{replication}"
                    )
                    runs.append({
                        "run_id": (
                            f"{repo_short}__{task['candidate_id']}__"
                            f"{harness['id']}__{condition}__rep{replication}"
                        ),
                        "repo": repo,
                        "candidate_id": task["candidate_id"],
                        "pr_number": task["pr_number"],
                        "condition": condition,
                        "replication": replication,
                        "harness": harness,
                        "workspace": {
                            "base_commit_sha": task["base_commit_sha"],
                            "env_commit_sha": task.get("env_commit_sha", task["base_commit_sha"]),
                            "merge_commit_sha": task["merge_commit_sha"],
                            "head_commit_sha": task["head_commit_sha"],
                        },
                        "task_prompt": task["task_prompt"],
                        "oracle": task["oracle"],
                        "stage4_plan": _condition_stage4_plan(task["degradation_targets"], condition),
                        "output_paths": {
                            "root": relative_root,
                            "metadata": f"{relative_root}/metadata.json",
                            "task_prompt": f"{relative_root}/issue_prompt.md",
                            "workspace": f"{relative_root}/workspace",
                            "logs": f"{relative_root}/logs",
                            "result": f"{relative_root}/result.json",
                            "metrics": f"{relative_root}/metrics.json",
                        },
                    })
    return runs


def _condition_stage4_plan(
    degradation_targets: dict[str, Any],
    condition: str,
) -> dict[str, Any]:
    if condition == "clean":
        return {
            "mode": "clean",
            "degradation": None,
            "targets": None,
        }
    return {
        "mode": "degraded",
        "degradation": condition,
        "targets": degradation_targets.get(condition),
    }


def _render_run_plan_markdown(plan: dict[str, Any]) -> str:
    stage5 = plan["stage5_status"]
    summary = plan["summary"]
    lines = [
        f"# Run Plan: {plan['repo']}",
        "",
        "## Status",
        f"- Stage 5 status: `{stage5['status']}`",
        f"- Reason: {stage5['reason']}",
        f"- Packet decision: `{stage5.get('packet_decision')}`",
        "",
        "## Summary",
        f"- Verified tasks: {summary['verified_task_count']}",
        f"- Conditions per task: {summary['conditions_per_task']}",
        f"- Harnesses: {summary['harness_count']}",
        f"- Replications: {summary['replications']}",
        f"- Planned runs: {summary['planned_runs']}",
        "",
        "## Harnesses",
    ]
    for harness in plan["run_policy"]["harnesses"]:
        lines.append(
            f"- `{harness['id']}` ({harness['runner']}): {harness['reason']}"
        )

    lines.extend([
        "",
        "## Conditions",
    ])
    for condition in plan["run_policy"]["conditions"]:
        lines.append(f"- `{condition}`")

    if stage5["warnings"]:
        lines.extend([
            "",
            "## Warnings",
        ])
        for warning in stage5["warnings"]:
            lines.append(f"- {warning}")

    lines.extend([
        "",
        "## Layout",
        f"- Root template: `{plan['run_layout']['root_template']}`",
    ])
    for label, path in plan["run_layout"]["expected_files"].items():
        lines.append(f"- `{label}` -> `{path}`")
    return "\n".join(lines) + "\n"
