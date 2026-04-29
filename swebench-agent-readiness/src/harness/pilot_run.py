"""Small clean-vs-degraded run contracts for the first Codex pilot."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.filters.eligibility import CONDITIONS, TaskEligibilityRecord


RUN_SCHEMA_VERSION = "0.1.0"


@dataclass(frozen=True)
class ConditionWorkspacePlan:
    """Filesystem contract for one condition-specific run root."""

    condition: str
    replication_index: int
    run_root: Path
    workspace_dir: Path
    oracle_workspace_dir: Path
    logs_dir: Path
    metadata_path: Path
    prompt_path: Path
    result_path: Path
    metrics_path: Path
    degradation_targets: dict[str, list[str]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "condition": self.condition,
            "replication_index": self.replication_index,
            "run_root": str(self.run_root),
            "workspace_dir": str(self.workspace_dir),
            "oracle_workspace_dir": str(self.oracle_workspace_dir),
            "logs_dir": str(self.logs_dir),
            "metadata_path": str(self.metadata_path),
            "prompt_path": str(self.prompt_path),
            "result_path": str(self.result_path),
            "metrics_path": str(self.metrics_path),
            "degradation_targets": {
                key: list(value) for key, value in sorted(self.degradation_targets.items())
            },
        }


@dataclass(frozen=True)
class PilotRunSpec:
    """Top-level run spec for the first clean-vs-degraded comparison."""

    schema_version: str
    instance_id: str
    repo: str
    harness: str
    integration_strategy: str
    eligibility_path: Path
    chosen_condition: str
    clean: ConditionWorkspacePlan
    degraded: ConditionWorkspacePlan
    comparison_artifact_path: Path

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "instance_id": self.instance_id,
            "repo": self.repo,
            "harness": self.harness,
            "integration_strategy": self.integration_strategy,
            "eligibility_path": str(self.eligibility_path),
            "chosen_condition": self.chosen_condition,
            "clean": self.clean.to_dict(),
            "degraded": self.degraded.to_dict(),
            "comparison_artifact_path": str(self.comparison_artifact_path),
        }


def _targets_for_condition(
    eligibility: TaskEligibilityRecord,
    condition: str,
) -> dict[str, list[str]]:
    if condition == "clean":
        return {}

    source_like = (
        eligibility.changed_source_files
        + eligibility.changed_test_files
        + eligibility.changed_test_support_files
    )
    if condition in {"comments_docstrings", "type_hints", "naming"}:
        return {"target_files": list(source_like)}
    if condition == "remove_tests":
        return {
            "delete_files": list(eligibility.changed_test_files),
            "preserve_files": list(eligibility.changed_test_support_files),
        }
    raise ValueError(f"Unsupported condition: {condition}")


def _build_condition_workspace(
    *,
    run_root: Path,
    condition: str,
    replication_index: int,
    targets: dict[str, list[str]],
) -> ConditionWorkspacePlan:
    condition_root = run_root / condition / f"rep_{replication_index}"
    return ConditionWorkspacePlan(
        condition=condition,
        replication_index=replication_index,
        run_root=condition_root,
        workspace_dir=condition_root / "workspace",
        oracle_workspace_dir=condition_root / "oracle_workspace",
        logs_dir=condition_root / "logs",
        metadata_path=condition_root / "metadata.json",
        prompt_path=condition_root / "issue_prompt.md",
        result_path=condition_root / "result.json",
        metrics_path=condition_root / "metrics.json",
        degradation_targets=targets,
    )


def build_pilot_run_spec(
    *,
    output_root: Path,
    eligibility: TaskEligibilityRecord,
    eligibility_path: Path,
    harness: str = "codex-cli",
    integration_strategy: str = "pypi_dependency",
    chosen_condition: str | None = None,
    replication_index: int = 0,
) -> PilotRunSpec:
    """Build the smallest useful clean-vs-degraded run spec."""

    condition = chosen_condition or eligibility.chosen_pilot_condition
    if condition is None:
        if not eligibility.eligible_conditions:
            raise ValueError("Eligibility record does not expose any eligible conditions")
        condition = eligibility.eligible_conditions[0]
    if condition not in CONDITIONS:
        raise ValueError(f"Unknown pilot condition: {condition}")
    if condition not in eligibility.eligible_conditions:
        raise ValueError(f"Condition {condition!r} is not marked eligible for this task")
    run_root = output_root / "runs" / eligibility.instance_id / harness
    clean = _build_condition_workspace(
        run_root=run_root,
        condition="clean",
        replication_index=replication_index,
        targets={},
    )
    degraded = _build_condition_workspace(
        run_root=run_root,
        condition=condition,
        replication_index=replication_index,
        targets=_targets_for_condition(eligibility, condition),
    )
    return PilotRunSpec(
        schema_version=RUN_SCHEMA_VERSION,
        instance_id=eligibility.instance_id,
        repo=eligibility.repo,
        harness=harness,
        integration_strategy=integration_strategy,
        eligibility_path=eligibility_path,
        chosen_condition=condition,
        clean=clean,
        degraded=degraded,
        comparison_artifact_path=run_root / "comparison.json",
    )


def write_pilot_run_spec(spec: PilotRunSpec, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(spec.to_dict(), handle, indent=2)
    return path
