"""Data models for LLM judge evaluation results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CriterionScore:
    """A single criterion score with reasoning."""

    score: int
    reasoning: str

    def to_dict(self) -> dict[str, Any]:
        return {"score": self.score, "reasoning": self.reasoning}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CriterionScore:
        return cls(score=int(data["score"]), reasoning=str(data["reasoning"]))


@dataclass
class JudgeResponse:
    """Structured response from the LLM judge."""

    scope: CriterionScore
    test_coverage: CriterionScore
    mutation_relevance: CriterionScore
    clarity: CriterionScore
    complexity: CriterionScore
    total_score: int
    recommendation: str  # "ACCEPT" | "REVIEW" | "REJECT"
    summary: str

    ACCEPT_THRESHOLD = 18
    REVIEW_THRESHOLD = 13

    @classmethod
    def compute_recommendation(
        cls,
        total_score: int,
        accept_threshold: int | None = None,
        review_threshold: int | None = None,
    ) -> str:
        accept = accept_threshold if accept_threshold is not None else cls.ACCEPT_THRESHOLD
        review = review_threshold if review_threshold is not None else cls.REVIEW_THRESHOLD
        if total_score >= accept:
            return "ACCEPT"
        elif total_score >= review:
            return "REVIEW"
        return "REJECT"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> JudgeResponse:
        return cls.from_dict_with_thresholds(data)

    @classmethod
    def from_dict_with_thresholds(
        cls,
        data: dict[str, Any],
        accept_threshold: int | None = None,
        review_threshold: int | None = None,
    ) -> JudgeResponse:
        scope = CriterionScore.from_dict(data["scope"])
        test_coverage = CriterionScore.from_dict(data["test_coverage"])
        mutation_relevance = CriterionScore.from_dict(data["mutation_relevance"])
        clarity = CriterionScore.from_dict(data["clarity"])
        complexity = CriterionScore.from_dict(data["complexity"])

        total = (
            scope.score
            + test_coverage.score
            + mutation_relevance.score
            + clarity.score
            + complexity.score
        )

        # Use computed total and recommendation (don't trust LLM arithmetic)
        recommendation = cls.compute_recommendation(
            total,
            accept_threshold=accept_threshold,
            review_threshold=review_threshold,
        )

        return cls(
            scope=scope,
            test_coverage=test_coverage,
            mutation_relevance=mutation_relevance,
            clarity=clarity,
            complexity=complexity,
            total_score=total,
            recommendation=recommendation,
            summary=str(data.get("summary", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "scope": self.scope.to_dict(),
            "test_coverage": self.test_coverage.to_dict(),
            "mutation_relevance": self.mutation_relevance.to_dict(),
            "clarity": self.clarity.to_dict(),
            "complexity": self.complexity.to_dict(),
            "total_score": self.total_score,
            "recommendation": self.recommendation,
            "summary": self.summary,
        }

    @property
    def criterion_scores(self) -> dict[str, int]:
        return {
            "scope": self.scope.score,
            "test_coverage": self.test_coverage.score,
            "mutation_relevance": self.mutation_relevance.score,
            "clarity": self.clarity.score,
            "complexity": self.complexity.score,
        }


@dataclass
class EvaluationResult:
    """A complete evaluation result tying a candidate to a judge response."""

    candidate_id: str
    repo: str
    pr_number: int
    response: JudgeResponse
    run_number: int  # 1 or 2 (for reliability measurement)
    model: str
    provider: str
    evaluated_at: str

    def to_csv_row(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "repo": self.repo,
            "pr_number": self.pr_number,
            "scope": self.response.scope.score,
            "test_coverage": self.response.test_coverage.score,
            "mutation_relevance": self.response.mutation_relevance.score,
            "clarity": self.response.clarity.score,
            "complexity": self.response.complexity.score,
            "total_score": self.response.total_score,
            "recommendation": self.response.recommendation,
            "summary": self.response.summary,
            "run_number": self.run_number,
            "model": self.model,
            "provider": self.provider,
        }
