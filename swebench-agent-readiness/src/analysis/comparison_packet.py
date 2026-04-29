"""Minimal comparison artifact for one clean-vs-degraded pilot task."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


PACKET_SCHEMA_VERSION = "0.1.0"


@dataclass(frozen=True)
class ConditionOutcome:
    """Normalized outcome fields for one condition."""

    condition: str
    completion_reason: str
    target_success: bool | None
    fail_to_pass_failed_count: int | None
    pass_to_pass_failed_count: int | None
    files_opened_before_first_edit: int | None = None
    exploration_efficiency: float | None = None
    total_duration_seconds: float | None = None
    changed_files: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "condition": self.condition,
            "completion_reason": self.completion_reason,
            "target_success": self.target_success,
            "fail_to_pass_failed_count": self.fail_to_pass_failed_count,
            "pass_to_pass_failed_count": self.pass_to_pass_failed_count,
            "files_opened_before_first_edit": self.files_opened_before_first_edit,
            "exploration_efficiency": self.exploration_efficiency,
            "total_duration_seconds": self.total_duration_seconds,
            "changed_files": list(self.changed_files),
        }


@dataclass(frozen=True)
class ComparisonPacket:
    """Task-level clean-vs-degraded comparison packet."""

    schema_version: str
    instance_id: str
    repo: str
    harness: str
    chosen_condition: str
    integration_strategy: str
    clean: ConditionOutcome
    degraded: ConditionOutcome
    deltas: dict[str, float | int | bool | None]
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "instance_id": self.instance_id,
            "repo": self.repo,
            "harness": self.harness,
            "chosen_condition": self.chosen_condition,
            "integration_strategy": self.integration_strategy,
            "clean": self.clean.to_dict(),
            "degraded": self.degraded.to_dict(),
            "deltas": dict(self.deltas),
            "notes": list(self.notes),
        }


def _delta(value: float | int | None, baseline: float | int | None) -> float | int | None:
    if value is None or baseline is None:
        return None
    return value - baseline


def build_comparison_packet(
    *,
    instance_id: str,
    repo: str,
    harness: str,
    chosen_condition: str,
    integration_strategy: str,
    clean: ConditionOutcome,
    degraded: ConditionOutcome,
    notes: list[str] | None = None,
) -> ComparisonPacket:
    """Build the first pilot comparison artifact."""

    deltas = {
        "target_success_changed": (
            None
            if clean.target_success is None or degraded.target_success is None
            else clean.target_success != degraded.target_success
        ),
        "fail_to_pass_failed_count_delta": _delta(
            degraded.fail_to_pass_failed_count,
            clean.fail_to_pass_failed_count,
        ),
        "pass_to_pass_failed_count_delta": _delta(
            degraded.pass_to_pass_failed_count,
            clean.pass_to_pass_failed_count,
        ),
        "files_opened_before_first_edit_delta": _delta(
            degraded.files_opened_before_first_edit,
            clean.files_opened_before_first_edit,
        ),
        "exploration_efficiency_delta": _delta(
            degraded.exploration_efficiency,
            clean.exploration_efficiency,
        ),
        "total_duration_seconds_delta": _delta(
            degraded.total_duration_seconds,
            clean.total_duration_seconds,
        ),
    }
    return ComparisonPacket(
        schema_version=PACKET_SCHEMA_VERSION,
        instance_id=instance_id,
        repo=repo,
        harness=harness,
        chosen_condition=chosen_condition,
        integration_strategy=integration_strategy,
        clean=clean,
        degraded=degraded,
        deltas=deltas,
        notes=list(notes or []),
    )


def write_comparison_packet(packet: ComparisonPacket, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(packet.to_dict(), handle, indent=2)
    return path
