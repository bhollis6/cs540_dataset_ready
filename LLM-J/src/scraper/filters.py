"""Heuristic pre-filters for PR candidates."""

from __future__ import annotations

from dataclasses import dataclass

from src.scraper.models import PRMetadata


@dataclass
class FilterStats:
    """Tracks how many PRs were filtered by each criterion."""

    total_input: int = 0
    no_test_changes: int = 0
    test_only: int = 0
    too_few_lines: int = 0
    too_many_lines: int = 0
    too_many_files: int = 0
    empty_description: int = 0
    too_old: int = 0
    bot_pr: int = 0
    passed: int = 0

    def __str__(self) -> str:
        return (
            f"Total: {self.total_input} | "
            f"No tests: {self.no_test_changes} | "
            f"Test-only: {self.test_only} | "
            f"Too small: {self.too_few_lines} | "
            f"Too large: {self.too_many_lines} | "
            f"Too many files: {self.too_many_files} | "
            f"Empty desc: {self.empty_description} | "
            f"Too old: {self.too_old} | "
            f"Bot: {self.bot_pr} | "
            f"Passed: {self.passed}"
        )


def apply_filters(
    prs: list[PRMetadata],
    config: object,
) -> tuple[list[PRMetadata], FilterStats]:
    """Apply heuristic pre-filters to PR metadata.

    config must have: min_lines_changed, max_lines_changed, max_files_changed,
    min_description_length, skip_bot_prs, target_candidates.
    """
    stats = FilterStats(total_input=len(prs))
    survivors: list[PRMetadata] = []

    target = getattr(config, "target_candidates", None)

    for pr in prs:
        # 1. Must have test file changes
        if not pr.has_test_changes:
            stats.no_test_changes += 1
            continue

        # 2. Must not be test-only (must touch source code too)
        if not pr.has_source_changes:
            stats.test_only += 1
            continue

        # 3. Minimum lines changed
        if pr.total_lines_changed < getattr(config, "min_lines_changed", 5):
            stats.too_few_lines += 1
            continue

        # 4. Maximum lines changed
        if pr.total_lines_changed > getattr(config, "max_lines_changed", 500):
            stats.too_many_lines += 1
            continue

        # 5. Maximum files changed
        if pr.changed_files_count > getattr(config, "max_files_changed", 20):
            stats.too_many_files += 1
            continue

        # 6. Has meaningful description
        desc_len = len((pr.body or "").strip())
        if desc_len < getattr(config, "min_description_length", 20):
            stats.empty_description += 1
            continue

        # 7. Skip PRs older than min_date
        min_date = getattr(config, "min_date", None)
        if min_date and pr.merged_at and pr.merged_at < min_date:
            stats.too_old += 1
            continue

        # 8. Skip bot PRs (optional)
        if getattr(config, "skip_bot_prs", True) and pr.is_bot:
            stats.bot_pr += 1
            continue

        survivors.append(pr)

        # Early stop if we have enough candidates
        if target and len(survivors) >= target:
            break

    stats.passed = len(survivors)
    return survivors, stats
