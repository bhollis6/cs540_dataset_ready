"""CSV and JSON output writers for evaluation results."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

from src.evaluator.models import EvaluationResult

RESULTS_COLUMNS = [
    "candidate_id", "repo", "pr_number",
    "scope", "test_coverage", "mutation_relevance", "clarity", "complexity",
    "total_score", "recommendation", "summary",
    "run_number", "model", "provider",
]

SUMMARY_COLUMNS = [
    "repo", "total_candidates", "accepted", "review", "rejected", "top_candidates",
]


def write_results_csv(results: list[EvaluationResult], path: Path) -> None:
    """Write per-candidate results to CSV."""
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=RESULTS_COLUMNS)
        writer.writeheader()
        for result in results:
            writer.writerow(result.to_csv_row())

    print(f"  Wrote {len(results)} results to {path}")


def write_summary_csv(results: list[EvaluationResult], path: Path) -> None:
    """Write per-repo summary to CSV."""
    # Group by repo, using only run_number=1 for summary
    by_repo: dict[str, list[EvaluationResult]] = defaultdict(list)
    for r in results:
        if r.run_number == 1:
            by_repo[r.repo].append(r)

    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SUMMARY_COLUMNS)
        writer.writeheader()

        for repo in sorted(by_repo):
            repo_results = by_repo[repo]
            accepted = [r for r in repo_results if r.response.recommendation == "ACCEPT"]
            review = [r for r in repo_results if r.response.recommendation == "REVIEW"]
            rejected = [r for r in repo_results if r.response.recommendation == "REJECT"]

            # Top candidates by total score
            top = sorted(repo_results, key=lambda r: r.response.total_score, reverse=True)[:5]
            top_str = ", ".join(f"pr_{r.pr_number}" for r in top)

            writer.writerow({
                "repo": repo,
                "total_candidates": len(repo_results),
                "accepted": len(accepted),
                "review": len(review),
                "rejected": len(rejected),
                "top_candidates": top_str,
            })

    print(f"  Wrote summary for {len(by_repo)} repos to {path}")


def write_detailed_json(results: list[EvaluationResult], path: Path) -> None:
    """Write full evaluation results with per-criterion reasoning to JSON."""
    output = []
    for r in results:
        output.append({
            "candidate_id": r.candidate_id,
            "repo": r.repo,
            "pr_number": r.pr_number,
            "run_number": r.run_number,
            "model": r.model,
            "provider": r.provider,
            "total_score": r.response.total_score,
            "recommendation": r.response.recommendation,
            "summary": r.response.summary,
            "scores": {
                "scope": r.response.scope.to_dict(),
                "test_coverage": r.response.test_coverage.to_dict(),
                "mutation_relevance": r.response.mutation_relevance.to_dict(),
                "clarity": r.response.clarity.to_dict(),
                "complexity": r.response.complexity.to_dict(),
            },
        })

    with open(path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  Wrote detailed results with reasoning to {path}")
