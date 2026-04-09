"""Tests for Anthropic provider schema construction."""

import pytest


def test_build_evaluation_tool_stage1_schema():
    """Stage 1 schema should not require navigation depth."""
    pytest.importorskip("anthropic")
    from src.providers.anthropic import _build_evaluation_tool

    tool = _build_evaluation_tool(has_navigation_depth=False)

    assert "navigation_depth" not in tool["input_schema"]["properties"]
    assert "navigation_depth" not in tool["input_schema"]["required"]


def test_build_evaluation_tool_stage2_schema():
    """Stage 2 schema should include navigation depth."""
    pytest.importorskip("anthropic")
    from src.providers.anthropic import _build_evaluation_tool

    tool = _build_evaluation_tool(has_navigation_depth=True)

    assert "navigation_depth" in tool["input_schema"]["properties"]
    assert "navigation_depth" in tool["input_schema"]["required"]
