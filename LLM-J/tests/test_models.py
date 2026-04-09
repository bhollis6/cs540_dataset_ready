"""Tests for data models and serialization."""

import json
from pathlib import Path

from src.evaluator.models import CriterionScore, EvaluationResult, JudgeResponse
from src.scraper.models import CandidatePR, _is_non_code_file, _is_test_file

FIXTURES = Path(__file__).parent / "fixtures"


def test_candidate_roundtrip():
    """CandidatePR serializes to dict and back identically."""
    with open(FIXTURES / "sample_candidate.json") as f:
        data = json.load(f)

    candidate = CandidatePR.from_dict(data)
    assert candidate.candidate_id == "fastapi_pr_4821"
    assert candidate.pr_number == 4821
    assert candidate.has_test_changes is True
    assert candidate.merge_commit_sha == "abc123def456"

    roundtripped = CandidatePR.from_dict(candidate.to_dict())
    assert roundtripped.candidate_id == candidate.candidate_id
    assert roundtripped.merge_commit_sha == candidate.merge_commit_sha


def test_judge_response_from_dict():
    """JudgeResponse parses and computes total/recommendation correctly."""
    with open(FIXTURES / "sample_judge_response.json") as f:
        data = json.load(f)

    response = JudgeResponse.from_dict(data)
    assert response.scope.score == 4
    assert response.test_coverage.score == 5
    assert response.total_score == 21  # 4+5+4+4+4
    assert response.recommendation == "ACCEPT"  # 21 >= 18


def test_judge_response_recommendation_thresholds():
    """Verify ACCEPT/REVIEW/REJECT thresholds."""
    assert JudgeResponse.compute_recommendation(18) == "ACCEPT"
    assert JudgeResponse.compute_recommendation(25) == "ACCEPT"
    assert JudgeResponse.compute_recommendation(17) == "REVIEW"
    assert JudgeResponse.compute_recommendation(13) == "REVIEW"
    assert JudgeResponse.compute_recommendation(12) == "REJECT"
    assert JudgeResponse.compute_recommendation(5) == "REJECT"


def test_judge_response_recomputes_total():
    """JudgeResponse recomputes total from criterion scores, ignoring LLM's total."""
    data = {
        "scope": {"score": 1, "reasoning": "bad"},
        "test_coverage": {"score": 1, "reasoning": "bad"},
        "mutation_relevance": {"score": 1, "reasoning": "bad"},
        "clarity": {"score": 1, "reasoning": "bad"},
        "complexity": {"score": 1, "reasoning": "bad"},
        "total_score": 99,  # LLM said 99, but real total is 5
        "recommendation": "ACCEPT",  # LLM said ACCEPT, but should be REJECT
        "summary": "test",
    }
    response = JudgeResponse.from_dict(data)
    assert response.total_score == 5
    assert response.recommendation == "REJECT"


def test_is_test_file():
    assert _is_test_file("tests/test_main.py") is True
    assert _is_test_file("test/test_main.py") is True
    assert _is_test_file("src/test_utils.py") is True
    assert _is_test_file("src/main_test.py") is True
    assert _is_test_file("conftest.py") is True
    assert _is_test_file("src/main.py") is False
    assert _is_test_file("src/testing.py") is False


def test_is_non_code_file():
    assert _is_non_code_file("README.md") is True
    assert _is_non_code_file("docs/guide.rst") is True
    assert _is_non_code_file(".github/workflows/ci.yml") is True
    assert _is_non_code_file("Dockerfile") is True
    assert _is_non_code_file("src/main.py") is False
    assert _is_non_code_file("fastapi/security/oauth2.py") is False


def test_evaluation_result_csv_row():
    response = JudgeResponse(
        scope=CriterionScore(4, "good"),
        test_coverage=CriterionScore(5, "great"),
        mutation_relevance=CriterionScore(3, "ok"),
        clarity=CriterionScore(4, "clear"),
        complexity=CriterionScore(3, "moderate"),
        total_score=19,
        recommendation="ACCEPT",
        summary="solid candidate",
    )
    result = EvaluationResult(
        candidate_id="test_pr_1",
        repo="owner/repo",
        pr_number=1,
        response=response,
        run_number=1,
        model="claude-opus-4-6",
        provider="anthropic",
        evaluated_at="2024-01-01T00:00:00Z",
    )
    row = result.to_csv_row()
    assert row["scope"] == 4
    assert row["total_score"] == 19
    assert row["recommendation"] == "ACCEPT"
    assert row["run_number"] == 1
