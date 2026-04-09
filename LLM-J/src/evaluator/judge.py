"""LLM judge orchestration — sends candidates for evaluation and parses results."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from src.evaluator.models import EvaluationResult, JudgeResponse
from src.evaluator.prompts import SYSTEM_PROMPT, build_user_prompt
from src.providers.base import get_provider

if TYPE_CHECKING:
    from src.config import Config
    from src.providers.base import LLMProvider
    from src.scraper.models import CandidatePR


def evaluate_single(
    candidate: CandidatePR,
    provider_instance: LLMProvider,
    run_number: int = 1,
    accept_threshold: int | None = None,
    review_threshold: int | None = None,
) -> EvaluationResult | None:
    """Evaluate a single candidate PR using the LLM judge.

    Returns None if evaluation fails after retries.
    """
    user_prompt = build_user_prompt(candidate.to_dict())

    # First attempt
    try:
        raw_response = provider_instance.evaluate(SYSTEM_PROMPT, user_prompt)
        judge_response = JudgeResponse.from_dict_with_thresholds(
            raw_response,
            accept_threshold=accept_threshold,
            review_threshold=review_threshold,
        )
    except (ValueError, KeyError, TypeError) as e:
        # Retry once on malformed response
        print(f"    Retry (parse error: {e})...")
        try:
            raw_response = provider_instance.evaluate(SYSTEM_PROMPT, user_prompt)
            judge_response = JudgeResponse.from_dict_with_thresholds(
                raw_response,
                accept_threshold=accept_threshold,
                review_threshold=review_threshold,
            )
        except (ValueError, KeyError, TypeError) as e2:
            print(f"    FAILED after retry: {e2}")
            return None
    except Exception as e:
        print(f"    API error: {e}")
        return None

    return EvaluationResult(
        candidate_id=candidate.candidate_id,
        repo=candidate.repo,
        pr_number=candidate.pr_number,
        response=judge_response,
        run_number=run_number,
        model=provider_instance.model_name,
        provider=provider_instance.provider_name,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )


def evaluate_candidates(
    candidates: list[CandidatePR],
    config: Config,
) -> list[EvaluationResult]:
    """Evaluate all candidates, optionally with reliability double-run."""
    provider_instance = get_provider(config.provider, config.model, config.api_key)
    runs_per_candidate = 2 if config.reliability_check else 1
    results: list[EvaluationResult] = []

    total = len(candidates) * runs_per_candidate
    current = 0

    for candidate in candidates:
        for run in range(1, runs_per_candidate + 1):
            current += 1
            run_label = f" (run {run})" if runs_per_candidate > 1 else ""
            print(
                f"  [{current}/{total}] Evaluating {candidate.candidate_id}{run_label}...",
                end=" ",
            )

            result = evaluate_single(
                candidate,
                provider_instance,
                run_number=run,
                accept_threshold=config.accept_threshold,
                review_threshold=config.review_threshold,
            )

            if result:
                rec = result.response.recommendation
                score = result.response.total_score
                print(f"{rec} (score: {score})")
                results.append(result)
            else:
                print("SKIPPED (evaluation failed)")

    return results
