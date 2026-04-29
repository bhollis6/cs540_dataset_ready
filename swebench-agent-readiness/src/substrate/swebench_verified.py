"""Helpers for loading and normalizing official SWE-bench Verified tasks."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from swebench.harness.constants import KEY_INSTANCE_ID
from swebench.harness.utils import load_swebench_dataset
from unidiff import PatchSet


DEFAULT_DATASET_NAME = "SWE-bench/SWE-bench_Verified"
DEFAULT_SPLIT = "test"


def _parse_test_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return list(json.loads(value))
    return list(value)


def extract_changed_files(patch_text: str) -> list[str]:
    """Extract changed file paths from a unified diff string."""

    return [patched_file.path for patched_file in PatchSet(patch_text)]


@dataclass(frozen=True)
class TaskSnapshot:
    """Small local snapshot of one official SWE-bench task."""

    schema_version: str
    dataset_name: str
    dataset_split: str
    instance_id: str
    repo: str
    base_commit: str
    version: str | None
    problem_statement: str
    hints_text: str | None
    source_files: list[str]
    test_files: list[str]
    fail_to_pass: list[str]
    pass_to_pass: list[str]
    patch: str
    test_patch: str
    environment_setup_commit: str | None = None
    created_at: str | None = None
    difficulty: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "schema_version": self.schema_version,
            "dataset_name": self.dataset_name,
            "dataset_split": self.dataset_split,
            "instance_id": self.instance_id,
            "repo": self.repo,
            "base_commit": self.base_commit,
            "version": self.version,
            "problem_statement": self.problem_statement,
            "hints_text": self.hints_text,
            "source_files": list(self.source_files),
            "test_files": list(self.test_files),
            "fail_to_pass": list(self.fail_to_pass),
            "pass_to_pass": list(self.pass_to_pass),
            "patch": self.patch,
            "test_patch": self.test_patch,
        }
        if self.environment_setup_commit is not None:
            payload["environment_setup_commit"] = self.environment_setup_commit
        if self.created_at is not None:
            payload["created_at"] = self.created_at
        if self.difficulty is not None:
            payload["difficulty"] = self.difficulty
        return payload

    def to_swebench_instance(self) -> dict[str, Any]:
        """Render the snapshot back into the key shape expected by TestSpec."""

        payload = {
            KEY_INSTANCE_ID: self.instance_id,
            "repo": self.repo,
            "base_commit": self.base_commit,
            "version": self.version,
            "problem_statement": self.problem_statement,
            "hints_text": self.hints_text,
            "patch": self.patch,
            "test_patch": self.test_patch,
            "FAIL_TO_PASS": list(self.fail_to_pass),
            "PASS_TO_PASS": list(self.pass_to_pass),
        }
        if self.environment_setup_commit is not None:
            payload["environment_setup_commit"] = self.environment_setup_commit
        if self.created_at is not None:
            payload["created_at"] = self.created_at
        if self.difficulty is not None:
            payload["difficulty"] = self.difficulty
        return payload


def fetch_task_snapshot(
    instance_id: str,
    *,
    dataset_name: str = DEFAULT_DATASET_NAME,
    dataset_split: str = DEFAULT_SPLIT,
) -> TaskSnapshot:
    """Fetch one task from the official SWE-bench dataset and normalize it."""

    row = load_swebench_dataset(dataset_name, dataset_split, [instance_id])[0]
    return TaskSnapshot(
        schema_version="0.1.0",
        dataset_name=dataset_name,
        dataset_split=dataset_split,
        instance_id=row[KEY_INSTANCE_ID],
        repo=row["repo"],
        base_commit=row["base_commit"],
        version=row.get("version"),
        problem_statement=row["problem_statement"],
        hints_text=row.get("hints_text"),
        source_files=extract_changed_files(row["patch"]),
        test_files=extract_changed_files(row["test_patch"]),
        fail_to_pass=_parse_test_list(row.get("FAIL_TO_PASS")),
        pass_to_pass=_parse_test_list(row.get("PASS_TO_PASS")),
        patch=row["patch"],
        test_patch=row["test_patch"],
        environment_setup_commit=row.get("environment_setup_commit"),
        created_at=row.get("created_at"),
        difficulty=row.get("difficulty"),
    )


def write_task_snapshot(snapshot: TaskSnapshot, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(snapshot.to_dict(), handle, indent=2)
    return path
