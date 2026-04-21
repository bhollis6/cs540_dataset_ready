"""Validated Stage 3 -> Stage 4 handoff helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.scraper.models import (
    _is_executable_test_file,
    _is_test_related_file,
    _is_test_support_file,
)

REQUIRED_CANDIDATE_FIELDS = (
    "base_commit_sha",
    "merge_commit_sha",
    "head_commit_sha",
    "source_files",
    "test_files",
)


def load_candidate_handoff(candidate_file: Path) -> dict[str, Any]:
    """Load and validate the candidate metadata required by downstream stages."""
    if not candidate_file.exists():
        raise FileNotFoundError(
            f"Candidate file required for manifest handoff not found: {candidate_file}"
        )

    with open(candidate_file) as f:
        candidate_data = json.load(f)

    missing = [key for key in REQUIRED_CANDIDATE_FIELDS if key not in candidate_data]
    if missing:
        raise ValueError(
            f"Candidate {candidate_data.get('candidate_id', candidate_file.stem)} "
            f"missing required manifest fields: {', '.join(missing)}"
        )

    return candidate_data


def build_stage4_handoff(candidate_data: Mapping[str, Any]) -> dict[str, Any]:
    """Build a validated Stage 4 handoff with explicit degradation targets."""
    source_files = _normalize_paths(candidate_data.get("source_files", []))
    test_files = _normalize_paths(candidate_data.get("test_files", []))
    test_support_files = _normalize_paths(candidate_data.get("test_support_files", []))

    _validate_file_groups(
        source_files=source_files,
        test_files=test_files,
        test_support_files=test_support_files,
    )

    python_test_support_files = [
        path for path in test_support_files if path.lower().endswith(".py")
    ]
    python_signal_targets = sorted([
        *source_files,
        *test_files,
        *python_test_support_files,
    ])

    return {
        "merge_commit_sha": candidate_data.get("merge_commit_sha"),
        "base_commit_sha": candidate_data.get("base_commit_sha"),
        "head_commit_sha": candidate_data.get("head_commit_sha"),
        "source_files": source_files,
        "test_files": test_files,
        "test_support_files": test_support_files,
        "degradation_targets": {
            "type_hints": {"target_files": python_signal_targets},
            "naming": {"target_files": python_signal_targets},
            "comments_docstrings": {"target_files": python_signal_targets},
            "remove_tests": {
                "delete_files": test_files,
                "preserve_files": test_support_files,
            },
        },
    }


def _normalize_paths(paths: Any) -> list[str]:
    if paths is None:
        return []
    if not isinstance(paths, list):
        raise ValueError(f"Manifest file groups must be lists, got {type(paths).__name__}")

    normalized: list[str] = []
    seen: set[str] = set()
    for raw_path in paths:
        path = str(raw_path).strip().replace("\\", "/")
        if not path:
            raise ValueError("Manifest file groups cannot contain empty paths")
        if path in seen:
            continue
        seen.add(path)
        normalized.append(path)
    return sorted(normalized)


def _validate_file_groups(
    *,
    source_files: list[str],
    test_files: list[str],
    test_support_files: list[str],
) -> None:
    overlaps = (
        ("source_files", "test_files", sorted(set(source_files) & set(test_files))),
        (
            "source_files",
            "test_support_files",
            sorted(set(source_files) & set(test_support_files)),
        ),
        (
            "test_files",
            "test_support_files",
            sorted(set(test_files) & set(test_support_files)),
        ),
    )
    for left, right, shared in overlaps:
        if shared:
            raise ValueError(
                f"Manifest file groups overlap between {left} and {right}: {', '.join(shared)}"
            )

    invalid_sources = [path for path in source_files if _is_test_related_file(path)]
    if invalid_sources:
        raise ValueError(
            "source_files contains test-related paths: "
            + ", ".join(sorted(invalid_sources))
        )

    invalid_tests = [path for path in test_files if not _is_executable_test_file(path)]
    if invalid_tests:
        raise ValueError(
            "test_files contains non-removable paths: "
            + ", ".join(sorted(invalid_tests))
        )

    invalid_support = [path for path in test_support_files if not _is_test_support_file(path)]
    if invalid_support:
        raise ValueError(
            "test_support_files contains non-support paths: "
            + ", ".join(sorted(invalid_support))
        )
