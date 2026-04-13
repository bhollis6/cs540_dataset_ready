
from __future__ import annotations

import ast
import io
import os
import shutil
import subprocess
import sys
import tokenize
from pathlib import Path


EXCLUDE_DIRS = {
    ".git", ".ropeproject", "venv", "env", ".venv",
    "__pycache__", ".tox", ".nox", "build", "dist",
    ".idea", ".vscode", "tests", "test", "testing",
}

# Names never renamed
PROTECTED = {
    "self", "cls", "True", "False", "None",
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k",
    "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v",
    "w", "x", "y", "z",
}


def _is_protected(name: str) -> bool:
    if name in PROTECTED:
        return True
    if name.startswith("__") and name.endswith("__"):
        return True
    return False


def _is_safe_function(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """
    Return True only if this function contains no constructs that
    could cause scoping issues when variables are renamed:
    - No generator expressions
    - No list/set/dict comprehensions
    - No nested functions or lambdas
    - No nonlocal or global statements
    """
    for node in ast.walk(func):
        if node is func:
            continue
        if isinstance(node, (
            ast.GeneratorExp,
            ast.ListComp,
            ast.SetComp,
            ast.DictComp,
            ast.Lambda,
            ast.FunctionDef,
            ast.AsyncFunctionDef,
            ast.Nonlocal,
            ast.Global,
        )):
            return False
    return True


def _collect_locals(func: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    # Collect all parameter names first — these are off-limits
    param_names: set[str] = set()
    all_args = (
        func.args.args + func.args.posonlyargs + func.args.kwonlyargs
    )
    if func.args.vararg:
        all_args.append(func.args.vararg)
    if func.args.kwarg:
        all_args.append(func.args.kwarg)
    for arg in all_args:
        param_names.add(arg.arg)

    # Collect all ExceptHandler names — these are off-limits too.
    # In Python 3, except X as e variables are deleted after the block,
    # but assignments inside the block (e = e.x) must use the same name.
    for node in ast.walk(func):
        if isinstance(node, ast.ExceptHandler) and node.name:
            param_names.add(node.name)

    names: set[str] = set()
    for node in ast.walk(func):
        if node is not func and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                names.add(node.target.id)
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            if isinstance(node.target, ast.Name):
                names.add(node.target.id)
        elif isinstance(node, ast.withitem):
            if node.optional_vars and isinstance(node.optional_vars, ast.Name):
                names.add(node.optional_vars.id)
        # ExceptHandler variables (except X as e) are intentionally excluded.
        # In Python 3, these are deleted after the except block ends,
        # so renaming them causes NameError if referenced after the block.
    return {n for n in names if not _is_protected(n) and n not in param_names}


def _build_mapping(source: str) -> dict[tuple[int, int], str]:
    """Build {(line, col): new_name} for all safe renames in this file."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}

    renames: dict[tuple[int, int], str] = {}

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not _is_safe_function(node):
            continue

        local_names = _collect_locals(node)
        if not local_names:
            continue

        # Deterministic sequential mapping
        mapping = {name: f"v{i}" for i, name in enumerate(sorted(local_names))}

        for child in ast.walk(node):
            if isinstance(child, ast.Name) and child.id in mapping:
                renames[(child.lineno, child.col_offset)] = mapping[child.id]

    return renames


def _apply_renames(source: str, renames: dict[tuple[int, int], str]) -> str:
    if not renames:
        return source
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except tokenize.TokenError:
        return source

    new_tokens = []
    for tok in tokens:
        if tok.type == tokenize.NAME:
            key = (tok.start[0], tok.start[1])
            if key in renames:
                tok = tok._replace(string=renames[key])
        new_tokens.append(tok)

    try:
        return tokenize.untokenize(new_tokens)
    except Exception:
        return source


def process_file(path: Path) -> int:
    try:
        source = path.read_text(encoding="utf-8")
    except Exception:
        return 0
    renames = _build_mapping(source)
    if not renames:
        return 0
    new_source = _apply_renames(source, renames)
    if new_source == source:
        return 0
    path.write_text(new_source, encoding="utf-8")
    return len(renames)


def process_repo(repo_path: str, dry_run: bool = False) -> int:
    path = Path(repo_path).resolve()
    total = 0
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]
        for fname in files:
            if not fname.endswith(".py"):
                continue
            fpath = Path(root) / fname
            source = fpath.read_text(encoding="utf-8")
            renames = _build_mapping(source)
            if not renames:
                continue
            if dry_run:
                print(f"  {fpath.relative_to(path)} — {len(renames)} renames")
            else:
                n = process_file(fpath)
                total += n
                if n:
                    print(f"  ✓ {fpath.relative_to(path)} ({n} renames)")
    return total


def backup(repo_path: str) -> None:
    bak = repo_path.rstrip("/\\") + ".bak"
    if os.path.exists(bak):
        shutil.rmtree(bak)
    shutil.copytree(repo_path, bak)
    print(f"Backup created: {bak}")


def restore(repo_path: str) -> None:
    bak = repo_path.rstrip("/\\") + ".bak"
    if not os.path.exists(bak):
        raise FileNotFoundError(f"No backup at {bak}")
    shutil.rmtree(repo_path)
    shutil.copytree(bak, repo_path)
    print(f"Restored from {bak}")


def run_tests(repo_path: str) -> bool:
    result = subprocess.run(
        ["python", "-m", "pytest", "--tb=short", "-q"],
        cwd=repo_path, capture_output=True, text=True,
    )
    out = result.stdout
    print(out[-3000:] if len(out) > 3000 else out)
    if result.returncode != 0:
        print("STDERR:", result.stderr[-500:])
        print("⚠  Tests FAILED")
        return False
    print("✓  All tests passed")
    return True


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
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

    total = process_repo(args.repo_path, dry_run=args.dry_run)

    if not args.dry_run:
        print(f"\nTotal renames: {total}")
        if not args.skip_tests:
            passed = run_tests(args.repo_path)
            if not passed:
                print(f"\nRestore with: python naming_conventions.py {args.repo_path} --restore")
                sys.exit(1)


if __name__ == "__main__":
    main()
