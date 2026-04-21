"""Tests for Stage 2 output contracts."""

import json
from pathlib import Path

import pytest

from src.config import Config
from src.deep_eval.deep_judge import write_deep_results
from src.deep_eval.models import (
    ContextStats,
    DeepEvaluationResult,
    DeepJudgeResponse,
    PreflightResult,
)
from src.evaluator.models import CriterionScore


def _make_deep_result(
    candidate_id: str = "repo_pr_1",
    navigation_depth: int = 4,
) -> DeepEvaluationResult:
    """Create a passing Stage 2 result for manifest tests."""
    return DeepEvaluationResult(
        candidate_id=candidate_id,
        repo="owner/repo",
        pr_number=1,
        preflight=PreflightResult(
            candidate_id=candidate_id,
            status="PASS",
            reason="1 tests went FAIL→PASS",
            fail_to_pass_tests=["tests/test_example.py::test_fix"],
            pass_to_pass_tests=["tests/test_example.py::test_existing"],
            patch_apply_method="test:git_apply, fix:git_apply",
            install_success=True,
        ),
        judge_response=DeepJudgeResponse(
            scope=CriterionScore(4, "focused"),
            test_coverage=CriterionScore(4, "good"),
            mutation_relevance=CriterionScore(4, "relevant"),
            clarity=CriterionScore(4, "clear"),
            complexity=CriterionScore(3, "moderate"),
            navigation_depth=CriterionScore(navigation_depth, "cross-file"),
            total_score=19 + navigation_depth,
            recommendation="ACCEPT",
            summary="strong candidate",
        ),
        context_stats=ContextStats(source_files_read=2, dependency_files_read=1),
        stage1_score=19,
        evaluated_at="2026-03-24T00:00:00Z",
    )


def test_write_deep_results_writes_complete_verified_manifest(tmp_path: Path):
    """Verified manifest should contain real git metadata and file lists."""
    candidates_dir = tmp_path / "candidates"
    output_dir = tmp_path / "deep_results"
    candidates_dir.mkdir()

    candidate_file = candidates_dir / "repo_pr_1.json"
    candidate_file.write_text(json.dumps({
        "candidate_id": "repo_pr_1",
        "base_commit_sha": "base123",
        "merge_commit_sha": "merge123",
        "head_commit_sha": "head123",
        "source_files": ["src/app.py"],
        "test_files": ["tests/test_app.py"],
        "test_support_files": ["tests/conftest.py"],
    }))

    config = Config(model="claude-opus-4-6")
    config._candidates_dir = candidates_dir

    write_deep_results([_make_deep_result()], "owner/repo", output_dir, config)

    manifest = json.loads((output_dir / "repo_verified_manifest.json").read_text())
    entry = manifest["verified_prs"][0]

    assert manifest["navigation_depth_threshold"] == 3
    assert manifest["llm_stage2_accepted"] == 1
    assert entry["base_commit_sha"] == "base123"
    assert entry["merge_commit_sha"] == "merge123"
    assert entry["head_commit_sha"] == "head123"
    assert entry["source_files"] == ["src/app.py"]
    assert entry["test_files"] == ["tests/test_app.py"]
    assert entry["test_support_files"] == ["tests/conftest.py"]
    assert entry["degradation_targets"]["naming"]["target_files"] == [
        "src/app.py",
        "tests/conftest.py",
        "tests/test_app.py",
    ]


def test_write_deep_results_applies_navigation_depth_gate(tmp_path: Path):
    """Low-navigation tasks should not appear in the verified manifest."""
    candidates_dir = tmp_path / "candidates"
    output_dir = tmp_path / "deep_results"
    candidates_dir.mkdir()

    candidate_file = candidates_dir / "repo_pr_1.json"
    candidate_file.write_text(json.dumps({
        "candidate_id": "repo_pr_1",
        "base_commit_sha": "base123",
        "merge_commit_sha": "merge123",
        "head_commit_sha": "head123",
        "source_files": ["src/app.py"],
        "test_files": ["tests/test_app.py"],
        "test_support_files": [],
    }))

    config = Config(model="claude-opus-4-6")
    config._candidates_dir = candidates_dir

    write_deep_results(
        [_make_deep_result(navigation_depth=2)],
        "owner/repo",
        output_dir,
        config,
    )

    manifest = json.loads((output_dir / "repo_verified_manifest.json").read_text())
    assert manifest["llm_stage2_accepted"] == 1
    assert manifest["stage2_accepted"] == 0
    assert manifest["verified_prs"] == []


def test_write_deep_results_fails_when_candidate_metadata_missing(tmp_path: Path):
    """Missing candidate JSON should fail fast instead of writing a bad manifest."""
    output_dir = tmp_path / "deep_results"
    config = Config(model="claude-opus-4-6")
    config._candidates_dir = tmp_path / "missing_candidates"

    with pytest.raises(FileNotFoundError):
        write_deep_results([_make_deep_result()], "owner/repo", output_dir, config)


def test_write_deep_results_fails_when_required_fields_missing(tmp_path: Path):
    """Candidate metadata should include the fields downstream stages require."""
    candidates_dir = tmp_path / "candidates"
    output_dir = tmp_path / "deep_results"
    candidates_dir.mkdir()

    candidate_file = candidates_dir / "repo_pr_1.json"
    candidate_file.write_text(json.dumps({
        "candidate_id": "repo_pr_1",
        "merge_commit_sha": "merge123",
        "head_commit_sha": "head123",
        "source_files": ["src/app.py"],
        "test_files": ["tests/test_app.py"],
        "test_support_files": [],
    }))

    config = Config(model="claude-opus-4-6")
    config._candidates_dir = candidates_dir

    with pytest.raises(ValueError):
        write_deep_results([_make_deep_result()], "owner/repo", output_dir, config)
