"""Scope-limited naming obfuscation for targeted pilot workspaces."""

from __future__ import annotations

import ast
import os
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Generator

from rope.base.exceptions import RefactoringError, ResourceNotFoundError
from rope.base.project import Project
from rope.refactor.rename import Rename


EXCLUDE_DIRS = {
    ".git",
    ".ropeproject",
    "venv",
    "env",
    ".venv",
    "__pycache__",
    ".tox",
    ".nox",
    "build",
    "dist",
    ".idea",
    ".vscode",
}
PROTECTED_NAMES = {
    "self",
    "cls",
    "True",
    "False",
    "None",
    "_",
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
    "g",
    "h",
    "i",
    "j",
    "k",
    "l",
    "m",
    "n",
    "o",
    "p",
    "q",
    "r",
    "s",
    "t",
    "u",
    "v",
    "w",
    "x",
    "y",
    "z",
    "char",
    "item",
    "key",
    "val",
    "value",
    "line",
    "row",
    "col",
    "elem",
    "entry",
    "chunk",
    "byte",
    "token",
    "part",
    "word",
    "pair",
    "match",
    "obj",
    "typ",
    "msg",
    "buf",
    "func",
    "callback",
    "handler",
    "fn",
    "cb",
    "setUp",
    "tearDown",
    "setUpClass",
    "tearDownClass",
    "asyncSetUp",
    "asyncTearDown",
    "setup_method",
    "teardown_method",
    "setup_class",
    "teardown_class",
    "setup_module",
    "teardown_module",
    "setup_function",
    "teardown_function",
}
PROTECTED_PREFIXES = ("pytest_",)


@dataclass(frozen=True)
class Symbol:
    name: str
    kind: str
    file_path: str
    offset: int


@dataclass
class RenameStats:
    classes: int = 0
    functions: int = 0
    variables: int = 0
    skipped: int = 0
    skipped_missing_resource: int = 0
    skipped_offset_not_found: int = 0
    skipped_refactoring_error: int = 0
    skipped_other_error: int = 0
    skip_name_counts: Counter[str] = field(default_factory=Counter)

    def total(self) -> int:
        return self.classes + self.functions + self.variables

    def record_skip(self, reason: str, name: str | None = None) -> None:
        self.skipped += 1
        if reason == "missing_resource":
            self.skipped_missing_resource += 1
        elif reason == "offset_not_found":
            self.skipped_offset_not_found += 1
        elif reason == "refactoring_error":
            self.skipped_refactoring_error += 1
        else:
            self.skipped_other_error += 1
        if name:
            self.skip_name_counts[name] += 1

    def to_dict(self, top_n: int = 15) -> dict[str, Any]:
        attempted = self.total() + self.skipped
        return {
            "renamed": {
                "classes": self.classes,
                "functions": self.functions,
                "variables": self.variables,
                "total": self.total(),
            },
            "skipped": {
                "total": self.skipped,
                "missing_resource": self.skipped_missing_resource,
                "offset_not_found": self.skipped_offset_not_found,
                "refactoring_error": self.skipped_refactoring_error,
                "other_error": self.skipped_other_error,
            },
            "rates": {
                "rename_success_rate": self.total() / attempted if attempted else 0.0,
                "offset_not_found_rate": (
                    self.skipped_offset_not_found / attempted if attempted else 0.0
                ),
                "refactoring_error_rate": (
                    self.skipped_refactoring_error / attempted if attempted else 0.0
                ),
            },
            "top_skipped_names": [
                {"name": name, "count": count}
                for name, count in self.skip_name_counts.most_common(top_n)
            ],
        }


def _is_protected(name: str) -> bool:
    if name in PROTECTED_NAMES:
        return True
    if any(name.startswith(prefix) for prefix in PROTECTED_PREFIXES):
        return True
    return name.startswith("__") and name.endswith("__")


def _is_executable_test_path(path: Path) -> bool:
    name = path.name.lower()
    return name.startswith("test_") or name.endswith("_test.py") or name == "tests.py"


