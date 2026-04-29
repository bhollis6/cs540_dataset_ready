"""Container-first Stage 2 runtime comparison and admission helpers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def resolve_stage2_runtime_artifact_paths(
    *,
    repo: str,
    host_probe_root: Path | None,
    container_bundle_root: Path | None,
) -> dict[str, Path | None]:
    """Resolve the expected raw artifact paths for Stage 2 runtime evidence."""
    repo_short = repo.split("/")[-1]
    return {
        "host_probe_report": (
            host_probe_root / repo_short / f"{repo_short}_stage2_probe.json"
            if host_probe_root is not None else None
        ),
        "container_bundle_report": (
            container_bundle_root / f"{repo_short}_stage2_container_bundles.json"
            if container_bundle_root is not None else None
        ),
    }


def summarize_stage2_runtime(
    *,
    repo: str,
    host_probe_root: Path | None,
    container_bundle_root: Path | None,
) -> dict[str, Any]:
    """Summarize host-vs-container Stage 2 runtime evidence for repo admission."""
    artifact_paths = resolve_stage2_runtime_artifact_paths(
        repo=repo,
        host_probe_root=host_probe_root,
        container_bundle_root=container_bundle_root,
    )
    host_report = _load_json(artifact_paths["host_probe_report"])
    container_report = _load_json(artifact_paths["container_bundle_report"])

    host_summary = _summarize_host_probe(artifact_paths["host_probe_report"], host_report)
    container_summary = _summarize_container_probe(
        artifact_paths["container_bundle_report"],
        container_report,
    )

    status, reason, authority_source = _determine_runtime_authority(
        host_summary=host_summary,
        container_summary=container_summary,
    )

    return {
        "status": status,
        "reason": reason,
        "authority_source": authority_source,
        "host_probe_role": "fast_heuristic",
        "artifacts": {
            "host_probe_report": host_summary["artifact"],
            "container_bundle_report": container_summary["artifact"],
        },
        "host_probe": host_summary,
        "container_probe": container_summary,
        "compared_commits": _build_compared_commit_rows(
            host_results=host_summary.get("results", []),
            container_results=container_summary.get("bundles", []),
        ),
    }


def build_stage2_runtime_comparison_matrix(
    *,
    repos: list[str],
    host_probe_root: Path | None,
    container_bundle_root: Path | None,
    output_dir: Path,
) -> Path:
    """Write one cross-repo Stage 2 runtime comparison report."""
    output_dir.mkdir(parents=True, exist_ok=True)
    comparisons = [
        summarize_stage2_runtime(
            repo=repo,
            host_probe_root=host_probe_root,
            container_bundle_root=container_bundle_root,
        )
        for repo in repos
    ]

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "authority_policy": {
            "primary": "container_probe",
            "secondary": "host_probe",
            "host_probe_role": "fast_heuristic",
            "rules": [
                "container success is the repo-admission authority even if host probing fails",
                "container failure blocks repo admission until the profile/runtime path is fixed",
                "host success without container evidence is only REVIEW, not PASS",
            ],
        },
        "repos": [
            {
                "repo": repo,
                "repo_short": repo.split("/")[-1],
                **comparison,
            }
            for repo, comparison in zip(repos, comparisons, strict=True)
        ],
        "summary": {
            "repo_count": len(comparisons),
            "pass": sum(1 for comparison in comparisons if comparison["status"] == "PASS"),
            "review": sum(1 for comparison in comparisons if comparison["status"] == "REVIEW"),
            "fail": sum(1 for comparison in comparisons if comparison["status"] == "FAIL"),
            "missing": sum(1 for comparison in comparisons if comparison["status"] == "MISSING"),
        },
    }

    output_path = output_dir / "stage2_runtime_comparison_matrix.json"
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    markdown_path = output_dir / "stage2_runtime_comparison_matrix.md"
    markdown_path.write_text(_render_matrix_markdown(report), encoding="utf-8")
    return output_path


def _load_json(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def _summarize_host_probe(
    path: Path | None,
    payload: dict[str, Any] | None,
) -> dict[str, Any]:
    artifact = _artifact_ref(path, payload)
    if payload is None:
        return {
            "artifact": artifact,
            "overall_status": "MISSING",
            "reason": "No host Stage 2 probe report found.",
            "results": [],
        }

    results = payload.get("results", [])
    summarized_results = [
        {
            "commit_sha": result.get("commit_sha"),
            "status": result.get("status", "MISSING"),
            "reason": result.get("reason"),
            "install_success": result.get("install_success"),
            "probe_success": result.get("probe_success"),
            "elapsed_seconds": result.get("elapsed_seconds"),
            "failure_signature": _extract_failure_signature(result),
        }
        for result in results
    ]
    summary = payload.get("summary", {})
    return {
        "artifact": artifact,
        "execution_mode": payload.get("execution_mode"),
        "overall_status": summary.get("overall_status", "MISSING"),
        "reason": summary.get("reason", "Host Stage 2 probe report is incomplete."),
        "results": summarized_results,
        "probed_commits": summary.get("probed_commits", len(results)),
        "passed": summary.get("passed", 0),
        "failed": summary.get("failed", 0),
        "errored": summary.get("errored", 0),
    }


def _summarize_container_probe(
    path: Path | None,
    payload: dict[str, Any] | None,
) -> dict[str, Any]:
    artifact = _artifact_ref(path, payload)
    if payload is None:
        return {
            "artifact": artifact,
            "overall_status": "MISSING",
            "reason": "No Stage 2 container bundle report found.",
            "bundles": [],
        }

    bundle_results: list[dict[str, Any]] = []
    for bundle in payload.get("bundles", []):
        probe_result_path = _resolve_reported_path(path, bundle.get("default_probe_result"))
        probe_payload = _load_json(probe_result_path)
        install_status = probe_payload.get("install_status") if probe_payload else None
        probe_status = probe_payload.get("probe_status") if probe_payload else None
        bundle_results.append({
            "commit_sha": bundle.get("commit_sha"),
            "bundle_dir": bundle.get("bundle_dir"),
            "probe_result": _artifact_ref(probe_result_path, probe_payload),
            "install_status": install_status,
            "probe_status": probe_status,
            "probe_exit_code": probe_payload.get("probe_exit_code") if probe_payload else None,
            "probe_command": probe_payload.get("probe_command") if probe_payload else None,
            "started_at": probe_payload.get("started_at") if probe_payload else None,
            "finished_at": probe_payload.get("finished_at") if probe_payload else None,
            "status": _container_bundle_status(probe_payload),
            "reason": _container_bundle_reason(probe_payload),
        })

    passed = sum(1 for bundle in bundle_results if bundle["status"] == "PASS")
    failed = sum(1 for bundle in bundle_results if bundle["status"] == "FAIL")
    missing = sum(1 for bundle in bundle_results if bundle["status"] == "MISSING")

    if passed and failed == 0 and missing == 0:
        overall_status = "PASS"
        reason = "Container probe succeeded for all sampled commits."
    elif passed and failed == 0:
        overall_status = "REVIEW"
        reason = "Some container probe results are still missing even though at least one commit passed."
    elif failed:
        overall_status = "FAIL"
        reason = "At least one container probe failed; runtime viability is not yet proven on the container substrate."
    else:
        overall_status = "MISSING"
        reason = "Container bundles exist, but no probe_result.json evidence was found."

    return {
        "artifact": artifact,
        "overall_status": overall_status,
        "reason": reason,
        "bundles": bundle_results,
        "bundle_count": len(bundle_results),
        "passed": passed,
        "failed": failed,
        "missing": missing,
    }


def _artifact_ref(path: Path | None, payload: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "path": str(path) if path is not None else None,
        "exists": payload is not None,
    }


def _resolve_reported_path(report_path: Path | None, reported_path: str | None) -> Path | None:
    if reported_path is None:
        return None
    candidate = Path(reported_path)
    if candidate.is_absolute() or candidate.exists():
        return candidate
    if report_path is None:
        return candidate
    cwd_relative = report_path.parent.parent / candidate if len(report_path.parents) >= 2 else report_path.parent / candidate
    if cwd_relative.exists():
        return cwd_relative
    return candidate


def _extract_failure_signature(result: dict[str, Any]) -> str | None:
    output = result.get("install_output") or ""
    attempts = result.get("install_attempts") or []
    if not output and attempts:
        output = attempts[0].get("output") or ""
    for marker in (
        "hatch-fancy-pypi-readme",
        "hatch-vcs",
        "hatchling",
        "anyio.pytest_plugin",
        "pytest_benchmark.plugin",
        "_hypothesis_pytestplugin",
    ):
        if marker in output:
            return marker
    first_line = output.strip().splitlines()[0] if output.strip() else None
    return first_line or result.get("reason")


def _container_bundle_status(payload: dict[str, Any] | None) -> str:
    if payload is None:
        return "MISSING"
    if payload.get("install_status") == "success" and payload.get("probe_status") == "success":
        return "PASS"
    return "FAIL"


def _container_bundle_reason(payload: dict[str, Any] | None) -> str:
    if payload is None:
        return "Container probe result is missing."
    if payload.get("install_status") == "success" and payload.get("probe_status") == "success":
        return "Container probe completed successfully."
    return "Container probe did not reach a clean install+probe success result."


def _determine_runtime_authority(
    *,
    host_summary: dict[str, Any],
    container_summary: dict[str, Any],
) -> tuple[str, str, str]:
    container_status = container_summary["overall_status"]
    host_status = host_summary["overall_status"]

    if container_status == "PASS":
        if host_status == "PASS":
            return (
                "PASS",
                "Container probe succeeded and host probing agrees; repo is runtime-admissible for Stage 2.",
                "container_probe",
            )
        if host_status in {"FAIL", "REVIEW"}:
            return (
                "PASS",
                "Container probe succeeded; host probe remains heuristic-only and does not block repo admission.",
                "container_probe",
            )
        return (
            "PASS",
            "Container probe succeeded; repo admission now keys off container evidence first.",
            "container_probe",
        )

    if container_status == "FAIL":
        return (
            "FAIL",
            "Container probe failed; repo is not runtime-admissible until the profile/container path is fixed.",
            "container_probe",
        )

    if host_status == "PASS":
        return (
            "REVIEW",
            "Host probe passed, but container-backed Stage 2 evidence is still missing.",
            "host_probe_only",
        )

    if host_status in {"FAIL", "REVIEW"}:
        return (
            "MISSING",
            "Container-backed Stage 2 evidence is missing, and the host heuristic did not establish viability.",
            "none",
        )

    return (
        "MISSING",
        "No Stage 2 runtime evidence was found for this repo.",
        "none",
    )


def _build_compared_commit_rows(
    *,
    host_results: list[dict[str, Any]],
    container_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    host_by_commit = {
        result.get("commit_sha"): result
        for result in host_results
        if result.get("commit_sha")
    }
    rows: list[dict[str, Any]] = []
    for bundle in container_results:
        commit_sha = bundle.get("commit_sha")
        host_result = host_by_commit.get(commit_sha)
        rows.append({
            "commit_sha": commit_sha,
            "host_status": host_result.get("status") if host_result else "MISSING",
            "host_reason": host_result.get("reason") if host_result else "No matching host probe result found.",
            "host_failure_signature": (
                host_result.get("failure_signature") if host_result else None
            ),
            "container_status": bundle.get("status", "MISSING"),
            "container_reason": bundle.get("reason"),
        })
    return rows


def _render_matrix_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Stage 2 Runtime Comparison Matrix",
        "",
        "## Authority Policy",
        "",
        "- Primary authority: `container_probe`",
        "- Secondary heuristic: `host_probe`",
        "- Host probe role: fast heuristic only; it does not veto a successful container probe.",
        "",
        "## Repo Comparison",
        "",
        "| Repo | Admission Status | Container | Host | Reason |",
        "|---|---|---|---|---|",
    ]
    for entry in report["repos"]:
        lines.append(
            f"| {entry['repo']} | `{entry['status']}` | "
            f"`{entry['container_probe']['overall_status']}` | "
            f"`{entry['host_probe']['overall_status']}` | {entry['reason']} |"
        )

    lines.extend([
        "",
        "## Commit Notes",
        "",
    ])
    for entry in report["repos"]:
        lines.append(f"### {entry['repo']}")
        lines.append("")
        for row in entry["compared_commits"]:
            host_detail = row["host_failure_signature"] or row["host_reason"]
            lines.append(
                f"- `{row['commit_sha'][:12]}`: host=`{row['host_status']}` "
                f"({host_detail}); container=`{row['container_status']}`"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
