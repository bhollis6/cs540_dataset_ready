"""Assemble a human-review experiment packet for a repo."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def build_repo_experiment_packet(
    *,
    repo: str,
    results_dir: Path,
    deep_results_dir: Path,
    readiness_dir: Path,
    naming_audit_dir: Path | None,
    output_dir: Path,
) -> Path:
    """Combine readiness, naming, and task manifests into one review packet."""
    output_dir.mkdir(parents=True, exist_ok=True)
    repo_short = repo.split("/")[-1]

    selected_path = results_dir / f"{repo_short}_selected_prs.json"
    verified_path = deep_results_dir / f"{repo_short}_verified_manifest.json"
    readiness_path = readiness_dir / f"{repo_short}_repo_readiness.json"
    naming_dir = naming_audit_dir if naming_audit_dir is not None else readiness_dir
    naming_path = naming_dir / f"{repo_short}_naming_readiness.json"

    selected = _load_json(selected_path)
    verified = _load_json(verified_path)
    readiness = _load_json(readiness_path)
    naming = _load_json(naming_path)

    packet = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo": repo,
        "repo_short": repo_short,
        "artifacts": {
            "selected_manifest": _artifact_ref(selected_path, selected),
            "verified_manifest": _artifact_ref(verified_path, verified),
            "repo_readiness": _artifact_ref(readiness_path, readiness),
            "naming_readiness": _artifact_ref(naming_path, naming),
        },
        "summary": {
            "stage1": _summarize_stage1(selected),
            "stage2": _summarize_stage2(verified),
            "repo_readiness": _summarize_repo_readiness(readiness),
            "naming_audit": _summarize_naming_audit(naming),
        },
    }
    packet["admission_rubric"] = _build_admission_rubric(packet["summary"])
    packet["review_checks"] = _build_review_checks(packet["summary"], packet["admission_rubric"])
    packet["suggested_decision"] = _suggest_decision(packet["admission_rubric"])

    output_path = output_dir / f"{repo_short}_experiment_packet.json"
    with open(output_path, "w") as f:
        json.dump(packet, f, indent=2)
    markdown_path = output_dir / f"{repo_short}_experiment_packet.md"
    markdown_path.write_text(_render_packet_markdown(packet), encoding="utf-8")
    return output_path


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


def _summarize_stage1(selected: dict[str, Any] | None) -> dict[str, Any]:
    if selected is None:
        return {"status": "MISSING", "reason": "No Stage 1 selected manifest found."}

    selected_prs = selected.get("selected_prs", [])
    top_candidates = [entry.get("candidate_id") for entry in selected_prs[:5]]
    if selected.get("accepted", 0) == 0:
        return {
            "status": "FAIL",
            "reason": "Stage 1 did not accept any PRs for this repo.",
            "accepted": 0,
            "total_candidates": selected.get("total_candidates", 0),
            "top_candidates": [],
        }

    return {
        "status": "PASS",
        "reason": "Stage 1 selected candidate PRs for deeper evaluation.",
        "accepted": selected.get("accepted", 0),
        "review": selected.get("review", 0),
        "rejected": selected.get("rejected", 0),
        "total_candidates": selected.get("total_candidates", 0),
        "top_candidates": top_candidates,
    }


def _summarize_stage2(verified: dict[str, Any] | None) -> dict[str, Any]:
    if verified is None:
        return {"status": "MISSING", "reason": "No Stage 2 verified manifest found."}

    verified_prs = verified.get("verified_prs", [])
    top_verified = [entry.get("candidate_id") for entry in verified_prs[:5]]
    if verified.get("stage2_accepted", 0) == 0:
        return {
            "status": "REVIEW",
            "reason": "Stage 2 produced no verified tasks for downstream experiments.",
            "verified_count": 0,
            "preflight_passed": verified.get("preflight_passed", 0),
            "llm_stage2_accepted": verified.get("llm_stage2_accepted", 0),
            "navigation_depth_threshold": verified.get("navigation_depth_threshold"),
            "top_verified": [],
        }

    return {
        "status": "PASS",
        "reason": "Stage 2 produced verified tasks for downstream experiments.",
        "verified_count": verified.get("stage2_accepted", 0),
        "preflight_passed": verified.get("preflight_passed", 0),
        "llm_stage2_accepted": verified.get("llm_stage2_accepted", 0),
        "navigation_depth_threshold": verified.get("navigation_depth_threshold"),
        "top_verified": top_verified,
    }


def _summarize_repo_readiness(readiness: dict[str, Any] | None) -> dict[str, Any]:
    if readiness is None:
        return {"status": "MISSING", "reason": "No repo readiness report found."}

    audit = readiness.get("audit", {})
    overall = audit.get("overall", {})
    return {
        "status": overall.get("status", "REVIEW"),
        "reason": overall.get("reason", "Repo readiness needs review."),
        "condition_statuses": audit.get("readiness", {}),
    }


def _summarize_naming_audit(naming: dict[str, Any] | None) -> dict[str, Any]:
    if naming is None:
        return {"status": "MISSING", "reason": "No naming readiness report found."}

    audit = naming.get("audit", {})
    dry_run = audit.get("dry_run", {})
    live_run = audit.get("live_run")
    if live_run is None:
        return {
            "status": "REVIEW",
            "reason": "Only dry-run naming data is available; run a live audit before experiments.",
            "candidate_symbol_count": dry_run.get("candidate_symbol_count", 0),
            "files_with_renames": dry_run.get("files_with_renames", 0),
        }

    rates = live_run.get("rates", {})
    success_rate = rates.get("rename_success_rate", 0.0)
    refactoring_error_rate = rates.get("refactoring_error_rate", 0.0)
    offset_rate = rates.get("offset_not_found_rate", 0.0)
    status = "PASS"
    reason = "Live naming audit looks viable."
    if success_rate < 0.70 or refactoring_error_rate > 0.25 or offset_rate > 0.15:
        status = "REVIEW"
        reason = "Live naming audit needs human review before experiments."

    return {
        "status": status,
        "reason": reason,
        "candidate_symbol_count": dry_run.get("candidate_symbol_count", 0),
        "files_with_renames": dry_run.get("files_with_renames", 0),
        "live_rates": rates,
        "top_skipped_names": live_run.get("top_skipped_names", []),
    }


def _build_admission_rubric(summary: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    stage1 = summary["stage1"]
    stage2 = summary["stage2"]
    repo_readiness = summary["repo_readiness"]
    naming_audit = summary["naming_audit"]

    criteria = [
        {
            "id": "repo_static_surface",
            "title": "Repo Static Surface",
            "gate": "hard",
            "status": _normalize_status(repo_readiness["status"]),
            "reason": repo_readiness["reason"],
            "evidence": {
                "condition_statuses": repo_readiness.get("condition_statuses", {}),
            },
            "review_prompt": (
                "Do all degradation conditions have enough surface area, or is one condition "
                "too weak to support a meaningful clean-vs-degraded comparison?"
            ),
        },
        {
            "id": "stage1_task_pool",
            "title": "Stage 1 Task Pool",
            "gate": "soft",
            "status": _stage1_pool_status(stage1),
            "reason": _stage1_pool_reason(stage1),
            "evidence": {
                "accepted": stage1.get("accepted", 0),
                "total_candidates": stage1.get("total_candidates", 0),
                "top_candidates": stage1.get("top_candidates", []),
            },
            "review_prompt": (
                "Does the repo have enough strong candidate PRs to justify deeper evaluation, "
                "or is the pool too shallow to support 3-5 good tasks?"
            ),
        },
        {
            "id": "stage2_verified_tasks",
            "title": "Stage 2 Verified Tasks",
            "gate": "hard",
            "status": _stage2_verified_status(stage2),
            "reason": _stage2_verified_reason(stage2),
            "evidence": {
                "verified_count": stage2.get("verified_count", 0),
                "preflight_passed": stage2.get("preflight_passed", 0),
                "llm_stage2_accepted": stage2.get("llm_stage2_accepted", 0),
                "top_verified": stage2.get("top_verified", []),
            },
            "review_prompt": (
                "Are there enough historically validated tasks to support experiments, or does "
                "Stage 2 need to be rerun/tuned before this repo should move forward?"
            ),
        },
        {
            "id": "naming_live_audit",
            "title": "Naming Live Audit",
            "gate": "hard",
            "status": _naming_gate_status(naming_audit),
            "reason": _naming_gate_reason(naming_audit),
            "evidence": {
                "candidate_symbol_count": naming_audit.get("candidate_symbol_count", 0),
                "files_with_renames": naming_audit.get("files_with_renames", 0),
                "live_rates": naming_audit.get("live_rates"),
                "top_skipped_names": naming_audit.get("top_skipped_names", []),
            },
            "review_prompt": (
                "Does the naming degradation look strong and safe enough on this repo, or do "
                "the live rename skips still need investigation before approval?"
            ),
        },
    ]
    return criteria


def _build_review_checks(
    summary: dict[str, dict[str, Any]],
    rubric: list[dict[str, Any]],
) -> list[str]:
    checks: list[str] = []
    for criterion in rubric:
        if criterion["status"] in {"REVIEW", "FAIL", "MISSING"}:
            checks.append(criterion["review_prompt"])
    if not checks:
        checks.append("Repo is ready for human approval and downstream experiment setup.")
    return checks


def _suggest_decision(rubric: list[dict[str, Any]]) -> dict[str, str]:
    hard_fail = any(
        criterion["gate"] == "hard" and criterion["status"] == "FAIL"
        for criterion in rubric
    )
    hard_missing = any(
        criterion["gate"] == "hard" and criterion["status"] == "MISSING"
        for criterion in rubric
    )
    review_needed = any(
        criterion["status"] == "REVIEW"
        or criterion["status"] == "MISSING"
        for criterion in rubric
    )

    if hard_fail or hard_missing:
        return {
            "status": "NO_GO",
            "reason": "One or more hard-gate criteria failed or are missing.",
        }
    if review_needed:
        return {
            "status": "REVIEW",
            "reason": "Repo has useful artifacts, but still needs guided human review before Stage 4/Stage 5.",
        }
    return {
        "status": "GO",
        "reason": "Repo passed the current admission rubric for downstream runs.",
    }


def _normalize_status(status: str) -> str:
    if status in {"PASS", "REVIEW", "FAIL", "MISSING"}:
        return status
    return "REVIEW"


def _stage1_pool_status(stage1: dict[str, Any]) -> str:
    status = stage1.get("status", "MISSING")
    if status in {"FAIL", "MISSING"}:
        return status
    accepted = stage1.get("accepted", 0)
    if accepted >= 3:
        return "PASS"
    return "REVIEW"


def _stage1_pool_reason(stage1: dict[str, Any]) -> str:
    status = stage1.get("status", "MISSING")
    if status in {"FAIL", "MISSING"}:
        return stage1["reason"]
    accepted = stage1.get("accepted", 0)
    if accepted >= 3:
        return "Stage 1 produced enough accepted candidates to target a 3-5 task shortlist."
    return "Stage 1 produced some candidates, but the pool is smaller than the target 3-5 tasks."


def _stage2_verified_status(stage2: dict[str, Any]) -> str:
    status = stage2.get("status", "MISSING")
    if status == "MISSING":
        return "MISSING"
    verified_count = stage2.get("verified_count", 0)
    if verified_count >= 3:
        return "PASS"
    if verified_count >= 1:
        return "REVIEW"
    return "FAIL"


def _stage2_verified_reason(stage2: dict[str, Any]) -> str:
    status = stage2.get("status", "MISSING")
    if status == "MISSING":
        return stage2["reason"]
    verified_count = stage2.get("verified_count", 0)
    if verified_count >= 3:
        return "Stage 2 produced enough verified tasks for downstream experiments."
    if verified_count >= 1:
        return "Stage 2 produced some verified tasks, but fewer than the target 3-5 task set."
    return "Stage 2 produced zero verified tasks, so the repo is not ready for downstream experiments."


def _naming_gate_status(naming_audit: dict[str, Any]) -> str:
    status = naming_audit.get("status", "MISSING")
    if status == "MISSING":
        return "MISSING"
    if naming_audit.get("live_rates") is None:
        return "REVIEW"
    if status == "PASS":
        return "PASS"
    return "FAIL" if status == "FAIL" else "REVIEW"


def _naming_gate_reason(naming_audit: dict[str, Any]) -> str:
    if naming_audit.get("status") == "MISSING":
        return naming_audit["reason"]
    if naming_audit.get("live_rates") is None:
        return "Only dry-run naming data is available; a live audit is required before approval."
    return naming_audit["reason"]


def _render_packet_markdown(packet: dict[str, Any]) -> str:
    summary = packet["summary"]
    lines = [
        f"# Experiment Packet: {packet['repo']}",
        "",
        "## Decision",
        "",
        f"- Status: `{packet['suggested_decision']['status']}`",
        f"- Reason: {packet['suggested_decision']['reason']}",
        "",
        "## Admission Rubric",
        "",
        "| Criterion | Gate | Status | Reason |",
        "|---|---|---|---|",
    ]
    for criterion in packet["admission_rubric"]:
        lines.append(
            f"| {criterion['title']} | {criterion['gate']} | "
            f"`{criterion['status']}` | {criterion['reason']} |"
        )

    lines.extend([
        "",
        "## Review Checks",
        "",
    ])
    for check in packet["review_checks"]:
        lines.append(f"- {check}")

    lines.extend([
        "",
        "## Summary",
        "",
        f"- Stage 1: `{summary['stage1']['status']}` — {summary['stage1']['reason']}",
        f"- Stage 2: `{summary['stage2']['status']}` — {summary['stage2']['reason']}",
        f"- Repo readiness: `{summary['repo_readiness']['status']}` — {summary['repo_readiness']['reason']}",
        f"- Naming audit: `{summary['naming_audit']['status']}` — {summary['naming_audit']['reason']}",
        "",
        "## Artifacts",
        "",
    ])
    for name, artifact in packet["artifacts"].items():
        exists = "yes" if artifact["exists"] else "no"
        lines.append(f"- `{name}`: exists={exists} path=`{artifact['path']}`")

    return "\n".join(lines) + "\n"
