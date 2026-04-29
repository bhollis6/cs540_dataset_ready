"""Data models for scraped PR metadata and candidates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PRMetadata:
    """Raw PR metadata from GitHub GraphQL API. Used for pre-filtering."""

    pr_number: int
    title: str
    body: str
    additions: int
    deletions: int
    changed_files_count: int
    file_paths: list[str]
    merge_commit_sha: str | None
    base_commit_sha: str | None
    head_commit_sha: str | None
    merged_at: str | None
    author_login: str | None = None
    is_bot: bool = False

    @property
    def total_lines_changed(self) -> int:
        return self.additions + self.deletions

    @property
    def test_files(self) -> list[str]:
        return [p for p in self.file_paths if _is_executable_test_file(p)]

    @property
    def test_support_files(self) -> list[str]:
        return [p for p in self.file_paths if _is_test_support_file(p)]

    @property
    def source_files(self) -> list[str]:
        return [
            p for p in self.file_paths
            if not _is_test_related_file(p) and not _is_non_code_file(p)
        ]

    @property
    def has_test_changes(self) -> bool:
        return len(self.test_files) > 0 or len(self.test_support_files) > 0

    @property
    def has_source_changes(self) -> bool:
        return len(self.source_files) > 0


@dataclass
class CandidatePR:
    """Enriched PR candidate with diff content, ready for LLM evaluation and JSON serialization."""

    candidate_id: str
    repo: str
    pr_number: int
    title: str
    description: str
    patch_diff: str
    test_diff: str
    files_changed: list[str]
    source_files: list[str]
    test_files: list[str]
    test_support_files: list[str]
    lines_added: int
    lines_removed: int
    has_test_changes: bool
    merge_commit_sha: str | None
    base_commit_sha: str | None
    env_commit_sha: str | None
    head_commit_sha: str | None
    merged_at: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "repo": self.repo,
            "pr_number": self.pr_number,
            "title": self.title,
            "description": self.description,
            "patch_diff": self.patch_diff,
            "test_diff": self.test_diff,
            "files_changed": self.files_changed,
            "source_files": self.source_files,
            "test_files": self.test_files,
            "test_support_files": self.test_support_files,
            "lines_added": self.lines_added,
            "lines_removed": self.lines_removed,
            "has_test_changes": self.has_test_changes,
            "merge_commit_sha": self.merge_commit_sha,
            "base_commit_sha": self.base_commit_sha,
            "env_commit_sha": self.env_commit_sha,
            "head_commit_sha": self.head_commit_sha,
            "merged_at": self.merged_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CandidatePR:
        return cls(
            candidate_id=data["candidate_id"],
            repo=data["repo"],
            pr_number=data["pr_number"],
            title=data["title"],
            description=data["description"],
            patch_diff=data["patch_diff"],
            test_diff=data["test_diff"],
            files_changed=data["files_changed"],
            source_files=data.get("source_files", []),
            test_files=data.get("test_files", []),
            test_support_files=data.get("test_support_files", []),
            lines_added=data["lines_added"],
            lines_removed=data["lines_removed"],
            has_test_changes=data["has_test_changes"],
            merge_commit_sha=data.get("merge_commit_sha"),
            base_commit_sha=data.get("base_commit_sha"),
            env_commit_sha=data.get("env_commit_sha", data.get("base_commit_sha")),
            head_commit_sha=data.get("head_commit_sha"),
            merged_at=data.get("merged_at"),
        )


def _is_test_dir_path(path: str) -> bool:
    path_lower = path.lower()
    return (
        "tests/" in path_lower
        or "test/" in path_lower
        or "testing/" in path_lower
    )


def _is_executable_test_file(path: str) -> bool:
    """Check if a file path is a removable/executable test file."""
    parts = path.lower().split("/")
    filename = parts[-1] if parts else ""
    return (
        filename.startswith("test_")
        or filename.endswith("_test.py")
        or filename == "tests.py"
    )


def _is_test_support_file(path: str) -> bool:
    """Check if a path is test infrastructure that should be preserved."""
    parts = [part.lower() for part in path.split("/")]
    filename = parts[-1] if parts else ""
    support_dirs = {"fixtures", "test_data", "__snapshots__"}

    if filename == "conftest.py":
        return True
    if any(part in support_dirs for part in parts):
        return True
    if _is_test_dir_path(path) and not _is_executable_test_file(path):
        return True
    return False


def _is_test_related_file(path: str) -> bool:
    return _is_executable_test_file(path) or _is_test_support_file(path)


def _is_test_file(path: str) -> bool:
    """Backward-compatible alias for any test-related path."""
    return _is_test_related_file(path)


def _is_non_code_file(path: str) -> bool:
    """Check if a file is docs, CI, config, or other non-code."""
    path_lower = path.lower()
    filename = path_lower.split("/")[-1] if "/" in path_lower else path_lower

    non_code_patterns = [
        ".md", ".rst", ".txt", ".yml", ".yaml", ".toml", ".cfg", ".ini",
        ".json",  # usually config
        "dockerfile", ".dockerignore",
        "makefile",
        "license", "licence",
        ".gitignore", ".gitattributes",
    ]
    non_code_dirs = [
        "docs/", "doc/", ".github/", ".circleci/", ".gitlab/",
    ]

    if any(path_lower.startswith(d) or f"/{d}" in path_lower for d in non_code_dirs):
        return True
    if any(filename.endswith(p) or filename == p for p in non_code_patterns):
        return True
    return False
