from __future__ import annotations

import ast
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Generator

from rope.base.exceptions import RefactoringError, ResourceNotFoundError
from rope.base.project import Project
from rope.refactor.rename import Rename


# ── Config ────────────────────────────────────────────────────────────────────

EXCLUDE_DIRS: set[str] = {
    ".git", ".ropeproject", "venv", "env", ".venv",
    "__pycache__", ".tox", ".nox", "build", "dist",
    ".idea", ".vscode", "tests", "test", "testing",
}

# Single-letter and common callback/loop names that cause scope issues
PROTECTED_NAMES: set[str] = {
    "self", "cls", "True", "False", "None",
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
}


def _is_protected(name: str) -> bool:
    if name in PROTECTED_NAMES:
        return True
    if name.startswith("__") and name.endswith("__"):
        return True
    return False


# ── File discovery ────────────────────────────────────────────────────────────

def _iter_py_files(repo_path: Path) -> Generator[Path, None, None]:
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [
            d for d in dirs
            if d not in EXCLUDE_DIRS and not d.startswith(".")
        ]
        for fname in files:
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


def _inside_class(node: ast.AST, parent_map: dict[int, ast.AST]) -> bool:
    """True if node is inside a class (possibly through method boundary)."""
    current = parent_map.get(id(node))
    while current is not None:
        if isinstance(current, ast.ClassDef):
            return True
        current = parent_map.get(id(current))
    return False


def _inside_function(node: ast.AST, parent_map: dict[int, ast.AST]) -> bool:
    current = parent_map.get(id(node))
    while current is not None:
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return True
        current = parent_map.get(id(current))
    return False


def _inside_generator(node: ast.AST, parent_map: dict[int, ast.AST]) -> bool:
    """True if node is inside a genexp, comprehension, or lambda (own scope)."""
    current = parent_map.get(id(node))
    while current is not None:
        if isinstance(current, (
            ast.GeneratorExp, ast.ListComp, ast.SetComp, ast.DictComp, ast.Lambda,
        )):
            return True
        current = parent_map.get(id(current))
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


def _collect_symbols(repo_path: Path, forbidden: set[str]) -> list[Symbol]:
    """
    Narrow scope:
      1. Classes not exported via __all__ and not inside any class
      2. Private functions (name starts with _, not dunder) that are
         standalone (not methods) and have no scope hazards
      3. Local variables inside standalone non-class functions
         with no scope hazards, excluding parameters and except vars
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
                offset = _offset_from_linecol(
                    source_bytes, node.lineno, node.col_offset
                )
                if offset is not None:
                    symbols.append(Symbol(node.name, "class", str(py_file), offset))

            # ── Private functions (standalone only) ────────────────────
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Must be private
                is_dunder = node.name.startswith("__") and node.name.endswith("__")
                is_private = node.name.startswith("_") and not is_dunder
                if not is_private:
                    pass  # Don't rename, but still look for local vars below
                elif skip(node.name):
                    pass
                elif _inside_class(node, parent_map):
                    pass  # method, skip
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
                if _inside_class(node, parent_map):
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

                    var_name: str | None = None
                    line: int | None = None
                    col: int | None = None

                    if isinstance(child, ast.Assign):
                        for target in child.targets:
                            if isinstance(target, ast.Name):
                                if target.id in params or target.id in except_names:
                                    continue
                                if skip(target.id):
                                    continue
                                off = _offset_from_linecol(
                                    source_bytes, target.lineno, target.col_offset
                                )
                                if off is not None:
                                    symbols.append(
                                        Symbol(target.id, "variable", str(py_file), off)
                                    )
                    elif isinstance(child, ast.AnnAssign):
                        if isinstance(child.target, ast.Name):
                            if (child.target.id not in params
                                    and child.target.id not in except_names
                                    and not skip(child.target.id)):
                                off = _offset_from_linecol(
                                    source_bytes,
                                    child.target.lineno,
                                    child.target.col_offset,
                                )
                                if off is not None:
                                    symbols.append(
                                        Symbol(
                                            child.target.id, "variable",
                                            str(py_file), off,
                                        )
                                    )

    return symbols


# ── Rename application ────────────────────────────────────────────────────────

@dataclass
class RenameStats:
    classes: int = 0
    functions: int = 0
    variables: int = 0
    skipped: int = 0

    def total(self) -> int:
        return self.classes + self.functions + self.variables

    def __str__(self) -> str:
        return (
            f"  Classes renamed   : {self.classes}\n"
            f"  Functions renamed : {self.functions}\n"
            f"  Variables renamed : {self.variables}\n"
            f"  Total renamed     : {self.total()}\n"
            f"  Skipped (errors)  : {self.skipped}"
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

    i = 0
    while True:
        idx = region.find(name, i)
        if idx == -1:
            return None
        abs_idx = start + idx
        before = source[abs_idx - 1] if abs_idx > 0 else " "
        after = (
            source[abs_idx + len(name)]
            if abs_idx + len(name) < len(source) else " "
        )
        if not (before.isalnum() or before == "_") and not (
            after.isalnum() or after == "_"
        ):
            return abs_idx
        i = idx + 1


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

    # Dedupe by (kind, name) — rope propagates across all usages
    seen: set[str] = set()
    unique: list[Symbol] = []
    for sym in symbols:
        key = f"{sym.kind}::{sym.name}"
        if key not in seen:
            seen.add(key)
            unique.append(sym)
    print(f"  {len(unique)} unique symbols to rename\n")

    if dry_run:
        counter = {"class": 0, "function": 0, "variable": 0}
        for sym in unique:
            new = _new_name(sym.kind, counter)
            rel = Path(sym.file_path).relative_to(path)
            print(f"  {sym.kind:9s}  {sym.name:40s} → {new}  ({rel})")
        return RenameStats()

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
                stats.skipped += 1
                continue

            current_source = resource.read()
            offset = _find_near(current_source, sym.name, sym.offset)
            if offset is None:
                stats.skipped += 1
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
                stats.skipped += 1
                print(f"  ✗ {sym.kind:9s}  {sym.name}: {e}")
            except Exception as e:
                stats.skipped += 1
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
