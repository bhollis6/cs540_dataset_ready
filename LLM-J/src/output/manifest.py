"""Generate selected_prs.json manifest for downstream pipeline stages."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.config import Config
    from src.evaluator.models import EvaluationResult


def write_manifest(results: list[EvaluationResult], config: Config) -> None:
    """Write per-repo selected_prs.json manifests to the output directory.

    These manifests are the handoff to Stage 4 (codebase mutation) and
    Stage 5 (agent task runs). They contain everything downstream needs
    to revert PRs and apply targeted degradation.
    """
    # Group run_number=1 results by repo
    by_repo: dict[str, list[EvaluationResult]] = defaultdict(list)
    for r in results:
        if r.run_number == 1:
            by_repo[r.repo].append(r)

    for repo, repo_results in sorted(by_repo.items()):
        accepted = [r for r in repo_results if r.response.recommendation == "ACCEPT"]
        review = [r for r in repo_results if r.response.recommendation == "REVIEW"]
        rejected = [r for r in repo_results if r.response.recommendation == "REJECT"]

        # Load candidate data to get git SHAs and file lists
        selected_prs = []
        for r in sorted(accepted, key=lambda x: x.response.total_score, reverse=True):
            candidate_file = config.input_dir / f"{r.candidate_id}.json"
            candidate_data = {}
            if candidate_file.exists():
                with open(candidate_file) as f:
                    candidate_data = json.load(f)

            selected_prs.append({
                "candidate_id": r.candidate_id,
                "pr_number": r.pr_number,
                "total_score": r.response.total_score,
                "scores": r.response.criterion_scores,
                "recommendation": r.response.recommendation,
                "summary": r.response.summary,
                "merge_commit_sha": candidate_data.get("merge_commit_sha"),
                "base_commit_sha": candidate_data.get("base_commit_sha"),
                "head_commit_sha": candidate_data.get("head_commit_sha"),
                "source_files": candidate_data.get("source_files", []),
                "test_files": candidate_data.get("test_files", []),
            })

        manifest = {
            "repo": repo,
            "selection_timestamp": datetime.now(timezone.utc).isoformat(),
            "model_used": config.model,
            "provider_used": config.provider,
            "total_candidates": len(repo_results),
            "accepted": len(accepted),
            "review": len(review),
            "rejected": len(rejected),
            "accept_threshold": config.accept_threshold,
            "selected_prs": selected_prs,
        }

        repo_short = repo.split("/")[-1]
        manifest_path = config.output_dir / f"{repo_short}_selected_prs.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        print(f"  Wrote manifest ({len(selected_prs)} accepted PRs) to {manifest_path}")
