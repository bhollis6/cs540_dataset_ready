"""Machine-readable eligibility contracts for the SWE-bench degradation study."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


CONDITIONS = (
    "type_hints",
    "naming",
    "comments_docstrings",
    "remove_tests",
)
SIGNAL_LEVELS = ("none", "low", "medium", "high")
DECISION_STATES = ("GO", "REVIEW", "NO_GO")


def _require_membership(value: str, *, field_name: str, allowed: tuple[str, ...]) -> None:
    if value not in allowed:
        allowed_text = ", ".join(allowed)
        raise ValueError(f"{field_name} must be one of {{{allowed_text}}}, got {value!r}")


def _normalize_path_list(paths: list[str]) -> list[str]:
    normalized = []
    seen: set[str] = set()
    for raw_path in paths:
        path = raw_path.strip().replace("\\", "/")
        if not path:
            raise ValueError("Changed-file lists cannot contain empty paths")
        if path in seen:
            continue
        normalized.append(path)
        seen.add(path)
    return normalized


@dataclass(frozen=True)
class SignalAssessment:
    """Strength estimate for one information surface."""

    level: str
    rationale: str
    evidence: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _require_membership(self.level, field_name="SignalAssessment.level", allowed=SIGNAL_LEVELS)

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "rationale": self.rationale,
            "evidence": list(self.evidence),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SignalAssessment":
        return cls(
            level=payload["level"],
            rationale=payload["rationale"],
            evidence=list(payload.get("evidence", [])),
        )


@dataclass(frozen=True)
class ConditionEligibility:
    """Eligibility decision for one degradation condition."""

    condition: str
    status: str
    signal: SignalAssessment
    fairness_notes: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _require_membership(self.condition, field_name="ConditionEligibility.condition", allowed=CONDITIONS)
        _require_membership(self.status, field_name="ConditionEligibility.status", allowed=DECISION_STATES)

    def to_dict(self) -> dict[str, Any]:
        return {
            "condition": self.condition,
            "status": self.status,
            "signal": self.signal.to_dict(),
            "fairness_notes": list(self.fairness_notes),
            "blockers": list(self.blockers),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ConditionEligibility":
        return cls(
            condition=payload["condition"],
            status=payload["status"],
            signal=SignalAssessment.from_dict(payload["signal"]),
            fairness_notes=list(payload.get("fairness_notes", [])),
            blockers=list(payload.get("blockers", [])),
        )


@dataclass(frozen=True)
class TaskEligibilityRecord:
    """Study-specific admission record for one SWE-bench task."""

    schema_version: str
    dataset_name: str
    dataset_split: str
    instance_id: str
    repo: str
    base_commit: str | None
    changed_source_files: list[str]
    changed_test_files: list[str]
    changed_test_support_files: list[str]
    regression_surface_strength: str
    test_signal: SignalAssessment
    conditions: dict[str, ConditionEligibility]
    overall_status: str
    eligible_conditions: list[str]
    chosen_pilot_condition: str | None
    decision_summary: str
    evidence_sources: list[dict[str, str]] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _require_membership(
            self.regression_surface_strength,
            field_name="TaskEligibilityRecord.regression_surface_strength",
            allowed=SIGNAL_LEVELS,
        )
        _require_membership(
            self.overall_status,
            field_name="TaskEligibilityRecord.overall_status",
            allowed=DECISION_STATES,
        )
        object.__setattr__(self, "changed_source_files", _normalize_path_list(self.changed_source_files))
        object.__setattr__(self, "changed_test_files", _normalize_path_list(self.changed_test_files))
        object.__setattr__(
            self,
            "changed_test_support_files",
            _normalize_path_list(self.changed_test_support_files),
        )
        overlapping = set(self.changed_source_files) & set(self.changed_test_files)
        if overlapping:
            raise ValueError(f"Source/test file lists overlap: {sorted(overlapping)}")
        condition_keys = set(self.conditions)
        if condition_keys != set(CONDITIONS):
            raise ValueError(
                "TaskEligibilityRecord.conditions must contain exactly "
                f"{list(CONDITIONS)}, got {sorted(condition_keys)}"
            )
        for condition, payload in self.conditions.items():
            if payload.condition != condition:
                raise ValueError(
                    f"Condition key {condition!r} does not match payload.condition={payload.condition!r}"
                )
        eligible_set = set(self.eligible_conditions)
        unknown_eligible = eligible_set - set(CONDITIONS)
        if unknown_eligible:
            raise ValueError(f"eligible_conditions contains unknown values: {sorted(unknown_eligible)}")
        for condition in self.eligible_conditions:
            if self.conditions[condition].status == "NO_GO":
                raise ValueError(f"Condition {condition!r} cannot be eligible when its status is NO_GO")
        if self.chosen_pilot_condition is not None:
            _require_membership(
                self.chosen_pilot_condition,
                field_name="TaskEligibilityRecord.chosen_pilot_condition",
                allowed=CONDITIONS,
            )
            if self.chosen_pilot_condition not in eligible_set:
                raise ValueError("chosen_pilot_condition must appear in eligible_conditions")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "dataset_name": self.dataset_name,
            "dataset_split": self.dataset_split,
            "instance_id": self.instance_id,
            "repo": self.repo,
            "base_commit": self.base_commit,
            "changed_source_files": list(self.changed_source_files),
            "changed_test_files": list(self.changed_test_files),
            "changed_test_support_files": list(self.changed_test_support_files),
            "regression_surface_strength": self.regression_surface_strength,
            "test_signal": self.test_signal.to_dict(),
            "conditions": {
                condition: self.conditions[condition].to_dict() for condition in CONDITIONS
            },
            "overall_status": self.overall_status,
            "eligible_conditions": list(self.eligible_conditions),
            "chosen_pilot_condition": self.chosen_pilot_condition,
            "decision_summary": self.decision_summary,
            "evidence_sources": list(self.evidence_sources),
            "open_questions": list(self.open_questions),
            "notes": list(self.notes),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TaskEligibilityRecord":
        conditions = {
            condition: ConditionEligibility.from_dict(payload["conditions"][condition])
            for condition in CONDITIONS
        }
        return cls(
            schema_version=payload["schema_version"],
            dataset_name=payload["dataset_name"],
            dataset_split=payload["dataset_split"],
            instance_id=payload["instance_id"],
            repo=payload["repo"],
            base_commit=payload.get("base_commit"),
            changed_source_files=list(payload.get("changed_source_files", [])),
            changed_test_files=list(payload.get("changed_test_files", [])),
            changed_test_support_files=list(payload.get("changed_test_support_files", [])),
            regression_surface_strength=payload["regression_surface_strength"],
            test_signal=SignalAssessment.from_dict(payload["test_signal"]),
            conditions=conditions,
            overall_status=payload["overall_status"],
            eligible_conditions=list(payload.get("eligible_conditions", [])),
            chosen_pilot_condition=payload.get("chosen_pilot_condition"),
            decision_summary=payload["decision_summary"],
            evidence_sources=list(payload.get("evidence_sources", [])),
            open_questions=list(payload.get("open_questions", [])),
            notes=list(payload.get("notes", [])),
        )


def validate_task_eligibility_dict(payload: dict[str, Any]) -> TaskEligibilityRecord:
    """Raise ValueError for malformed eligibility payloads."""

    return TaskEligibilityRecord.from_dict(payload)


def load_task_eligibility(path: Path) -> TaskEligibilityRecord:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return validate_task_eligibility_dict(payload)


def write_task_eligibility(record: TaskEligibilityRecord, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(record.to_dict(), handle, indent=2)
    return path
