from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.analysis.oracle_packet import (
    build_oracle_comparison_artifact,
    write_oracle_comparison_artifact,
)
from src.filters.eligibility import load_task_eligibility
from src.harness.codex_metrics import CodexAgentMetrics
from src.harness.oracle_replay import OracleReplayResult
from src.harness.pilot_run import build_pilot_run_spec


ROOT = Path(__file__).resolve().parents[1]


class OraclePacketTest(unittest.TestCase):
    def test_builds_oracle_comparison_artifact(self) -> None:
        eligibility_path = ROOT / "src" / "profiles" / "first_pilot_eligibility.json"
        eligibility = load_task_eligibility(eligibility_path)
        run_spec = build_pilot_run_spec(
            output_root=ROOT,
            eligibility=eligibility,
            eligibility_path=eligibility_path,
            replication_index=1,
        )
        clean = OracleReplayResult(
            schema_version="0.1.0",
            instance_id=run_spec.instance_id,
            repo=run_spec.repo,
            condition="clean",
            workspace_dir="/tmp/clean",
            oracle_workspace_dir="/tmp/clean_oracle",
            oracle_log_path="/tmp/clean.log",
            oracle_report_path="/tmp/clean_report.json",
            oracle_env_path="/tmp/clean_env.json",
            test_command="pytest -rA testing/test_skipping.py",
            command_returncode=0,
            duration_seconds=1.0,
            task_success=True,
            fail_to_pass_passed=["f2p"],
            fail_to_pass_failed=[],
            pass_to_pass_passed=["p2p"],
            pass_to_pass_failed=[],
            changed_files=["src/_pytest/skipping.py"],
            completion_reason="oracle_pass",
        )
        degraded = OracleReplayResult(
            schema_version="0.1.0",
            instance_id=run_spec.instance_id,
            repo=run_spec.repo,
            condition=run_spec.chosen_condition,
            workspace_dir="/tmp/degraded",
            oracle_workspace_dir="/tmp/degraded_oracle",
            oracle_log_path="/tmp/degraded.log",
            oracle_report_path="/tmp/degraded_report.json",
            oracle_env_path="/tmp/degraded_env.json",
            test_command="pytest -rA testing/test_skipping.py",
            command_returncode=1,
            duration_seconds=2.0,
            task_success=False,
            fail_to_pass_passed=[],
            fail_to_pass_failed=["f2p"],
            pass_to_pass_passed=[],
            pass_to_pass_failed=["p2p"],
            changed_files=["src/_pytest/skipping.py", "testing/test_skipping.py"],
            completion_reason="oracle_fail",
        )

        artifact = build_oracle_comparison_artifact(
            run_spec=run_spec,
            clean=clean,
            degraded=degraded,
            clean_metrics=CodexAgentMetrics(
                files_opened_before_first_edit=1,
                opened_files_before_first_edit=["src/_pytest/skipping.py"],
                relevant_files_opened=1,
                relevant_opened_files=["src/_pytest/skipping.py"],
                dead_end_file_opens=0,
                dead_end_opened_files=[],
                exploration_efficiency=1.0,
                first_edit_detected=True,
                input_tokens=10,
                cached_input_tokens=2,
                output_tokens=4,
                total_tokens=16,
            ),
            degraded_metrics=CodexAgentMetrics(
                files_opened_before_first_edit=3,
                opened_files_before_first_edit=["a", "b", "c"],
                relevant_files_opened=1,
                relevant_opened_files=["a"],
                dead_end_file_opens=2,
                dead_end_opened_files=["b", "c"],
                exploration_efficiency=0.3333,
                first_edit_detected=True,
                input_tokens=20,
                cached_input_tokens=3,
                output_tokens=5,
                total_tokens=28,
            ),
            notes=["pilot oracle replay"],
        )

        self.assertEqual(artifact.comparison_type, "pilot_oracle_replay")
        self.assertEqual(artifact.replication_index, 1)
        self.assertTrue(artifact.packet.clean.target_success)
        self.assertEqual(artifact.packet.degraded.pass_to_pass_failed_count, 1)
        self.assertTrue(artifact.packet.deltas["target_success_changed"])
        self.assertEqual(artifact.packet.clean.files_opened_before_first_edit, 1)
        self.assertEqual(artifact.packet.degraded.files_opened_before_first_edit, 3)

    def test_writes_json_and_markdown(self) -> None:
        eligibility_path = ROOT / "src" / "profiles" / "first_pilot_eligibility.json"
        eligibility = load_task_eligibility(eligibility_path)
        run_spec = build_pilot_run_spec(
            output_root=ROOT,
            eligibility=eligibility,
            eligibility_path=eligibility_path,
            replication_index=1,
        )
        clean = OracleReplayResult(
            schema_version="0.1.0",
            instance_id=run_spec.instance_id,
            repo=run_spec.repo,
            condition="clean",
            workspace_dir="/tmp/clean",
            oracle_workspace_dir="/tmp/clean_oracle",
            oracle_log_path="/tmp/clean.log",
            oracle_report_path="/tmp/clean_report.json",
            oracle_env_path="/tmp/clean_env.json",
            test_command="pytest -rA testing/test_skipping.py",
            command_returncode=0,
            duration_seconds=1.0,
            task_success=True,
            fail_to_pass_passed=["f2p"],
            fail_to_pass_failed=[],
            pass_to_pass_passed=["p2p"],
            pass_to_pass_failed=[],
            changed_files=["src/_pytest/skipping.py"],
            completion_reason="oracle_pass",
        )
        degraded = OracleReplayResult(
            schema_version="0.1.0",
            instance_id=run_spec.instance_id,
            repo=run_spec.repo,
            condition=run_spec.chosen_condition,
            workspace_dir="/tmp/degraded",
            oracle_workspace_dir="/tmp/degraded_oracle",
            oracle_log_path="/tmp/degraded.log",
            oracle_report_path="/tmp/degraded_report.json",
            oracle_env_path="/tmp/degraded_env.json",
            test_command="pytest -rA testing/test_skipping.py",
            command_returncode=0,
            duration_seconds=2.0,
            task_success=True,
            fail_to_pass_passed=["f2p"],
            fail_to_pass_failed=[],
            pass_to_pass_passed=["p2p"],
            pass_to_pass_failed=[],
            changed_files=["src/_pytest/skipping.py", "testing/test_skipping.py"],
            completion_reason="oracle_pass",
        )
        artifact = build_oracle_comparison_artifact(
            run_spec=run_spec,
            clean=clean,
            degraded=degraded,
            clean_metrics=CodexAgentMetrics(
                files_opened_before_first_edit=1,
                opened_files_before_first_edit=["src/_pytest/skipping.py"],
                relevant_files_opened=1,
                relevant_opened_files=["src/_pytest/skipping.py"],
                dead_end_file_opens=0,
                dead_end_opened_files=[],
                exploration_efficiency=1.0,
                first_edit_detected=True,
                input_tokens=10,
                cached_input_tokens=2,
                output_tokens=4,
                total_tokens=16,
            ),
            degraded_metrics=CodexAgentMetrics(
                files_opened_before_first_edit=2,
                opened_files_before_first_edit=["src/_pytest/skipping.py", "testing/test_skipping.py"],
                relevant_files_opened=2,
                relevant_opened_files=["src/_pytest/skipping.py", "testing/test_skipping.py"],
                dead_end_file_opens=0,
                dead_end_opened_files=[],
                exploration_efficiency=1.0,
                first_edit_detected=True,
                input_tokens=20,
                cached_input_tokens=3,
                output_tokens=5,
                total_tokens=28,
            ),
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            json_path = Path(temp_dir) / "comparison.json"
            markdown_path = Path(temp_dir) / "comparison.md"
            write_oracle_comparison_artifact(artifact, json_path, markdown_path)
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            markdown = markdown_path.read_text(encoding="utf-8")

        self.assertEqual(payload["replication_index"], 1)
        self.assertEqual(payload["comparison_type"], "pilot_oracle_replay")
        self.assertEqual(payload["agent_metrics"]["clean"]["total_tokens"], 16)
        self.assertIn("## Clean", markdown)


if __name__ == "__main__":
    unittest.main()
