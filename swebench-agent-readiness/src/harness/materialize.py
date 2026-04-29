"""Host-local workspace materialization helpers for the first pilot."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.degradation.comments_docstrings import process_file as strip_comments_docstrings_file
from src.degradation.naming import obfuscate_targets
from src.degradation.type_hints import process_file as strip_type_hints_file
from src.harness.pilot_run import PilotRunSpec
from src.substrate.swebench_verified import TaskSnapshot


def _run(command: list[str], *, cwd: Path | None = None) -> None:
    subprocess.run(command, check=True, cwd=str(cwd) if cwd else None)


@dataclass(frozen=True)
class MaterializationResult:
    """Record of what was created for a local pilot workspace."""

    instance_id: str
    repo: str
    base_commit: str
    clean_workspace: str
    degraded_workspace: str
    degraded_condition: str
    degraded_targets: dict[str, list[str]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "repo": self.repo,
            "base_commit": self.base_commit,
            "clean_workspace": self.clean_workspace,
            "degraded_workspace": self.degraded_workspace,
            "degraded_condition": self.degraded_condition,
            "degraded_targets": {
                key: list(value) for key, value in sorted(self.degraded_targets.items())
            },
        }


def render_issue_prompt(snapshot: TaskSnapshot) -> str:
    """Render the minimal problem statement prompt for the pilot harness."""

    lines = [
        f"# SWE-bench Task: {snapshot.instance_id}",
        "",
        f"- Repo: `{snapshot.repo}`",
        f"- Base commit: `{snapshot.base_commit}`",
        f"- Version: `{snapshot.version}`" if snapshot.version else "- Version: unknown",
        "",
        "## Problem Statement",
        snapshot.problem_statement.strip(),
        "",
        "## Constraints",
        "- You are working from a historical repository checkout.",
        "- Existing tests are not shown directly unless they remain in the workspace.",
        "- Solve the issue without relying on future repository history.",
        "- For validation, prefer the workspace-local interpreter if present:",
        "  `./.pilot-venv-*/bin/python -m pytest ...`",
        "- Do not rely on `/usr/bin/python`, `python`, or any repo-root `.venv` when a workspace venv exists.",
    ]
    if snapshot.hints_text:
        lines.extend(["", "## Hints", snapshot.hints_text.strip()])
    return "\n".join(lines).strip() + "\n"


def write_run_context(
    *,
    snapshot: TaskSnapshot,
    run_spec: PilotRunSpec,
) -> None:
    """Write prompt and metadata files for both clean and degraded run roots."""

    prompt = render_issue_prompt(snapshot)
    for plan in (run_spec.clean, run_spec.degraded):
        plan.run_root.mkdir(parents=True, exist_ok=True)
        plan.logs_dir.mkdir(parents=True, exist_ok=True)
        plan.prompt_path.write_text(prompt, encoding="utf-8")
        metadata = {
            "instance_id": snapshot.instance_id,
            "repo": snapshot.repo,
            "base_commit": snapshot.base_commit,
            "condition": plan.condition,
            "source_files": snapshot.source_files,
            "test_files": snapshot.test_files,
            "fail_to_pass": snapshot.fail_to_pass,
            "pass_to_pass_count": len(snapshot.pass_to_pass),
            "degradation_targets": plan.degradation_targets,
        }
        with plan.metadata_path.open("w", encoding="utf-8") as handle:
            json.dump(metadata, handle, indent=2)


def materialize_clean_workspace(
    *,
    snapshot: TaskSnapshot,
    target_dir: Path,
    source_clone_dir: Path | None = None,
) -> Path:
    """Clone a repo and reset it to the task base commit."""

    if target_dir.exists():
        raise FileExistsError(f"Target workspace already exists: {target_dir}")
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    clone_source = str(source_clone_dir) if source_clone_dir is not None else f"https://github.com/{snapshot.repo}.git"
    _run(["git", "clone", "-o", "origin", "--single-branch", clone_source, str(target_dir)])
    _run(["git", "reset", "--hard", snapshot.base_commit], cwd=target_dir)
    _run(["git", "remote", "remove", "origin"], cwd=target_dir)
    return target_dir


def materialize_degraded_workspace(
    *,
    clean_dir: Path,
    degraded_dir: Path,
    condition: str,
    targets: dict[str, list[str]],
) -> Path:
    """Copy the clean workspace and apply the selected degradation."""

    if degraded_dir.exists():
        raise FileExistsError(f"Target workspace already exists: {degraded_dir}")
    shutil.copytree(clean_dir, degraded_dir)
    if condition == "comments_docstrings":
        for relative_path in targets.get("target_files", []):
            path = degraded_dir / relative_path
            if path.suffix == ".py" and path.exists():
                strip_comments_docstrings_file(path)
    elif condition == "type_hints":
        for relative_path in targets.get("target_files", []):
            path = degraded_dir / relative_path
            if path.suffix == ".py" and path.exists():
                strip_type_hints_file(path)
    elif condition == "naming":
        obfuscate_targets(
            degraded_dir,
            {
                relative_path
                for relative_path in targets.get("target_files", [])
                if (degraded_dir / relative_path).suffix == ".py"
                and (degraded_dir / relative_path).exists()
            },
        )
    elif condition == "remove_tests":
        for relative_path in targets.get("delete_files", []):
            path = degraded_dir / relative_path
            if path.exists() and path.is_file():
                path.unlink()
    return degraded_dir


def materialize_pilot_run(
    *,
    snapshot: TaskSnapshot,
    run_spec: PilotRunSpec,
    output_path: Path,
    source_clone_dir: Path | None = None,
) -> Path:
    """Materialize the first clean/degraded pair on the host filesystem."""

    clean_dir = materialize_clean_workspace(
        snapshot=snapshot,
        target_dir=run_spec.clean.workspace_dir,
        source_clone_dir=source_clone_dir,
    )
    degraded_dir = materialize_degraded_workspace(
        clean_dir=clean_dir,
        degraded_dir=run_spec.degraded.workspace_dir,
        condition=run_spec.degraded.condition,
        targets=run_spec.degraded.degradation_targets,
    )
    write_run_context(snapshot=snapshot, run_spec=run_spec)
    result = MaterializationResult(
        instance_id=snapshot.instance_id,
        repo=snapshot.repo,
        base_commit=snapshot.base_commit,
        clean_workspace=str(clean_dir),
        degraded_workspace=str(degraded_dir),
        degraded_condition=run_spec.degraded.condition,
        degraded_targets=run_spec.degraded.degradation_targets,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(result.to_dict(), handle, indent=2)
    return output_path
