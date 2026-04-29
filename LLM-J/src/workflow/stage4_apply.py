"""Apply one Stage 4 degradation condition to a prepared workspace."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


def apply_stage4_condition(
    workspace: Path,
    condition: str,
    targets: dict[str, Any] | None,
) -> dict[str, Any]:
    """Apply one degradation condition inside an existing historical workspace."""
    resolved_workspace = workspace.resolve()
    if not resolved_workspace.is_dir():
        raise ValueError(f"Workspace does not exist: {resolved_workspace}")

    if condition == "clean":
        return {
            "status": "PASS",
            "condition": condition,
            "workspace": str(resolved_workspace),
            "summary": {
                "mode": "clean",
                "changed_files": 0,
            },
        }

    if targets is None:
        raise ValueError(f"Condition '{condition}' requires explicit degradation targets")

    if condition == "remove_tests":
        summary = _apply_remove_tests(resolved_workspace, targets)
    elif condition == "comments_docstrings":
        summary = _apply_comments_docstrings(resolved_workspace, targets)
    elif condition == "type_hints":
        summary = _apply_type_hints(resolved_workspace, targets)
    elif condition == "naming":
        summary = _apply_naming(resolved_workspace, targets)
    else:
        raise ValueError(f"Unsupported Stage 4 condition: {condition}")

    return {
        "status": "PASS",
        "condition": condition,
        "workspace": str(resolved_workspace),
        "summary": summary,
    }


def _apply_remove_tests(workspace: Path, targets: dict[str, Any]) -> dict[str, Any]:
    delete_files = _normalize_relative_paths(targets.get("delete_files", []))
    preserve_files = _normalize_relative_paths(targets.get("preserve_files", []))

    deleted: list[str] = []
    missing_delete_files: list[str] = []
    preserved_existing: list[str] = []
    preserved_missing: list[str] = []

    for relative_path in delete_files:
        path = _workspace_path(workspace, relative_path)
        if path.exists():
            path.unlink()
            deleted.append(relative_path)
        else:
            missing_delete_files.append(relative_path)

    for relative_path in preserve_files:
        if _workspace_path(workspace, relative_path).exists():
            preserved_existing.append(relative_path)
        else:
            preserved_missing.append(relative_path)

    return {
        "mode": "remove_tests",
        "delete_targets": delete_files,
        "preserve_targets": preserve_files,
        "deleted_files": deleted,
        "missing_delete_files": missing_delete_files,
        "preserved_existing": preserved_existing,
        "preserved_missing": preserved_missing,
        "changed_files": len(deleted),
    }


def _apply_comments_docstrings(workspace: Path, targets: dict[str, Any]) -> dict[str, Any]:
    module = _load_degradation_module("comments_docstrings")
    target_files = _normalize_relative_paths(targets.get("target_files", []))

    cleaned: list[str] = []
    failed: list[dict[str, str]] = []
    missing: list[str] = []
    skipped_non_python: list[str] = []

    for relative_path in target_files:
        path = _workspace_path(workspace, relative_path)
        if not path.exists():
            missing.append(relative_path)
            continue
        if path.suffix != ".py":
            skipped_non_python.append(relative_path)
            continue

        if module.process_file(path):
            cleaned.append(relative_path)
        else:
            failed.append({
                "path": relative_path,
                "error": "process_file returned False",
            })

    return {
        "mode": "comments_docstrings",
        "target_files": target_files,
        "cleaned_files": cleaned,
        "failed_files": failed,
        "missing_files": missing,
        "skipped_non_python": skipped_non_python,
        "changed_files": len(cleaned),
    }


def _apply_type_hints(workspace: Path, targets: dict[str, Any]) -> dict[str, Any]:
    try:
        module = _load_degradation_module("type_hint")
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Stage 4 type-hint degradation requires 'libcst'. "
            "Install it in the active environment or use uv fallback."
        ) from exc

    target_files = _normalize_relative_paths(targets.get("target_files", []))
    stripped: list[str] = []
    failed: list[dict[str, str]] = []
    missing: list[str] = []
    skipped_non_python: list[str] = []
    hints_encountered = 0
    hints_removed = 0

    for relative_path in target_files:
        path = _workspace_path(workspace, relative_path)
        if not path.exists():
            missing.append(relative_path)
            continue
        if path.suffix != ".py":
            skipped_non_python.append(relative_path)
            continue

        try:
            source = path.read_text(encoding="utf-8")
            tree = module.cst.parse_module(source)
            transformer = module.SuperSafeTypeHintStripper(removal_chance=1.0)
            modified = tree.visit(transformer)
            path.write_text(modified.code, encoding="utf-8")

            hints_encountered += transformer.hints_encountered
            hints_removed += transformer.hints_removed
            stripped.append(relative_path)
        except Exception as exc:  # pragma: no cover - safety path
            failed.append({
                "path": relative_path,
                "error": f"{type(exc).__name__}: {exc}",
            })

    return {
        "mode": "type_hints",
        "target_files": target_files,
        "stripped_files": stripped,
        "failed_files": failed,
        "missing_files": missing,
        "skipped_non_python": skipped_non_python,
        "hints_encountered": hints_encountered,
        "hints_removed": hints_removed,
        "changed_files": len(stripped),
    }


def _apply_naming(workspace: Path, targets: dict[str, Any]) -> dict[str, Any]:
    try:
        module = _load_degradation_module("naming_conventions")
        from rope.base.exceptions import RefactoringError, ResourceNotFoundError
        from rope.base.project import Project
        from rope.refactor.rename import Rename
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Stage 4 naming degradation requires 'rope'. "
            "Install it in the active environment or use uv fallback."
        ) from exc

    target_files = set(_normalize_relative_paths(targets.get("target_files", [])))
    forbidden = module._collect_forbidden(workspace)
    scoped_symbols = [
        symbol
        for symbol in module._collect_symbols(workspace, forbidden)
        if _relative_posix(Path(symbol.file_path).resolve().relative_to(workspace)) in target_files
    ]
    unique_symbols = module._dedupe_symbols(scoped_symbols)

    project = Project(str(workspace), ropefolder=None)
    project.prefs["ignored_resources"] = list(module.EXCLUDE_DIRS)

    stats = module.RenameStats()
    counter = {"class": 0, "function": 0, "variable": 0}
    used: set[str] = set()

    try:
        for symbol in unique_symbols:
            new_name = module._new_name(symbol.kind, counter)
            while new_name in used:
                new_name = module._new_name(symbol.kind, counter)
            used.add(new_name)

            try:
                relative_path = Path(symbol.file_path).resolve().relative_to(workspace)
                resource = project.get_resource(str(relative_path))
            except (ResourceNotFoundError, ValueError):
                stats.record_skip("missing_resource", symbol.name)
                continue

            current_source = resource.read()
            offset = module._find_near(current_source, symbol.name, symbol.offset)
            if offset is None:
                stats.record_skip("offset_not_found", symbol.name)
                continue

            try:
                renamer = Rename(project, resource, offset)
                changes = renamer.get_changes(new_name)
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

    return {
        "mode": "naming",
        "target_files": sorted(target_files),
        "candidate_symbol_count": len(unique_symbols),
        **stats.to_dict(),
    }


def _normalize_relative_paths(paths: Any) -> list[str]:
    if paths is None:
        return []
    if not isinstance(paths, list):
        raise ValueError(f"Expected a list of relative paths, got {type(paths).__name__}")

    normalized: list[str] = []
    seen: set[str] = set()
    for raw_path in paths:
        raw = str(raw_path).strip().replace("\\", "/")
        if not raw:
            raise ValueError("Empty relative path in degradation target list")
        pure = PurePosixPath(raw)
        if pure.is_absolute():
            raise ValueError(f"Degradation targets must be relative paths, got: {raw}")
        normalized_path = pure.as_posix()
        if normalized_path in seen:
            continue
        seen.add(normalized_path)
        normalized.append(normalized_path)
    return sorted(normalized)


def _workspace_path(workspace: Path, relative_path: str) -> Path:
    return workspace.joinpath(*PurePosixPath(relative_path).parts)


def _relative_posix(path: Path) -> str:
    return PurePosixPath(path.as_posix()).as_posix()


def _degradation_root() -> Path:
    return Path(__file__).resolve().parents[3] / "degradation"


def _load_degradation_module(module_name: str) -> Any:
    module_path = _degradation_root() / f"{module_name}.py"
    if not module_path.exists():
        raise FileNotFoundError(f"Degradation helper not found: {module_path}")

    spec = importlib.util.spec_from_file_location(f"llmj_degradation_{module_name}", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load degradation helper: {module_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, module)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply one Stage 4 condition to a workspace")
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--condition", required=True)
    parser.add_argument("--targets-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    with open(args.targets_file) as f:
        targets = json.load(f)

    result = apply_stage4_condition(args.workspace, args.condition, targets)
    result["generated_at"] = datetime.now(timezone.utc).isoformat()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)


if __name__ == "__main__":
    main()
