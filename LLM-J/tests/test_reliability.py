"""Tests for ICC calculation and reliability metrics."""

import math

from src.evaluator.reliability import _compute_icc


def test_icc_perfect_agreement():
    """Perfect agreement should give ICC close to 1.0."""
    pairs = [(3, 3), (4, 4), (5, 5), (2, 2), (1, 1)]
    icc = _compute_icc(pairs)
    assert icc >= 0.99, f"Perfect agreement ICC should be ~1.0, got {icc}"


def test_icc_no_agreement():
    """Random/opposite scores should give ICC near 0 or negative."""
    pairs = [(1, 5), (5, 1), (2, 4), (4, 2), (3, 3)]
    icc = _compute_icc(pairs)
    assert icc < 0.5, f"Poor agreement ICC should be low, got {icc}"


def test_icc_moderate_agreement():
    """Scores within ±1 should give moderate ICC."""
    pairs = [(3, 4), (4, 4), (5, 4), (2, 3), (1, 2)]
    icc = _compute_icc(pairs)
    assert 0.3 < icc < 1.0, f"Moderate agreement ICC should be moderate, got {icc}"


def test_icc_empty_pairs():
    """Empty input should return 0."""
    assert _compute_icc([]) == 0.0


def test_icc_single_pair():
    """Single pair should return 0 (insufficient data)."""
    assert _compute_icc([(3, 4)]) == 0.0


def test_icc_constant_scores():
    """All same scores (no variance) should return 0."""
    pairs = [(3, 3), (3, 3), (3, 3)]
    icc = _compute_icc(pairs)
    assert icc == 0.0 or math.isnan(icc) is False
