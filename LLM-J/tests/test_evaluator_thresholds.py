"""Regression tests for evaluation threshold handling."""

import json
from pathlib import Path

from src.config import Config
from src.evaluator.judge import evaluate_candidates
from src.scraper.models import CandidatePR

FIXTURES = Path(__file__).parent / "fixtures"


class FakeProvider:
    """Provider stub that returns a fixed judge payload."""

    model_name = "fake-model"
    provider_name = "fake-provider"

    def evaluate(self, system_prompt: str, user_content: str) -> dict:
        return {
            "scope": {"score": 4, "reasoning": "focused"},
            "test_coverage": {"score": 4, "reasoning": "good tests"},
            "mutation_relevance": {"score": 3, "reasoning": "relevant enough"},
            "clarity": {"score": 3, "reasoning": "clear enough"},
            "complexity": {"score": 3, "reasoning": "moderate"},
            "summary": "threshold exercise",
        }


def test_evaluate_candidates_uses_configured_thresholds(monkeypatch):
    """Configured thresholds should affect final recommendations."""
    with open(FIXTURES / "sample_candidate.json") as f:
        candidate = CandidatePR.from_dict(json.load(f))

    config = Config(
        provider="claude-code",
        model="fake-model",
        accept_threshold=17,
        review_threshold=12,
    )

    monkeypatch.setattr("src.evaluator.judge.get_provider", lambda *args: FakeProvider())

    results = evaluate_candidates([candidate], config)

    assert len(results) == 1
    assert results[0].response.total_score == 17
    assert results[0].response.recommendation == "ACCEPT"
