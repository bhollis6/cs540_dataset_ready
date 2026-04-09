"""Tests for CSV output formatting."""

import csv
from pathlib import Path

from src.evaluator.models import CriterionScore, EvaluationResult, JudgeResponse
from src.output.csv_writer import write_results_csv, write_summary_csv


def _make_result(
    candidate_id: str = "test_pr_1",
    repo: str = "owner/repo",
    pr_number: int = 1,
    scores: tuple[int, ...] = (4, 5, 4, 4, 4),
    run_number: int = 1,
) -> EvaluationResult:
    s, tc, mr, cl, cx = scores
    response = JudgeResponse(
        scope=CriterionScore(s, "r"),
        test_coverage=CriterionScore(tc, "r"),
        mutation_relevance=CriterionScore(mr, "r"),
        clarity=CriterionScore(cl, "r"),
        complexity=CriterionScore(cx, "r"),
        total_score=s + tc + mr + cl + cx,
        recommendation=JudgeResponse.compute_recommendation(s + tc + mr + cl + cx),
        summary="test",
    )
    return EvaluationResult(
        candidate_id=candidate_id,
        repo=repo,
        pr_number=pr_number,
        response=response,
        run_number=run_number,
        model="claude-opus-4-6",
        provider="anthropic",
        evaluated_at="2024-01-01T00:00:00Z",
    )


def test_write_results_csv(tmp_path: Path):
    results = [
        _make_result("pr_1", scores=(4, 5, 4, 4, 4)),
        _make_result("pr_2", scores=(2, 1, 3, 2, 1)),
    ]
    out = tmp_path / "results.csv"
    write_results_csv(results, out)

    with open(out) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 2
    assert rows[0]["candidate_id"] == "pr_1"
    assert rows[0]["total_score"] == "21"
    assert rows[0]["recommendation"] == "ACCEPT"
    assert rows[1]["recommendation"] == "REJECT"


def test_write_summary_csv(tmp_path: Path):
    results = [
        _make_result("pr_1", repo="owner/repo", scores=(4, 5, 4, 4, 4)),
        _make_result("pr_2", repo="owner/repo", scores=(2, 1, 3, 2, 1)),
        _make_result("pr_3", repo="other/repo", scores=(3, 3, 3, 3, 3)),
    ]
    out = tmp_path / "summary.csv"
    write_summary_csv(results, out)

    with open(out) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 2  # two repos
    repo1 = next(r for r in rows if r["repo"] == "owner/repo")
    assert repo1["total_candidates"] == "2"
    assert repo1["accepted"] == "1"
    assert repo1["rejected"] == "1"


def test_summary_uses_only_run1(tmp_path: Path):
    """Summary should only count run_number=1 results."""
    results = [
        _make_result("pr_1", run_number=1, scores=(4, 5, 4, 4, 4)),
        _make_result("pr_1", run_number=2, scores=(4, 5, 4, 4, 4)),
    ]
    out = tmp_path / "summary.csv"
    write_summary_csv(results, out)

    with open(out) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert rows[0]["total_candidates"] == "1"  # not 2