def _is_preserved_test_support_path(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    return (
        path.name.lower() == "conftest.py"
        or "fixtures" in parts
        or "test_data" in parts
        or "__snapshots__" in parts
    )


def _decorator_name(decorator: ast.AST) -> str | None:
    if isinstance(decorator, ast.Name):
        return decorator.id
    if isinstance(decorator, ast.Attribute):
        return decorator.attr
    if isinstance(decorator, ast.Call):
        return _decorator_name(decorator.func)
    return None


def _iter_py_files(repo_path: Path) -> Generator[Path, None, None]:
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith("."))
        for filename in sorted(files):
            if filename.endswith(".py"):
                yield Path(root) / filename


def collect_forbidden(repo_path: Path) -> set[str]:
    forbidden: set[str] = set()
    for py_file in _iter_py_files(repo_path):
        forbidden.add(py_file.stem)
    for py_file in _iter_py_files(repo_path):
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(py_file))
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Nonlocal):
                forbidden.update(node.names)
            elif isinstance(node, ast.Global):
                forbidden.update(node.names)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    forbidden.add(alias.name.split(".")[0])
                    if alias.asname:
                        forbidden.add(alias.asname)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.asname:
                        forbidden.add(alias.asname)
                    elif isinstance(alias.name, str):
                        forbidden.add(alias.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__":
                        if isinstance(node.value, (ast.List, ast.Tuple)):
                            for element in node.value.elts:
                                if isinstance(element, ast.Constant) and isinstance(element.value, str):
                                    forbidden.add(element.value)
            elif isinstance(node, ast.Call):
                for keyword in node.keywords:
                    if keyword.arg is not None:
                        forbidden.add(keyword.arg)
    return forbidden


def _offset_from_linecol(source_bytes: bytes, lineno: int, col_offset: int) -> int | None:
    try:
        lines = source_bytes.split(b"\n")
        if lineno < 1 or lineno > len(lines):
            return None
        return sum(len(lines[index]) + 1 for index in range(lineno - 1)) + col_offset
    except Exception:
        return None


def _build_parent_map(tree: ast.Module) -> dict[int, ast.AST]:
    parent: dict[int, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parent[id(child)] = node
    return parent


def _enclosing_class(node: ast.AST, parent_map: dict[int, ast.AST]) -> ast.ClassDef | None:
    current = parent_map.get(id(node))
    while current is not None:
        if isinstance(current, ast.ClassDef):
            return current
        current = parent_map.get(id(current))
    return None


def _inside_class(node: ast.AST, parent_map: dict[int, ast.AST]) -> bool:
    return _enclosing_class(node, parent_map) is not None


def _inside_function(node: ast.AST, parent_map: dict[int, ast.AST]) -> bool:
    current = parent_map.get(id(node))
    while current is not None:
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return True
        current = parent_map.get(id(current))
    return False


def _is_pytest_fixture(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return any(_decorator_name(decorator) == "fixture" for decorator in node.decorator_list)


def _is_discovery_critical_test_class(
    node: ast.ClassDef,
    py_file: Path,
    parent_map: dict[int, ast.AST],
) -> bool:
    return _is_executable_test_path(py_file) and not _inside_class(node, parent_map) and node.name.startswith("Test")


def _is_discovery_critical_test_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    py_file: Path,
    parent_map: dict[int, ast.AST],
) -> bool:
    if _is_protected(node.name):
        return True
    if _is_executable_test_path(py_file) and node.name.startswith("test_"):
        return True
    if _is_preserved_test_support_path(py_file) and _is_pytest_fixture(node):
        return True
    enclosing_class = _enclosing_class(node, parent_map)
    if enclosing_class is not None and enclosing_class.name.startswith("Test"):
        return node.name.startswith("test_") or node.name in PROTECTED_NAMES
    return False


def _function_has_scope_hazards(func: ast.AST) -> bool:
    for node in ast.walk(func):
        if node is func:
            continue
        if isinstance(
            node,
            (
                ast.GeneratorExp,
                ast.ListComp,
                ast.SetComp,
                ast.DictComp,
                ast.Lambda,
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.Nonlocal,
                ast.Global,
            ),
        ):
            return True
    return False


def _collect_function_params(func: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    params: set[str] = set()
    all_args = list(func.args.args) + list(func.args.posonlyargs) + list(func.args.kwonlyargs)
    if func.args.vararg:
        all_args.append(func.args.vararg)
    if func.args.kwarg:
        all_args.append(func.args.kwarg)
    for arg in all_args:
        params.add(arg.arg)
    return params


def _iter_bound_names(target: ast.AST) -> Generator[tuple[str, int, int], None, None]:
    if isinstance(target, ast.Name):
        yield target.id, target.lineno, target.col_offset
    elif isinstance(target, (ast.Tuple, ast.List)):
        for element in target.elts:
            yield from _iter_bound_names(element)
    elif isinstance(target, ast.Starred):
        yield from _iter_bound_names(target.value)


def collect_symbols(repo_path: Path, forbidden: set[str]) -> list[Symbol]:
    symbols: list[Symbol] = []
    for py_file in _iter_py_files(repo_path):
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(py_file))
        except Exception:
            continue
        source_bytes = source.encode("utf-8")
        parent_map = _build_parent_map(tree)

        def skip(name: str) -> bool:
            return _is_protected(name) or name in forbidden

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if (
                    skip(node.name)
                    or _inside_class(node, parent_map)
                    or len(node.name) <= 1
                    or _is_discovery_critical_test_class(node, py_file, parent_map)
                ):
                    continue
                offset = _offset_from_linecol(source_bytes, node.lineno, node.col_offset)
                if offset is not None:
                    symbols.append(Symbol(node.name, "class", str(py_file), offset))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not (
                    node.name.startswith("__")
                    and node.name.endswith("__")
                    or skip(node.name)
                    or _is_discovery_critical_test_function(node, py_file, parent_map)
                    or _inside_function(node, parent_map)
                    or _function_has_scope_hazards(node)
                ):
                    offset = _offset_from_linecol(source_bytes, node.lineno, node.col_offset)
                    if offset is not None:
                        symbols.append(Symbol(node.name, "function", str(py_file), offset))

                if _inside_function(node, parent_map) or _function_has_scope_hazards(node):
                    continue
                params = _collect_function_params(node)
                except_names = {
                    child.name
                    for child in ast.walk(node)
                    if isinstance(child, ast.ExceptHandler) and child.name
                }
                for child in ast.walk(node):
                    if child is node or isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        continue
                    targets: list[ast.AST] = []
                    if isinstance(child, ast.Assign):
                        targets.extend(child.targets)
                    elif isinstance(child, ast.AnnAssign):
                        targets.append(child.target)
                    elif isinstance(child, ast.AugAssign):
                        targets.append(child.target)
                    elif isinstance(child, (ast.For, ast.AsyncFor)):
                        targets.append(child.target)
                    elif isinstance(child, ast.NamedExpr):
                        targets.append(child.target)
                    elif isinstance(child, (ast.With, ast.AsyncWith)):
                        targets.extend(item.optional_vars for item in child.items if item.optional_vars is not None)
                    for target in targets:
                        for name, line, col in _iter_bound_names(target):
                            if name in params or name in except_names or skip(name):
                                continue
                            offset = _offset_from_linecol(source_bytes, line, col)
                            if offset is not None:
                                symbols.append(Symbol(name, "variable", str(py_file), offset))
    return symbols


def dedupe_symbols(symbols: list[Symbol]) -> list[Symbol]:
    seen: set[str] = set()
    unique: list[Symbol] = []
    for symbol in symbols:
        key = f"{symbol.kind}::{symbol.file_path}::{symbol.offset}"
        if key in seen:
            continue
        seen.add(key)
        unique.append(symbol)
    unique.sort(key=lambda symbol: (symbol.file_path, symbol.offset, symbol.kind, symbol.name))
    return unique


def _new_name(kind: str, counter: dict[str, int]) -> str:
    value = counter[kind]
    counter[kind] += 1
    if kind == "class":
        return f"Cls{value}"
    if kind == "function":
        return f"fn{value}"
    return f"v{value}"


def _find_near(source: str, name: str, offset: int) -> int | None:
    window = 400
    start = max(0, offset - window)
    end = min(len(source), offset + len(name) + window)
    region = source[start:end]

    def is_identifier_match(abs_index: int) -> bool:
        before = source[abs_index - 1] if abs_index > 0 else " "
        after = source[abs_index + len(name)] if abs_index + len(name) < len(source) else " "
        return not (before.isalnum() or before == "_") and not (after.isalnum() or after == "_")

    matches: list[int] = []
    index = 0
    while True:
        found = region.find(name, index)
        if found == -1:
            break
        absolute = start + found
        if is_identifier_match(absolute):
            matches.append(absolute)
        index = found + 1
    if matches:
        return min(matches, key=lambda found: abs(found - offset))

    matches = []
    index = 0
    while True:
        found = source.find(name, index)
        if found == -1:
            break
        if is_identifier_match(found):
            matches.append(found)
        index = found + 1
    if matches:
        return min(matches, key=lambda found: abs(found - offset))
    return None


def collect_naming_audit(repo_path: Path, target_files: set[str] | None = None) -> dict[str, Any]:
    repo = repo_path.resolve()
    forbidden = collect_forbidden(repo)
    symbols = dedupe_symbols(collect_symbols(repo, forbidden))
    if target_files is not None:
        normalized = {path.replace("\\", "/") for path in target_files}
        symbols = [
            symbol
            for symbol in symbols
            if Path(symbol.file_path).resolve().relative_to(repo).as_posix() in normalized
        ]
    counts = Counter(symbol.kind for symbol in symbols)
    return {
        "candidate_symbol_count": len(symbols),
        "rename_counts": {
            "classes": counts.get("class", 0),
            "functions": counts.get("function", 0),
            "variables": counts.get("variable", 0),
            "total": len(symbols),
        },
        "sample_symbols": [
            {
                "name": symbol.name,
                "kind": symbol.kind,
                "path": Path(symbol.file_path).resolve().relative_to(repo).as_posix(),
            }
            for symbol in symbols[:20]
        ],
    }


def obfuscate_targets(repo_path: Path, target_files: set[str]) -> tuple[RenameStats, int]:
    repo = repo_path.resolve()
    normalized_targets = {path.replace("\\", "/") for path in target_files}
    forbidden = collect_forbidden(repo)
    symbols = [
        symbol
        for symbol in dedupe_symbols(collect_symbols(repo, forbidden))
        if Path(symbol.file_path).resolve().relative_to(repo).as_posix() in normalized_targets
    ]

    project = Project(str(repo), ropefolder=None)
    project.prefs["ignored_resources"] = list(EXCLUDE_DIRS)
    stats = RenameStats()
    counter = {"class": 0, "function": 0, "variable": 0}
    used: set[str] = set()
    try:
        for symbol in symbols:
            new_name = _new_name(symbol.kind, counter)
            while new_name in used:
                new_name = _new_name(symbol.kind, counter)
            used.add(new_name)
            try:
                relative_path = Path(symbol.file_path).resolve().relative_to(repo)
                resource = project.get_resource(relative_path.as_posix())
            except (ResourceNotFoundError, ValueError):
                stats.record_skip("missing_resource", symbol.name)
                continue
            offset = _find_near(resource.read(), symbol.name, symbol.offset)
            if offset is None:
                stats.record_skip("offset_not_found", symbol.name)
                continue
            try:
                changes = Rename(project, resource, offset).get_changes(new_name)
                project.do(changes)
                if symbol.kind == "class":
                    stats.classes += 1
                elif symbol.kind == "function":
                    stats.functions += 1
                else:
                    stats.variables += 1
            except RefactoringError:
                stats.record_skip("refactoring_error", symbol.name)
            except Exception:
                stats.record_skip("other_error", symbol.name)
    finally:
        project.close()
    return stats, len(symbols)
