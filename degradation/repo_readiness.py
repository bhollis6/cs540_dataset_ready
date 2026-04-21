from __future__ import annotations

import ast
import io
import json
import tokenize
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from naming_conventions import collect_naming_audit

EXCLUDE_DIRS = {
    ".git", ".ropeproject", "venv", "env", ".venv",
    "__pycache__", ".tox", ".nox", "build", "dist",
    ".idea", ".vscode",
}

PYTEST_CONFIG_FILES = {
    "pytest.ini",
    "conftest.py",
    "pyproject.toml",
    "tox.ini",
    "setup.cfg",
}

REMOVABLE_TEST_PATTERNS = (
    "test_*.py",
    "*_test.py",
    "tests.py",
)

TEST_SUPPORT_DIRS = {"fixtures", "test_data", "__snapshots__"}


def collect_repo_readiness(repo_path: str | Path, sample_limit: int = 10) -> dict[str, Any]:
    path = Path(repo_path).resolve()
    if not path.is_dir():
        raise ValueError(f"Not a directory: {path}")

    python_files = list(_iter_py_files(path))
    type_hint_metrics = _collect_type_hint_metrics(python_files)
    comments_metrics = _collect_comments_docstrings_metrics(python_files)
    test_surface_metrics = _collect_test_surface_metrics(path)
    naming_metrics = collect_naming_audit(path, sample_limit=sample_limit)

    readiness = {
        "type_hints": _assess_type_hint_readiness(type_hint_metrics),
        "comments_docstrings": _assess_comments_readiness(comments_metrics),
        "remove_tests": _assess_remove_tests_readiness(test_surface_metrics),
        "naming": _assess_naming_readiness(naming_metrics),
    }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_path": str(path),
        "python_file_count": len(python_files),
        "type_hints": type_hint_metrics,
        "comments_docstrings": comments_metrics,
        "test_surface": test_surface_metrics,
        "naming": naming_metrics,
        "readiness": readiness,
        "overall": _summarize_overall(readiness),
    }


def _iter_py_files(repo_path: Path) -> list[Path]:
    files: list[Path] = []
    for path in repo_path.rglob("*.py"):
        if not path.is_file():
            continue
        relative_parts = path.relative_to(repo_path).parts[:-1]
        if any(part in EXCLUDE_DIRS or part.startswith(".") for part in relative_parts):
            continue
        files.append(path)
    return sorted(files)


def _collect_type_hint_metrics(python_files: list[Path]) -> dict[str, Any]:
    functions_total = 0
    functions_with_any_annotation = 0
    param_annotations = 0
    return_annotations = 0
    annotated_assignments = 0
    files_with_annotations = 0

    for file_path in python_files:
        try:
            tree = ast.parse(file_path.read_text(encoding="utf-8"))
        except Exception:
            continue

        file_has_annotations = False
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions_total += 1
                has_annotation = False
                args = (
                    list(node.args.posonlyargs)
                    + list(node.args.args)
                    + list(node.args.kwonlyargs)
                )
                if node.args.vararg:
                    args.append(node.args.vararg)
                if node.args.kwarg:
                    args.append(node.args.kwarg)
                for arg in args:
                    if arg.annotation is not None:
                        param_annotations += 1
                        has_annotation = True
                        file_has_annotations = True
                if node.returns is not None:
                    return_annotations += 1
                    has_annotation = True
                    file_has_annotations = True
                if has_annotation:
                    functions_with_any_annotation += 1
            elif isinstance(node, ast.AnnAssign):
                annotated_assignments += 1
                file_has_annotations = True

        if file_has_annotations:
            files_with_annotations += 1

    total_annotations = param_annotations + return_annotations + annotated_assignments
    return {
        "files_with_annotations": files_with_annotations,
        "functions_total": functions_total,
        "functions_with_any_annotation": functions_with_any_annotation,
        "annotated_function_ratio": (
            functions_with_any_annotation / functions_total if functions_total else 0.0
        ),
        "param_annotations": param_annotations,
        "return_annotations": return_annotations,
        "annotated_assignments": annotated_assignments,
        "total_annotations": total_annotations,
    }


