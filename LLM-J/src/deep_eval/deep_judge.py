"""Stage 2 deep evaluation orchestrator."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from src.deep_eval.context_extractor import collect_context_files
from src.deep_eval.models import (
    ContextStats,
    DeepEvaluationResult,
    DeepJudgeResponse,
    PreflightResult,
)
from src.deep_eval.preflight import run_preflight
from src.deep_eval.prompts import DEEP_SYSTEM_PROMPT, build_deep_user_prompt
from src.deep_eval.repo_manager import (
    cleanup_worktree,
    create_worktree,
    ensure_clone,
    sanitize_worktree,
    verify_commit_exists,
)
from src.output.degradation_plan import build_stage4_handoff, load_candidate_handoff
from src.providers.base import get_provider

if TYPE_CHECKING:
    from src.config import Config


def deep_evaluate_repo(
    repo: str,
    accepted_prs: list[dict],
    candidates_dir: Path,
    config: Config,
) -> list[DeepEvaluationResult]:
    """Run Stage 2 deep evaluation on accepted PRs for a single repo.

    accepted_prs: list of dicts from the Stage 1 manifest's selected_prs.
    """
    clones_dir = getattr(config, "clones_dir", Path("clones"))
    skip_preflight = getattr(config, "skip_preflight", False)
    preflight_only = getattr(config, "preflight_only", False)
    context_budget = getattr(config, "context_budget_chars", None)

    # Clone the repo
    bare_repo = ensure_clone(repo, clones_dir)

    # Set up LLM provider (only if not preflight-only)
    provider = None
    if not preflight_only:
        provider = get_provider(config.provider, config.model, config.api_key)

    results: list[DeepEvaluationResult] = []
    worktrees_dir = clones_dir / "worktrees"

    for i, pr_data in enumerate(accepted_prs, 1):
        candidate_id = pr_data["candidate_id"]
        pr_number = pr_data["pr_number"]
        base_sha = pr_data.get("base_commit_sha")
        stage1_score = pr_data.get("total_score", 0)

        print(f"\n  [{i}/{len(accepted_prs)}] {candidate_id}")

        # Load full candidate JSON for diffs
        candidate_file = candidates_dir / f"{candidate_id}.json"
        if not candidate_file.exists():
            print("    SKIP: candidate file not found")
            continue

        with open(candidate_file) as f:
            candidate = json.load(f)

        # Verify base commit exists
        if not base_sha or not verify_commit_exists(bare_repo, base_sha):
            print("    SKIP: base_commit_sha not reachable")
            results.append(DeepEvaluationResult(
                candidate_id=candidate_id, repo=repo, pr_number=pr_number,
                preflight=PreflightResult(candidate_id, "FAIL", "base_commit_sha not reachable"),
                judge_response=None, context_stats=ContextStats(),
                stage1_score=stage1_score,
                evaluated_at=datetime.now(timezone.utc).isoformat(),
            ))
            continue

        # Create worktree at base commit
        worktree = worktrees_dir / f"{candidate_id}"
        try:
            create_worktree(bare_repo, base_sha, worktree)
            sanitize_worktree(worktree, base_sha)
        except Exception as e:
            print(f"    SKIP: worktree creation failed: {e}")
            results.append(DeepEvaluationResult(
                candidate_id=candidate_id, repo=repo, pr_number=pr_number,
                preflight=PreflightResult(candidate_id, "ERROR", f"worktree failed: {e}"),
                judge_response=None, context_stats=ContextStats(),
                stage1_score=stage1_score,
                evaluated_at=datetime.now(timezone.utc).isoformat(),
            ))
            continue

        try:
            # Read full source files + dependencies
            source_files = candidate.get("source_files", [])
            source_contents, dep_contents, truncated = collect_context_files(
                worktree, source_files, max_chars=context_budget,
            )

            ctx_stats = ContextStats(
                source_files_read=len(source_contents),
                dependency_files_read=len(dep_contents),
                total_chars=sum(len(v) for v in source_contents.values())
                    + sum(len(v) for v in dep_contents.values()),
                truncated=truncated,
            )

            print(f"    Context: {ctx_stats.source_files_read} source files, "
                  f"{ctx_stats.dependency_files_read} deps, {ctx_stats.total_chars:,} chars"
                  f"{' (truncated)' if truncated else ''}")

            # Pre-flight validation
            preflight = PreflightResult(candidate_id, "SKIP", "skipped")
            if not skip_preflight:
                print("    Pre-flight...", end=" ")
                preflight = run_preflight(
                    worktree=worktree,
                    candidate_id=candidate_id,
                    patch_diff=candidate.get("patch_diff", ""),
                    test_diff=candidate.get("test_diff", ""),
                    test_files=candidate.get("test_files", []),
                )
                print(f"{preflight.status} — {preflight.reason}")

                if preflight.status != "PASS" and not preflight_only:
                    results.append(DeepEvaluationResult(
                        candidate_id=candidate_id, repo=repo, pr_number=pr_number,
                        preflight=preflight, judge_response=None,
                        context_stats=ctx_stats, stage1_score=stage1_score,
                        evaluated_at=datetime.now(timezone.utc).isoformat(),
                    ))
                    continue

            if preflight_only:
                results.append(DeepEvaluationResult(
                    candidate_id=candidate_id, repo=repo, pr_number=pr_number,
                    preflight=preflight, judge_response=None,
                    context_stats=ctx_stats, stage1_score=stage1_score,
                    evaluated_at=datetime.now(timezone.utc).isoformat(),
                ))
                continue

            # LLM deep evaluation
            print(f"    Evaluating with {config.model}...", end=" ")
            preflight_summary = None
            if preflight.status == "PASS":
                preflight_summary = (
                    f"Status: {preflight.status}\n"
                    f"FAIL_TO_PASS tests: {', '.join(preflight.fail_to_pass_tests)}\n"
                    f"Patch application: {preflight.patch_apply_method}"
                )

            user_prompt = build_deep_user_prompt(
                candidate, source_contents, dep_contents, preflight_summary,
            )

            try:
                raw = provider.evaluate(DEEP_SYSTEM_PROMPT, user_prompt)
                judge_response = DeepJudgeResponse.from_dict(raw)
                print(f"{judge_response.recommendation} (score: {judge_response.total_score}/30)")
            except (ValueError, KeyError, TypeError) as e:
                print(f"    Retry (parse error: {e})...")
                try:
                    raw = provider.evaluate(DEEP_SYSTEM_PROMPT, user_prompt)
                    judge_response = DeepJudgeResponse.from_dict(raw)
                    print(
                        f"    {judge_response.recommendation} "
                        f"(score: {judge_response.total_score}/30)"
                    )
                except Exception as e2:
                    print(f"    FAILED: {e2}")
                    judge_response = None
            except Exception as e:
                print(f"ERROR: {e}")
                judge_response = None

            results.append(DeepEvaluationResult(
                candidate_id=candidate_id, repo=repo, pr_number=pr_number,
                preflight=preflight, judge_response=judge_response,
                context_stats=ctx_stats, stage1_score=stage1_score,
                evaluated_at=datetime.now(timezone.utc).isoformat(),
            ))

        finally:
            cleanup_worktree(bare_repo, worktree)

    return results


def write_deep_results(
    results: list[DeepEvaluationResult],
    repo: str,
    output_dir: Path,
    config: Config,
) -> None:
    """Write Stage 2 results: detailed JSON + verified manifest."""
    output_dir.mkdir(parents=True, exist_ok=True)
    repo_short = repo.split("/")[-1]

    # Detailed results
    detail_path = output_dir / f"{repo_short}_deep_results.json"
    with open(detail_path, "w") as f:
        json.dump([r.to_dict() for r in results], f, indent=2)
    print(f"  Wrote deep results to {detail_path}")

    # Verified manifest — only candidates that passed both preflight and LLM
    min_navigation_depth = getattr(config, "min_navigation_depth", 3)
    llm_accepted = [
        r for r in results
        if r.preflight.status == "PASS"
        and r.judge_response is not None
        and r.judge_response.recommendation == "ACCEPT"
    ]
    verified = [
        r for r in llm_accepted
        if r.judge_response is not None
        and r.judge_response.navigation_depth.score >= min_navigation_depth
    ]

    # Build verified PR entries, loading git SHAs and file lists from candidate JSONs
    candidates_dir = getattr(config, '_candidates_dir', Path("candidates"))
    verified_entries = []
    for r in sorted(verified, key=lambda x: x.judge_response.total_score, reverse=True):
        candidate_data = load_candidate_handoff(candidates_dir / f"{r.candidate_id}.json")
        handoff = build_stage4_handoff(candidate_data)

        verified_entries.append({
            "candidate_id": r.candidate_id,
            "pr_number": r.pr_number,
            **handoff,
            "stage1_score": r.stage1_score,
            "stage2_score": r.judge_response.total_score if r.judge_response else None,
            "navigation_depth": (
                r.judge_response.navigation_depth.score
                if r.judge_response
                else None
            ),
            "scores": r.judge_response.criterion_scores if r.judge_response else {},
            "fail_to_pass_tests": r.preflight.fail_to_pass_tests,
            "pass_to_pass_tests": r.preflight.pass_to_pass_tests,
            "patch_apply_method": r.preflight.patch_apply_method,
        })

    manifest = {
        "repo": repo,
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "model_used": config.model,
        "stage1_candidates": len(results),
        "preflight_passed": sum(1 for r in results if r.preflight.status == "PASS"),
        "llm_stage2_accepted": len(llm_accepted),
        "navigation_depth_threshold": min_navigation_depth,
        "stage2_accepted": len(verified),
        "verified_prs": verified_entries,
    }

    manifest_path = output_dir / f"{repo_short}_verified_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"  Wrote verified manifest ({len(verified)} PRs) to {manifest_path}")
