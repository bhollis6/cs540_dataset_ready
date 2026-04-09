"""Tests for prompt construction."""

import json
from pathlib import Path

from src.evaluator.prompts import SYSTEM_PROMPT, build_user_prompt

FIXTURES = Path(__file__).parent / "fixtures"


def test_system_prompt_contains_rubric():
    """System prompt includes all 5 scoring criteria."""
    assert "Scope (1-5)" in SYSTEM_PROMPT
    assert "Test Coverage (1-5)" in SYSTEM_PROMPT
    assert "Mutation Relevance (1-5)" in SYSTEM_PROMPT
    assert "Clarity (1-5)" in SYSTEM_PROMPT
    assert "Complexity (1-5)" in SYSTEM_PROMPT


def test_system_prompt_emphasizes_strict_evaluation():
    """System prompt tells the judge not to be generous."""
    assert "strict" in SYSTEM_PROMPT.lower() or "not be generous" in SYSTEM_PROMPT.lower()


def test_system_prompt_warns_about_complexity():
    """System prompt clarifies that complexity 5 is also bad."""
    assert "sweet spot" in SYSTEM_PROMPT.lower() or "3-4" in SYSTEM_PROMPT


def test_user_prompt_contains_candidate_data():
    """User prompt includes all relevant PR data."""
    with open(FIXTURES / "sample_candidate.json") as f:
        data = json.load(f)

    prompt = build_user_prompt(data)
    assert "fastapi_pr_4821" in prompt
    assert "tiangolo/fastapi" in prompt
    assert "4821" in prompt
    assert "Fix token refresh race condition" in prompt
    assert "fastapi/security/oauth2.py" in prompt


def test_user_prompt_truncates_long_diffs():
    """User prompt truncates diffs that exceed the limit."""
    data = {
        "candidate_id": "test_pr_1",
        "repo": "owner/repo",
        "pr_number": 1,
        "title": "Test",
        "description": "Test PR",
        "patch_diff": "x" * 50000,
        "test_diff": "y" * 50000,
        "source_files": ["src/main.py"],
        "test_files": ["tests/test_main.py"],
        "lines_added": 100,
        "lines_removed": 50,
    }
    prompt = build_user_prompt(data)
    assert "truncated" in prompt
    assert len(prompt) < 100000  # should be truncated
