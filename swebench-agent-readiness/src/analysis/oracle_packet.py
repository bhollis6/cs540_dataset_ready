"""Build an oracle-backed comparison packet from pilot replay results."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.analysis.comparison_packet import (
    ComparisonPacket,
    ConditionOutcome,
    build_comparison_packet,
)
from src.harness.codex_metrics import CodexAgentMetrics
from src.harness.oracle_replay import OracleReplayResult
from src.harness.pilot_run import PilotRunSpec


@dataclass(frozen=True)
class OracleComparisonArtifact:
    """Small wrapper around the generic comparison packet with pilot metadata."""

    comparison_type: str
    replication_index: int
    packet: ComparisonPacket
    oracle_logs: dict[str, str]
    agent_metrics: dict[str, dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        payload = self.packet.to_dict()
        payload.update(
            {
                "comparison_type": self.comparison_type,
                "replication_index": self.replication_index,
                "oracle_logs": dict(self.oracle_logs),
                "agent_metrics": dict(self.agent_metrics),
            }
        )
        return payload


def _to_outcome(
    result: OracleReplayResult,
    metrics: CodexAgentMetrics | None,
) -> ConditionOutcome:
    return ConditionOutcome(
        condition=result.condition,
        completion_reason=result.completion_reason,
        target_success=result.task_success,
        fail_to_pass_failed_count=len(result.fail_to_pass_failed),
        pass_to_pass_failed_count=len(result.pass_to_pass_failed),
        files_opened_before_first_edit=(
            None if metrics is None else metrics.files_opened_before_first_edit
        ),
        exploration_efficiency=None if metrics is None else metrics.exploration_efficiency,
        total_duration_seconds=result.duration_seconds,
        changed_files=result.changed_files,
    )


def build_oracle_comparison_artifact(
    *,
    run_spec: PilotRunSpec,
    clean: OracleReplayResult,
    degraded: OracleReplayResult,
    clean_metrics: CodexAgentMetrics | None = None,
    degraded_metrics: CodexAgentMetrics | None = None,
    notes: list[str] | None = None,
) -> OracleComparisonArtifact:
    packet = build_comparison_packet(
        instance_id=run_spec.instance_id,
        repo=run_spec.repo,
        harness=run_spec.harness,
        chosen_condition=run_spec.chosen_condition,
        integration_strategy=run_spec.integration_strategy,
        clean=_to_outcome(clean, clean_metrics),
        degraded=_to_outcome(degraded, degraded_metrics),
        notes=notes,
    )
    return OracleComparisonArtifact(
        comparison_type="pilot_oracle_replay",
        replication_index=run_spec.clean.replication_index,
        packet=packet,
        oracle_logs={
            "clean": clean.oracle_log_path,
            "degraded": degraded.oracle_log_path,
        },
        agent_metrics={
            "clean": {} if clean_metrics is None else clean_metrics.to_dict(),
            "degraded": {} if degraded_metrics is None else degraded_metrics.to_dict(),
        },
    )


def write_oracle_comparison_artifact(
    artifact: OracleComparisonArtifact,
    json_path: Path,
    markdown_path: Path,
) -> Path:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(artifact.to_dict(), indent=2), encoding="utf-8")

    packet = artifact.packet
    markdown_lines = [
        f"# Oracle Comparison: {packet.instance_id}",
        "",
        f"- Harness: `{packet.harness}`",
        f"- Condition: `{packet.chosen_condition}`",
        f"- Replication: `rep_{artifact.replication_index}`",
        "",
        "## Clean",
        f"- Task success: `{packet.clean.target_success}`",
        f"- FAIL_TO_PASS failures: `{packet.clean.fail_to_pass_failed_count}`",
        f"- PASS_TO_PASS failures: `{packet.clean.pass_to_pass_failed_count}`",
        f"- Files opened before first edit: `{packet.clean.files_opened_before_first_edit}`",
        f"- Exploration efficiency: `{packet.clean.exploration_efficiency}`",
        "",
        "## Degraded",
        f"- Task success: `{packet.degraded.target_success}`",
        f"- FAIL_TO_PASS failures: `{packet.degraded.fail_to_pass_failed_count}`",
        f"- PASS_TO_PASS failures: `{packet.degraded.pass_to_pass_failed_count}`",
        f"- Files opened before first edit: `{packet.degraded.files_opened_before_first_edit}`",
        f"- Exploration efficiency: `{packet.degraded.exploration_efficiency}`",
        "",
        "## Delta",
        f"- Target success changed: `{packet.deltas['target_success_changed']}`",
        f"- FAIL_TO_PASS failure delta: `{packet.deltas['fail_to_pass_failed_count_delta']}`",
        f"- PASS_TO_PASS failure delta: `{packet.deltas['pass_to_pass_failed_count_delta']}`",
        f"- Files-opened delta: `{packet.deltas['files_opened_before_first_edit_delta']}`",
        f"- Exploration-efficiency delta: `{packet.deltas['exploration_efficiency_delta']}`",
        "",
        "## Notes",
    ]
    if packet.notes:
        markdown_lines.extend(f"- {note}" for note in packet.notes)
    else:
        markdown_lines.append("- No extra notes recorded.")
    markdown_path.write_text("\n".join(markdown_lines) + "\n", encoding="utf-8")
    return json_path