def _collect_comments_docstrings_metrics(python_files: list[Path]) -> dict[str, Any]:
    comment_count = 0
    docstring_count = 0
    files_with_signal = 0
    files_with_comments = 0
    files_with_docstrings = 0

    for file_path in python_files:
        try:
            source = file_path.read_text(encoding="utf-8")
        except Exception:
            continue

        file_comment_count = 0
        try:
            tokens = tokenize.generate_tokens(io.StringIO(source).readline)
            for token in tokens:
                if token.type == tokenize.COMMENT:
                    file_comment_count += 1
        except Exception:
            pass

        file_docstring_count = 0
        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(
                    node,
                    (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
                ) and ast.get_docstring(node) is not None:
                    file_docstring_count += 1
        except Exception:
            pass

        comment_count += file_comment_count
        docstring_count += file_docstring_count
        if file_comment_count:
            files_with_comments += 1
        if file_docstring_count:
            files_with_docstrings += 1
        if file_comment_count or file_docstring_count:
            files_with_signal += 1

    return {
        "comment_count": comment_count,
        "docstring_count": docstring_count,
        "total_signal_count": comment_count + docstring_count,
        "files_with_comments": files_with_comments,
        "files_with_docstrings": files_with_docstrings,
        "files_with_signal": files_with_signal,
    }


def _collect_test_surface_metrics(repo_path: Path) -> dict[str, Any]:
    executable_test_files: list[str] = []
    test_support_files: list[str] = []
    pytest_config_files: list[str] = []

    for path in repo_path.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(repo_path)
        parts = relative.parts[:-1]
        if any(part in EXCLUDE_DIRS or part.startswith(".") for part in parts):
            continue

        relative_str = relative.as_posix()
        if path.name in PYTEST_CONFIG_FILES:
            pytest_config_files.append(relative_str)
        if _is_executable_test_path(relative):
            executable_test_files.append(relative_str)
        elif _is_test_support_path(relative):
            test_support_files.append(relative_str)

    return {
        "executable_test_file_count": len(executable_test_files),
        "test_support_file_count": len(test_support_files),
        "pytest_config_count": len(sorted(set(pytest_config_files))),
        "executable_test_files_sample": sorted(executable_test_files)[:10],
        "test_support_files_sample": sorted(test_support_files)[:10],
        "pytest_config_files": sorted(set(pytest_config_files)),
    }


def _is_executable_test_path(path: Path) -> bool:
    return any(path.match(pattern) for pattern in REMOVABLE_TEST_PATTERNS)


def _is_test_support_path(path: Path) -> bool:
    parts = [part.lower() for part in path.parts]
    filename = parts[-1] if parts else ""
    if filename == "conftest.py":
        return True
    if any(part in TEST_SUPPORT_DIRS for part in parts):
        return True
    if any(part in {"tests", "test", "testing"} for part in parts[:-1]):
        return not _is_executable_test_path(path)
    return False


def _assess_type_hint_readiness(metrics: dict[str, Any]) -> dict[str, Any]:
    total = metrics["total_annotations"]
    ratio = metrics["annotated_function_ratio"]
    if total == 0:
        return _status("FAIL", "No type-hint surface detected for this degradation.")
    if total >= 50 and ratio >= 0.30:
        return _status("PASS", "Type-hint surface is strong enough for meaningful degradation.")
    return _status("REVIEW", "Type-hint surface exists but may be too sparse for a strong condition.")


def _assess_comments_readiness(metrics: dict[str, Any]) -> dict[str, Any]:
    total = metrics["total_signal_count"]
    files = metrics["files_with_signal"]
    if total == 0:
        return _status("FAIL", "No comment/docstring surface detected for this degradation.")
    if total >= 30 and files >= 5:
        return _status("PASS", "Comment/docstring surface is broad enough for meaningful degradation.")
    return _status("REVIEW", "Comment/docstring surface exists but looks uneven or sparse.")


def _assess_remove_tests_readiness(metrics: dict[str, Any]) -> dict[str, Any]:
    test_files = metrics["executable_test_file_count"]
    support_files = metrics["test_support_file_count"]
    config_files = metrics["pytest_config_count"]
    if test_files == 0:
        return _status("FAIL", "No removable executable tests were found.")
    if test_files >= 5 and (support_files > 0 or config_files > 0):
        return _status("PASS", "Test removal has enough executable tests and preserved infrastructure.")
    return _status("REVIEW", "Executable tests exist, but preserved support/config surface is limited.")


def _assess_naming_readiness(metrics: dict[str, Any]) -> dict[str, Any]:
    total = metrics["rename_counts"]["total"]
    files = metrics["files_with_renames"]
    if total == 0:
        return _status("FAIL", "No renamable naming surface detected.")
    if total >= 200 and files >= 10:
        return _status("PASS", "Naming surface is broad enough to justify the condition.")
    return _status("REVIEW", "Naming surface exists but may be weak for repo-level degradation.")


def _status(status: str, reason: str) -> dict[str, str]:
    return {"status": status, "reason": reason}


def _summarize_overall(readiness: dict[str, dict[str, str]]) -> dict[str, Any]:
    counts = Counter(item["status"] for item in readiness.values())
    if counts["FAIL"] > 0:
        status = "REVIEW"
        reason = "At least one degradation condition currently looks unsuitable."
    elif counts["REVIEW"] > 0:
        status = "REVIEW"
        reason = "Repo has usable surface area, but one or more conditions need human review."
    else:
        status = "PASS"
        reason = "All current degradation surfaces look viable at the static-screen level."
    return {
        "status": status,
        "reason": reason,
        "counts": dict(counts),
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate a structured static readiness report for repo degradations."
    )
    parser.add_argument("repo_path")
    parser.add_argument("--sample-limit", type=int, default=10)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    report = collect_repo_readiness(args.repo_path, sample_limit=args.sample_limit)
    payload = json.dumps(report, indent=2)
    if args.output is None:
        print(payload)
    else:
        args.output.write_text(payload + "\n", encoding="utf-8")
        print(f"Wrote repo readiness to {args.output}")


if __name__ == "__main__":
    main()
