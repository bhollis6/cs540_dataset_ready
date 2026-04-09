"""Read full source files and extract first-degree import dependencies."""

from __future__ import annotations

import ast
from pathlib import Path


def read_source_files(worktree: Path, file_paths: list[str]) -> dict[str, str]:
    """Read full contents of specified files in the worktree.

    Returns {relative_path: contents}. Skips files that don't exist
    (they may have been added by the PR and don't exist at base_commit).
    """
    result: dict[str, str] = {}
    for fp in file_paths:
        full_path = worktree / fp
        if full_path.exists() and full_path.is_file():
            try:
                result[fp] = full_path.read_text(errors="replace")
            except OSError:
                pass
    return result


def extract_imports(content: str) -> list[str]:
    """Extract import module paths from Python source using AST parsing."""
    modules: list[str] = []
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return modules

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.append(node.module)

    return modules


def resolve_import_to_file(import_path: str, worktree: Path) -> Path | None:
    """Try to resolve a Python import path to a file in the worktree.

    Checks common layouts: src/<package>/, <package>/, flat modules.
    Returns None if the import is third-party (not found locally).
    """
    # Convert dots to path separators
    parts = import_path.split(".")

    # Try various path patterns
    candidates = [
        worktree / Path(*parts).with_suffix(".py"),
        worktree / Path(*parts) / "__init__.py",
        worktree / "src" / Path(*parts).with_suffix(".py"),
        worktree / "src" / Path(*parts) / "__init__.py",
    ]

    # Also try with just the top-level package
    if len(parts) > 1:
        candidates.extend([
            worktree / Path(*parts[:-1]) / f"{parts[-1]}.py",
            worktree / "src" / Path(*parts[:-1]) / f"{parts[-1]}.py",
        ])

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            try:
                return candidate.relative_to(worktree)
            except ValueError:
                return candidate

    return None


def collect_context_files(
    worktree: Path,
    source_files: list[str],
    max_chars: int | None = None,
) -> tuple[dict[str, str], dict[str, str], bool]:
    """Collect PR source files and their first-degree import dependencies.

    Returns:
        (source_contents, dependency_contents, was_truncated)
    """
    # Read the PR's source files
    source_contents = read_source_files(worktree, source_files)

    # Extract imports from each source file and resolve to local files
    dep_paths: set[str] = set()
    for content in source_contents.values():
        for module in extract_imports(content):
            resolved = resolve_import_to_file(module, worktree)
            if resolved:
                rel_path = str(resolved)
                if rel_path not in source_contents:
                    dep_paths.add(rel_path)

    # Read dependency files
    dep_contents = read_source_files(worktree, list(dep_paths))

    # Apply context budget if set
    truncated = False
    if max_chars is not None:
        total = (
            sum(len(v) for v in source_contents.values())
            + sum(len(v) for v in dep_contents.values())
        )
        if total > max_chars:
            # Source files always kept in full. Truncate deps largest-first.
            source_total = sum(len(v) for v in source_contents.values())
            remaining = max_chars - source_total

            if remaining <= 0:
                dep_contents = {}
                truncated = True
            else:
                # Sort deps by size descending, drop largest until under budget
                sorted_deps = sorted(dep_contents.items(), key=lambda x: len(x[1]), reverse=True)
                kept: dict[str, str] = {}
                used = 0
                for path, content in reversed(sorted_deps):  # smallest first
                    if used + len(content) <= remaining:
                        kept[path] = content
                        used += len(content)
                    else:
                        truncated = True
                dep_contents = kept

    return source_contents, dep_contents, truncated
