from __future__ import annotations

import ast
import os
import shutil
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Generator

# ── Config ────────────────────────────────────────────────────────────────────

EXCLUDE_DIRS: set[str] = {
    ".git", ".ropeproject", "venv", "env", ".venv",
    "__pycache__", ".tox", ".nox", "build", "dist",
    ".idea", ".vscode",
}

# Single-letter and common callback/loop names that cause scope issues
PROTECTED_NAMES: set[str] = {
    "self", "cls", "True", "False", "None", "_",
    # Single letters — no semantic signal, often used as callables
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k",
    "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v",
    "w", "x", "y", "z",
    # Common loop / iteration variables used in generator expressions
    "char", "item", "key", "val", "value", "line", "row", "col",
    "elem", "entry", "chunk", "byte", "token", "part", "word",
    "pair", "match", "obj", "typ", "msg", "buf",
    # Common names for passed-around arguments / callables
    "func", "callback", "handler", "fn", "cb",
    # Test lifecycle hooks that must keep their framework-visible names
    "setUp", "tearDown", "setUpClass", "tearDownClass",
    "asyncSetUp", "asyncTearDown",
    "setup_method", "teardown_method",
    "setup_class", "teardown_class",
    "setup_module", "teardown_module",
    "setup_function", "teardown_function",
}

PROTECTED_PREFIXES: tuple[str, ...] = ("pytest_",)


def _is_protected(name: str) -> bool:
    if name in PROTECTED_NAMES:
        return True
    if any(name.startswith(prefix) for prefix in PROTECTED_PREFIXES):
        return True
    if name.startswith("__") and name.endswith("__"):
        return True
    return False


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


# ── File discovery ────────────────────────────────────────────────────────────

def _iter_py_files(repo_path: Path) -> Generator[Path, None, None]:
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = sorted([
            d for d in dirs
            if d not in EXCLUDE_DIRS and not d.startswith(".")
        ])
        for fname in sorted(files):
            if fname.endswith(".py"):
                yield Path(root) / fname


# ── Collect forbidden names ───────────────────────────────────────────────────

