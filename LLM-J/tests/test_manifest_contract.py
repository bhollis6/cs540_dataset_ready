"""Tests for the Stage 3 -> Stage 4 manifest handoff contract."""

import json
from pathlib import Path

import pytest

from src.config import Config
from src.evaluator.models import CriterionScore, EvaluationResult, JudgeResponse
from src.output.degradation_plan import build_stage4_handoff
from src.output.manifest import write_manifest


def test_build_stage4_handoff_emits_explicit_degradation_targets():
    handoff = build_stage4_handoff({
        "base_commit_sha": "base123",
        "env_commit_sha": "env123",
        "merge_commit_sha": "merge123",
        "head_commit_sha": "head123",
        "source_files": ["src/app.py"],
        "test_files": ["tests/test_app.py"],
        "test_support_files": ["tests/conftest.py", "tests/fixtures/example.json"],
    })

    assert handoff["source_files"] == ["src/app.py"]
    assert handoff["test_files"] == ["tests/test_app.py"]
    assert handoff["env_commit_sha"] == "env123"
    assert handoff["test_support_files"] == [
        "tests/conftest.py",
        "tests/fixtures/example.json",
    ]
    assert handoff["degradation_targets"]["type_hints"]["target_files"] == [
        "src/app.py",
        "tests/conftest.py",
        "tests/test_app.py",
    ]
    assert handoff["degradation_targets"]["remove_tests"] == {
        "delete_files": ["tests/test_app.py"],
        "preserve_files": ["tests/conftest.py", "tests/fixtures/example.json"],
    }


def test_build_stage4_handoff_rejects_overlapping_file_groups():
    with pytest.raises(ValueError, match="overlap"):
        build_stage4_handoff({
            "base_commit_sha": "base123",
            "env_commit_sha": "env123",
            "merge_commit_sha": "merge123",
            "head_commit_sha": "head123",
            "source_files": ["src/app.py", "tests/test_app.py"],
            "test_files": ["tests/test_app.py"],
            "test_support_files": [],
        })


def test_build_stage4_handoff_reclassifies_legacy_candidate_file_groups():
    handoff = build_stage4_handoff({
        "base_commit_sha": "base123",
        "env_commit_sha": "env123",
        "merge_commit_sha": "merge123",
        "head_commit_sha": "head123",
        "files_changed": [
            "httpx/_utils.py",
            "tests/test_utils.py",
            "tests/utils.py",
        ],
        "source_files": ["httpx/_utils.py"],
        "test_files": ["tests/test_utils.py", "tests/utils.py"],
        "test_support_files": [],
    })

    assert handoff["source_files"] == ["httpx/_utils.py"]
    assert handoff["test_files"] == ["tests/test_utils.py"]
    assert handoff["test_support_files"] == ["tests/utils.py"]
    assert handoff["degradation_targets"]["remove_tests"] == {
        "delete_files": ["tests/test_utils.py"],
        "preserve_files": ["tests/utils.py"],
    }


def test_write_manifest_emits_degradation_targets(tmp_path: Path):
    candidates_dir = tmp_path / "candidates"
    output_dir = tmp_path / "results"
    candidates_dir.mkdir()

    (candidates_dir / "repo_pr_1.json").write_text(json.dumps({
        "candidate_id": "repo_pr_1",
        "repo": "owner/repo",
        "pr_number": 1,
        "title": "Fix something",
        "description": "Fix bug with tests",
        "patch_diff": "diff --git a/src/app.py b/src/app.py",
        "test_diff": "diff --git a/tests/test_app.py b/tests/test_app.py",
        "files_changed": ["src/app.py", "tests/test_app.py", "tests/conftest.py"],
        "source_files": ["src/app.py"],
        "test_files": ["tests/test_app.py"],
        "test_support_files": ["tests/conftest.py", "tests/fixtures/example.json"],
        "lines_added": 10,
        "lines_removed": 2,
        "has_test_changes": True,
        "merge_commit_sha": "merge123",
        "base_commit_sha": "base123",
        "env_commit_sha": "env123",
        "head_commit_sha": "head123",
        "merged_at": "2026-04-21T00:00:00Z",
    }))

    result = EvaluationResult(
        candidate_id="repo_pr_1",
        repo="owner/repo",
        pr_number=1,
        response=JudgeResponse(
            scope=CriterionScore(4, "good scope"),
            test_coverage=CriterionScore(4, "good tests"),
            mutation_relevance=CriterionScore(4, "good mutation signal"),
            clarity=CriterionScore(4, "clear"),
            complexity=CriterionScore(3, "moderate"),
            total_score=19,
            recommendation="ACCEPT",
            summary="strong candidate",
        ),
        run_number=1,
        model="claude-opus-4-6",
        provider="anthropic",
        evaluated_at="2026-04-21T00:00:00Z",
    )

    config = Config(input_dir=candidates_dir, output_dir=output_dir, model="claude-opus-4-6")
    write_manifest([result], config)

    manifest = json.loads((output_dir / "repo_selected_prs.json").read_text())
    entry = manifest["selected_prs"][0]

    assert entry["env_commit_sha"] == "env123"
    assert entry["test_support_files"] == [
        "tests/conftest.py",
        "tests/fixtures/example.json",
    ]
    assert entry["degradation_targets"]["comments_docstrings"]["target_files"] == [
        "src/app.py",
        "tests/conftest.py",
        "tests/test_app.py",
    ]
    assert entry["degradation_targets"]["remove_tests"]["preserve_files"] == [
        "tests/conftest.py",
        "tests/fixtures/example.json",
    ]


def test_write_manifest_fails_when_candidate_file_missing(tmp_path: Path):
    output_dir = tmp_path / "results"
    config = Config(input_dir=tmp_path / "missing_candidates", output_dir=output_dir)

    result = EvaluationResult(
        candidate_id="repo_pr_1",
        repo="owner/repo",
        pr_number=1,
        response=JudgeResponse(
            scope=CriterionScore(4, "good scope"),
            test_coverage=CriterionScore(4, "good tests"),
            mutation_relevance=CriterionScore(4, "good mutation signal"),
            clarity=CriterionScore(4, "clear"),
            complexity=CriterionScore(3, "moderate"),
            total_score=19,
            recommendation="ACCEPT",
            summary="strong candidate",
        ),
        run_number=1,
        model="claude-opus-4-6",
        provider="anthropic",
        evaluated_at="2026-04-21T00:00:00Z",
    )

    with pytest.raises(FileNotFoundError):
        write_manifest([result], config)
