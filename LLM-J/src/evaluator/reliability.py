"""Reliability measurement: ICC, agreement rates, recommendation consistency."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import numpy as np

from src.evaluator.models import EvaluationResult

CRITERIA = ["scope", "test_coverage", "mutation_relevance", "clarity", "complexity"]


def compute_reliability(results: list[EvaluationResult], output_path: Path) -> None:
    """Compute reliability metrics from dual-run evaluation results.

    Expects results to contain run_number 1 and 2 for each candidate.
    Writes reliability.csv and prints a summary.
    """
    # Pair up run 1 and run 2 results by candidate_id
    by_candidate: dict[str, dict[int, EvaluationResult]] = defaultdict(dict)
    for r in results:
        by_candidate[r.candidate_id][r.run_number] = r

    # Only keep candidates with both runs
    paired = {
        cid: runs for cid, runs in by_candidate.items()
        if 1 in runs and 2 in runs
    }

    if not paired:
        print("  No paired results found for reliability analysis.")
        return

    n = len(paired)
    print(f"\n  Reliability analysis on {n} paired evaluations:")

    # Collect score pairs per criterion
    score_pairs: dict[str, list[tuple[int, int]]] = {c: [] for c in CRITERIA}
    recommendation_pairs: list[tuple[str, str]] = []

    for cid in sorted(paired):
        r1 = paired[cid][1]
        r2 = paired[cid][2]

        for criterion in CRITERIA:
            s1 = r1.response.criterion_scores[criterion]
            s2 = r2.response.criterion_scores[criterion]
            score_pairs[criterion].append((s1, s2))

        recommendation_pairs.append(
            (r1.response.recommendation, r2.response.recommendation)
        )

    # Compute metrics
    rows = []
    for criterion in CRITERIA:
        pairs = score_pairs[criterion]
        icc = _compute_icc(pairs)
        exact_agree = sum(1 for a, b in pairs if a == b) / len(pairs)
        within_one = sum(1 for a, b in pairs if abs(a - b) <= 1) / len(pairs)

        rows.append({
            "criterion": criterion,
            "icc": round(icc, 3),
            "exact_agreement": round(exact_agree, 3),
            "within_one_agreement": round(within_one, 3),
            "n_pairs": len(pairs),
        })

        print(f"    {criterion}: ICC={icc:.3f}, exact={exact_agree:.1%}, ±1={within_one:.1%}")

    # Recommendation consistency
    rec_agree = sum(1 for a, b in recommendation_pairs if a == b) / len(recommendation_pairs)
    print(f"    Recommendation consistency: {rec_agree:.1%}")

    # Total score ICC
    total_pairs = []
    for cid in sorted(paired):
        r1 = paired[cid][1]
        r2 = paired[cid][2]
        total_pairs.append((r1.response.total_score, r2.response.total_score))

    total_icc = _compute_icc(total_pairs)
    print(f"    Total score ICC: {total_icc:.3f}")

    # Write CSV
    fieldnames = ["criterion", "icc", "exact_agreement", "within_one_agreement", "n_pairs"]
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

        # Add summary rows
        writer.writerow({
            "criterion": "total_score",
            "icc": round(total_icc, 3),
            "exact_agreement": round(
                sum(1 for a, b in total_pairs if a == b) / len(total_pairs), 3
            ),
            "within_one_agreement": round(
                sum(1 for a, b in total_pairs if abs(a - b) <= 1) / len(total_pairs), 3
            ),
            "n_pairs": len(total_pairs),
        })
        writer.writerow({
            "criterion": "recommendation",
            "icc": "",
            "exact_agreement": round(rec_agree, 3),
            "within_one_agreement": "",
            "n_pairs": len(recommendation_pairs),
        })

    print(f"  Wrote reliability metrics to {output_path}")


def _compute_icc(pairs: list[tuple[int, int]]) -> float:
    """Compute ICC(3,1) — two-way mixed, single measures, consistency.

    This is the appropriate ICC variant for our case:
    - Same two "raters" (same LLM, same prompt) evaluate every subject
    - We care about consistency (relative agreement), not absolute agreement
    """
    if not pairs:
        return 0.0

    n = len(pairs)
    if n < 2:
        return 0.0

    # Convert to numpy arrays — each pair is (rater1, rater2) for one subject
    scores = np.array(pairs, dtype=float)  # shape: (n, 2)

    # Grand mean
    grand_mean = scores.mean()

    # Subject means (average of the two raters per subject)
    subject_means = scores.mean(axis=1)  # shape: (n,)

    # Rater means (average across all subjects for each rater)
    rater_means = scores.mean(axis=0)  # shape: (2,)

    k = 2  # number of raters

    # Between-subjects sum of squares
    ms_between = k * np.sum((subject_means - grand_mean) ** 2) / (n - 1)

    # Residual (error) sum of squares
    ss_total = np.sum((scores - grand_mean) ** 2)
    ss_between = k * np.sum((subject_means - grand_mean) ** 2)
    ss_raters = n * np.sum((rater_means - grand_mean) ** 2)
    ss_error = ss_total - ss_between - ss_raters
    ms_error = ss_error / ((n - 1) * (k - 1))

    # ICC(3,1) = (MS_between - MS_error) / (MS_between + (k-1)*MS_error)
    denominator = ms_between + (k - 1) * ms_error
    if denominator == 0:
        return 0.0

    icc = (ms_between - ms_error) / denominator
    return float(icc)