def _collect_forbidden(repo_path: Path) -> set[str]:
    """
    Names that cannot be safely renamed anywhere in the repo:
      - nonlocal / global declarations
      - names in __all__
      - import names (module names and aliases)
      - names used as keyword argument keys in any call
      - names matching a Python filename (rope would rename the file)
    """
    forbidden: set[str] = set()

    # Filenames
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
                if not isinstance(node.names, list):
                    continue
                for alias in node.names:
                    if alias.asname:
                        forbidden.add(alias.asname)
                    elif isinstance(alias.name, str):
                        forbidden.add(alias.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__":
                        val = node.value
                        if isinstance(val, (ast.List, ast.Tuple)):
                            for el in val.elts:
                                if isinstance(el, ast.Constant) and isinstance(el.value, str):
                                    forbidden.add(el.value)
            elif isinstance(node, ast.Call):
                for kw in node.keywords:
                    if kw.arg is not None:
                        forbidden.add(kw.arg)

    return forbidden


# ── Symbol collection (narrow scope) ──────────────────────────────────────────

@dataclass
class Symbol:
    name: str
    kind: str          # "class" | "function" | "variable"
    file_path: str
    offset: int        # byte offset of the definition


def _offset_from_linecol(source_bytes: bytes, lineno: int, col_offset: int) -> int | None:
    try:
        lines = source_bytes.split(b"\n")
        if lineno < 1 or lineno > len(lines):
            return None
        return sum(len(lines[i]) + 1 for i in range(lineno - 1)) + col_offset
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
    """True if node is inside a class (possibly through method boundary)."""
    return _enclosing_class(node, parent_map) is not None


def _inside_function(node: ast.AST, parent_map: dict[int, ast.AST]) -> bool:
    current = parent_map.get(id(node))
    while current is not None:
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return True
        current = parent_map.get(id(current))
    return False


def _is_discovery_critical_test_class(
    node: ast.ClassDef,
    py_file: Path,
    parent_map: dict[int, ast.AST],
) -> bool:
    return (
        _is_executable_test_path(py_file)
        and not _inside_class(node, parent_map)
        and node.name.startswith("Test")
    )


def _is_pytest_fixture(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for decorator in node.decorator_list:
        if _decorator_name(decorator) == "fixture":
            return True
    return False


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
        if node.name.startswith("test_") or node.name in PROTECTED_NAMES:
            return True

    return False


def _function_has_scope_hazards(func: ast.AST) -> bool:
    """
    Skip any function that contains constructs where rope's rename
    would cross a scope boundary and break runtime behavior.
    """
    for node in ast.walk(func):
        if node is func:
            continue
        if isinstance(node, (
            ast.GeneratorExp, ast.ListComp, ast.SetComp, ast.DictComp,
            ast.Lambda,
            ast.FunctionDef, ast.AsyncFunctionDef,
            ast.Nonlocal, ast.Global,
        )):
            return True
    return False


def _collect_function_params(func: ast.AST) -> set[str]:
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
        return
    if isinstance(target, (ast.Tuple, ast.List)):
        for element in target.elts:
            yield from _iter_bound_names(element)
        return
    if isinstance(target, ast.Starred):
        yield from _iter_bound_names(target.value)


def _collect_symbols(repo_path: Path, forbidden: set[str]) -> list[Symbol]:
    """
    Scope-limited but repo-wide:
      1. Classes not exported via __all__ and not inside any class
      2. Non-dunder functions and methods with no scope hazards,
         excluding test-discovery/framework hook names
      3. Local variables inside safe functions/methods, including
         assignment targets, loop targets, with-as bindings, and walrus
         bindings, excluding parameters and except vars
    """
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
            # ── Classes ────────────────────────────────────────────────
            if isinstance(node, ast.ClassDef):
                if skip(node.name):
                    continue
                if _inside_class(node, parent_map):
                    continue
                if len(node.name) <= 1:
                    continue
                if _is_discovery_critical_test_class(node, py_file, parent_map):
                    continue
                offset = _offset_from_linecol(
                    source_bytes, node.lineno, node.col_offset
                )
                if offset is not None:
                    symbols.append(Symbol(node.name, "class", str(py_file), offset))

            # ── Functions / methods ────────────────────────────────────
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                is_dunder = node.name.startswith("__") and node.name.endswith("__")
                if is_dunder:
                    pass  # Don't rename, but still look for local vars below
                elif skip(node.name):
                    pass
                elif _is_discovery_critical_test_function(node, py_file, parent_map):
                    pass
                elif _inside_function(node, parent_map):
                    pass  # nested function, skip
                elif _function_has_scope_hazards(node):
                    pass  # contains lambda / genexp / nested fn
                else:
                    offset = _offset_from_linecol(
                        source_bytes, node.lineno, node.col_offset
                    )
                    if offset is not None:
                        symbols.append(
                            Symbol(node.name, "function", str(py_file), offset)
                        )

                # ── Local variables inside this function ──────────────
                # Only if function itself is safe
                if _inside_function(node, parent_map):
                    continue
                if _function_has_scope_hazards(node):
                    continue

                params = _collect_function_params(node)

                # Collect ExceptHandler names so we don't rename the
                # reassignment `exc = exc.exceptions[0]` inside the block
                except_names: set[str] = set()
                for n in ast.walk(node):
                    if isinstance(n, ast.ExceptHandler) and n.name:
                        except_names.add(n.name)

                for child in ast.walk(node):
                    if child is node:
                        continue
                    # Skip nested function/class bodies (different scope)
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        continue

                    if isinstance(child, ast.Assign):
                        for target in child.targets:
                            for name, line, col in _iter_bound_names(target):
                                if name in params or name in except_names:
                                    continue
                                if skip(name):
                                    continue
                                off = _offset_from_linecol(
                                    source_bytes, line, col
                                )
                                if off is not None:
                                    symbols.append(
                                        Symbol(name, "variable", str(py_file), off)
                                    )
                    elif isinstance(child, ast.AnnAssign):
                        for name, line, col in _iter_bound_names(child.target):
                            if (
                                name not in params
                                and name not in except_names
                                and not skip(name)
                            ):
                                off = _offset_from_linecol(
                                    source_bytes,
                                    line,
                                    col,
                                )
                                if off is not None:
                                    symbols.append(
                                        Symbol(name, "variable", str(py_file), off)
                                    )
                    elif isinstance(child, ast.AugAssign):
                        for name, line, col in _iter_bound_names(child.target):
                            if name in params or name in except_names or skip(name):
                                continue
                            off = _offset_from_linecol(source_bytes, line, col)
                            if off is not None:
                                symbols.append(
                                    Symbol(name, "variable", str(py_file), off)
                                )
                    elif isinstance(child, (ast.For, ast.AsyncFor)):
                        for name, line, col in _iter_bound_names(child.target):
                            if name in params or name in except_names or skip(name):
                                continue
                            off = _offset_from_linecol(source_bytes, line, col)
                            if off is not None:
                                symbols.append(
                                    Symbol(name, "variable", str(py_file), off)
                                )
                    elif isinstance(child, (ast.With, ast.AsyncWith)):
                        for item in child.items:
                            if item.optional_vars is None:
                                continue
                            for name, line, col in _iter_bound_names(item.optional_vars):
                                if name in params or name in except_names or skip(name):
                                    continue
                                off = _offset_from_linecol(source_bytes, line, col)
                                if off is not None:
                                    symbols.append(
                                        Symbol(name, "variable", str(py_file), off)
                                    )
                    elif isinstance(child, ast.NamedExpr):
                        for name, line, col in _iter_bound_names(child.target):
                            if name in params or name in except_names or skip(name):
                                continue
                            off = _offset_from_linecol(source_bytes, line, col)
                            if off is not None:
                                symbols.append(
                                    Symbol(name, "variable", str(py_file), off)
                                )

    return symbols


def _dedupe_symbols(symbols: list[Symbol]) -> list[Symbol]:
    seen: set[str] = set()
    unique: list[Symbol] = []
    for sym in symbols:
        key = f"{sym.kind}::{sym.file_path}::{sym.offset}"
        if key in seen:
            continue
        seen.add(key)
        unique.append(sym)
    unique.sort(key=lambda sym: (sym.file_path, sym.offset, sym.kind, sym.name))
    return unique


def collect_naming_audit(repo_path: str | Path, sample_limit: int = 10) -> dict[str, Any]:
    """Collect a structured dry-run audit for the naming degrader."""
    path = Path(repo_path).resolve()
    if not path.is_dir():
        raise ValueError(f"Not a directory: {path}")

    forbidden = _collect_forbidden(path)
    unique = _dedupe_symbols(_collect_symbols(path, forbidden))

    counts = Counter(sym.kind for sym in unique)
    by_kind: dict[str, list[dict[str, Any]]] = {
        "class": [],
        "function": [],
        "variable": [],
    }
    files_touched: set[str] = set()
    for sym in unique:
        files_touched.add(sym.file_path)
        bucket = by_kind.setdefault(sym.kind, [])
        if len(bucket) >= sample_limit:
            continue
        bucket.append({
            "name": sym.name,
            "file_path": sym.file_path,
            "offset": sym.offset,
        })

    return {
        "repo_path": str(path),
        "forbidden_name_count": len(forbidden),
        "candidate_symbol_count": len(unique),
        "files_with_renames": len(files_touched),
        "rename_counts": {
            "classes": counts.get("class", 0),
            "functions": counts.get("function", 0),
            "variables": counts.get("variable", 0),
            "total": len(unique),
        },
        "sample_symbols": {
            "classes": by_kind.get("class", []),
            "functions": by_kind.get("function", []),
            "variables": by_kind.get("variable", []),
        },
    }


# ── Rename application ────────────────────────────────────────────────────────

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
                "rename_success_rate": (self.total() / attempted) if attempted else 0.0,
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

    def __str__(self) -> str:
        return (
            f"  Classes renamed   : {self.classes}\n"
            f"  Functions renamed : {self.functions}\n"
            f"  Variables renamed : {self.variables}\n"
            f"  Total renamed     : {self.total()}\n"
            f"  Skipped (errors)  : {self.skipped}\n"
            f"    Missing resource: {self.skipped_missing_resource}\n"
            f"    Offset not found: {self.skipped_offset_not_found}\n"
            f"    Refactor errors : {self.skipped_refactoring_error}\n"
            f"    Other errors    : {self.skipped_other_error}"
        )


def _new_name(kind: str, counter: dict[str, int]) -> str:
    n = counter[kind]
    counter[kind] += 1
    if kind == "class":
        return f"Cls{n}"
    elif kind == "function":
        return f"fn{n}"
    else:
        return f"v{n}"


def _find_near(source: str, name: str, offset: int) -> int | None:
    """
    Find `name` at approximately `offset` (which may be stale after
    prior renames). Returns the adjusted offset of a whole-identifier
    match, or None.
    """
    window = 400
    start = max(0, offset - window)
    end = min(len(source), offset + len(name) + window)
    region = source[start:end]

    def is_identifier_match(abs_idx: int) -> bool:
        before = source[abs_idx - 1] if abs_idx > 0 else " "
        after = (
            source[abs_idx + len(name)]
            if abs_idx + len(name) < len(source) else " "
        )
        return not (before.isalnum() or before == "_") and not (
            after.isalnum() or after == "_"
        )

    matches: list[int] = []
    i = 0
    while True:
        idx = region.find(name, i)
        if idx == -1:
            break
        abs_idx = start + idx
        if is_identifier_match(abs_idx):
            matches.append(abs_idx)
        i = idx + 1

    if matches:
        return min(matches, key=lambda found: abs(found - offset))

    # Earlier renames in the same file can shift the target far outside the
    # local window. Fall back to a whole-file search and choose the closest
    # whole-identifier match to the original definition offset.
    matches = []
    i = 0
    while True:
        idx = source.find(name, i)
        if idx == -1:
            break
        if is_identifier_match(idx):
            matches.append(idx)
        i = idx + 1

    if matches:
        return min(matches, key=lambda found: abs(found - offset))
    return None


def obfuscate_repo(repo_path: str, dry_run: bool = False) -> RenameStats:
    path = Path(repo_path).resolve()
    if not path.is_dir():
        raise ValueError(f"Not a directory: {path}")

    print(f"{'[DRY RUN] ' if dry_run else ''}Scanning {path} ...")
    forbidden = _collect_forbidden(path)
    print(f"  {len(forbidden)} names are globally off-limits "
          f"(imports / __all__ / kwarg keys / module names)")

    symbols = _collect_symbols(path, forbidden)
    print(f"  {len(symbols)} candidate symbols found")
    unique = _dedupe_symbols(symbols)
    print(f"  {len(unique)} unique symbols to rename\n")

    if dry_run:
        counter = {"class": 0, "function": 0, "variable": 0}
        try:
            for sym in unique:
                new = _new_name(sym.kind, counter)
                rel = Path(sym.file_path).relative_to(path)
                print(f"  {sym.kind:9s}  {sym.name:40s} → {new}  ({rel})")
        except BrokenPipeError:
            return RenameStats()
        return RenameStats()

    try:
        from rope.base.exceptions import RefactoringError, ResourceNotFoundError
        from rope.base.project import Project
        from rope.refactor.rename import Rename
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "The 'rope' package is required for non-dry-run naming obfuscation. "
            "Install it in the active environment before running this script."
        ) from exc

    project = Project(str(path), ropefolder=None)
    project.prefs["ignored_resources"] = list(EXCLUDE_DIRS)

    stats = RenameStats()
    counter = {"class": 0, "function": 0, "variable": 0}
    used: set[str] = set()

    try:
        for sym in unique:
            new_name = _new_name(sym.kind, counter)
            while new_name in used:
                new_name = _new_name(sym.kind, counter)
            used.add(new_name)

            try:
                rel_path = Path(sym.file_path).relative_to(path)
                resource = project.get_resource(str(rel_path))
            except (ResourceNotFoundError, ValueError):
                stats.record_skip("missing_resource", sym.name)
                continue

            current_source = resource.read()
            offset = _find_near(current_source, sym.name, sym.offset)
            if offset is None:
                stats.record_skip("offset_not_found", sym.name)
                continue

            try:
                renamer = Rename(project, resource, offset)
                changes = renamer.get_changes(new_name)
                project.do(changes)

                if sym.kind == "class":
                    stats.classes += 1
                elif sym.kind == "function":
                    stats.functions += 1
                else:
                    stats.variables += 1

                print(f"  ✓ {sym.kind:9s}  {sym.name:40s} → {new_name}")

            except RefactoringError as e:
                stats.record_skip("refactoring_error", sym.name)
                print(f"  ✗ {sym.kind:9s}  {sym.name}: {e}")
            except Exception as e:
                stats.record_skip("other_error", sym.name)
                print(f"  ✗ {sym.kind:9s}  {sym.name}: {type(e).__name__}: {e}")

    finally:
        project.close()

    return stats


# ── Backup / restore ──────────────────────────────────────────────────────────

def backup(repo_path: str) -> None:
    bak = repo_path.rstrip("/\\") + ".bak"
    if os.path.exists(bak):
        shutil.rmtree(bak)
    shutil.copytree(repo_path, bak)
    print(f"Backup: {bak}")


def restore(repo_path: str) -> None:
    bak = repo_path.rstrip("/\\") + ".bak"
    if not os.path.exists(bak):
        raise FileNotFoundError(f"No backup at {bak}")
    shutil.rmtree(repo_path)
    shutil.copytree(bak, repo_path)
    print(f"Restored {repo_path}")


# ── Test runner ───────────────────────────────────────────────────────────────

def run_tests(repo_path: str) -> bool:
    print(f"\nRunning tests in {repo_path} ...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--tb=short", "-q"],
        cwd=repo_path, capture_output=True, text=True,
    )
    out = result.stdout
    print(out[-3000:] if len(out) > 3000 else out)
    if result.returncode != 0:
        if result.stderr:
            print("STDERR:", result.stderr[-500:])
        print("⚠  Tests failed (note: some failures may be pre-existing)")
        return False
    print("✓  All tests passed")
    return True


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(
        description="Obfuscate names in a Python repo (rope-based, scope-limited)."
    )
    parser.add_argument("repo_path")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--restore", action="store_true")
    parser.add_argument("--no-backup", action="store_true")
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()

    if args.restore:
        restore(args.repo_path)
        return

    if not args.dry_run and not args.no_backup:
        backup(args.repo_path)

    stats = obfuscate_repo(args.repo_path, dry_run=args.dry_run)

    if not args.dry_run:
        print(f"\n{stats}")
        if not args.skip_tests:
            passed = run_tests(args.repo_path)
            if not passed:
                print(
                    f"\nRestore with: python naming_conventions.py "
                    f"{args.repo_path} --restore"
                )
                sys.exit(1)


if __name__ == "__main__":
    main()
