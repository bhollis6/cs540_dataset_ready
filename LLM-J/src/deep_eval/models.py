"""Data models for Stage 2 deep evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.evaluator.models import CriterionScore


@dataclass
class PreflightResult:
    """Result of mechanical FAIL_TO_PASS validation."""

    candidate_id: str
    status: str  # "PASS" | "FAIL" | "ERROR"
    reason: str
    fail_to_pass_tests: list[str] = field(default_factory=list)
    pass_to_pass_tests: list[str] = field(default_factory=list)
    base_test_output: str = ""  # raw pytest output at base_commit (truncated)
    fixed_test_output: str = ""  # raw pytest output after gold patch (truncated)
    patch_apply_method: str = ""  # "git_apply" | "git_apply_reject" | "patch_fuzz"
    install_success: bool = False
    elapsed_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "status": self.status,
            "reason": self.reason,
            "fail_to_pass_tests": self.fail_to_pass_tests,
            "pass_to_pass_tests": self.pass_to_pass_tests,
            "patch_apply_method": self.patch_apply_method,
            "install_success": self.install_success,
            "elapsed_seconds": self.elapsed_seconds,
        }


@dataclass
class ContextStats:
    """Metadata about the context provided to the judge."""

    source_files_read: int = 0
    dependency_files_read: int = 0
    total_chars: int = 0
    truncated: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_files_read": self.source_files_read,
            "dependency_files_read": self.dependency_files_read,
            "total_chars": self.total_chars,
            "truncated": self.truncated,
        }


@dataclass
class DeepJudgeResponse:
    """Stage 2 judge response with 6 criteria."""

    scope: CriterionScore
    test_coverage: CriterionScore
    mutation_relevance: CriterionScore
    clarity: CriterionScore
    complexity: CriterionScore
    navigation_depth: CriterionScore
    total_score: int  # out of 30
    recommendation: str  # "ACCEPT" | "REVIEW" | "REJECT"
    summary: str

    ACCEPT_THRESHOLD = 22  # ~73%, proportional to Stage 1's 18/25
    REVIEW_THRESHOLD = 16

    @classmethod
    def compute_recommendation(cls, total_score: int) -> str:
        if total_score >= cls.ACCEPT_THRESHOLD:
            return "ACCEPT"
        elif total_score >= cls.REVIEW_THRESHOLD:
            return "REVIEW"
        return "REJECT"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeepJudgeResponse:
        scope = CriterionScore.from_dict(data["scope"])
        test_coverage = CriterionScore.from_dict(data["test_coverage"])
        mutation_relevance = CriterionScore.from_dict(data["mutation_relevance"])
        clarity = CriterionScore.from_dict(data["clarity"])
        complexity = CriterionScore.from_dict(data["complexity"])
        navigation_depth = CriterionScore.from_dict(data["navigation_depth"])

        total = (
            scope.score + test_coverage.score + mutation_relevance.score
            + clarity.score + complexity.score + navigation_depth.score
        )
        recommendation = cls.compute_recommendation(total)

        return cls(
            scope=scope,
            test_coverage=test_coverage,
            mutation_relevance=mutation_relevance,
            clarity=clarity,
            complexity=complexity,
            navigation_depth=navigation_depth,
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
            "navigation_depth": self.navigation_depth.to_dict(),
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
            "navigation_depth": self.navigation_depth.score,
        }


@dataclass
class DeepEvaluationResult:
    """Complete Stage 2 result for a single candidate."""

    candidate_id: str
    repo: str
    pr_number: int
    preflight: PreflightResult
    judge_response: DeepJudgeResponse | None  # None if preflight failed
    context_stats: ContextStats
    stage1_score: int  # original Stage 1 total score
    evaluated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "repo": self.repo,
            "pr_number": self.pr_number,
            "preflight": self.preflight.to_dict(),
            "judge_response": self.judge_response.to_dict() if self.judge_response else None,
            "context_stats": self.context_stats.to_dict(),
            "stage1_score": self.stage1_score,
            "evaluated_at": self.evaluated_at,
        }
