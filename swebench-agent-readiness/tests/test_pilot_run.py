from __future__ import annotations

import unittest
from pathlib import Path

from src.analysis.comparison_packet import ConditionOutcome, build_comparison_packet
from src.filters.eligibility import load_task_eligibility
from src.harness.pilot_run import build_pilot_run_spec


ROOT = Path(__file__).resolve().parents[1]


class PilotRunContractTest(unittest.TestCase):
    def test_builds_clean_and_degraded_run_specs(self) -> None:
        eligibility_path = ROOT / "src" / "profiles" / "first_pilot_eligibility.json"
        eligibility = load_task_eligibility(eligibility_path)

        run_spec = build_pilot_run_spec(
            output_root=ROOT,
            eligibility=eligibility,
            eligibility_path=eligibility_path,
            replication_index=1,
        )

        self.assertEqual(run_spec.instance_id, "pytest-dev__pytest-7432")
        self.assertEqual(run_spec.clean.condition, "clean")
        self.assertEqual(run_spec.clean.replication_index, 1)
        self.assertEqual(run_spec.degraded.condition, "comments_docstrings")
        self.assertEqual(run_spec.degraded.replication_index, 1)
        self.assertIn("/rep_1/", str(run_spec.clean.workspace_dir))
        self.assertIn("target_files", run_spec.degraded.degradation_targets)
        self.assertIn("src/_pytest/skipping.py", run_spec.degraded.degradation_targets["target_files"])

    def test_builds_remove_tests_targets_from_eligibility(self) -> None:
        eligibility_path = ROOT / "src" / "profiles" / "first_pilot_eligibility.json"
        eligibility = load_task_eligibility(eligibility_path)

        run_spec = build_pilot_run_spec(
            output_root=ROOT,
            eligibility=eligibility,
            eligibility_path=eligibility_path,
            chosen_condition="remove_tests",
            replication_index=0,
        )

        self.assertEqual(run_spec.degraded.condition, "remove_tests")
        self.assertEqual(
            run_spec.degraded.degradation_targets["delete_files"],
            ["testing/test_skipping.py"],
        )
        self.assertEqual(run_spec.degraded.degradation_targets["preserve_files"], [])

    def test_comparison_packet_computes_deltas(self) -> None:
        clean = ConditionOutcome(
            condition="clean",
            completion_reason="oracle_pass",
            target_success=True,
            fail_to_pass_failed_count=0,
            pass_to_pass_failed_count=0,
            files_opened_before_first_edit=2,
            exploration_efficiency=1.0,
            total_duration_seconds=30.0,
        )
        degraded = ConditionOutcome(
            condition="comments_docstrings",
            completion_reason="oracle_fail",
            target_success=False,
            fail_to_pass_failed_count=1,
            pass_to_pass_failed_count=0,
            files_opened_before_first_edit=4,
            exploration_efficiency=0.5,
            total_duration_seconds=45.0,
        )

        packet = build_comparison_packet(
            instance_id="pytest-dev__pytest-7432",
            repo="pytest-dev/pytest",
            harness="codex-cli",
            chosen_condition="comments_docstrings",
            integration_strategy="pypi_dependency",
            clean=clean,
            degraded=degraded,
        )

        self.assertTrue(packet.deltas["target_success_changed"])
        self.assertEqual(packet.deltas["fail_to_pass_failed_count_delta"], 1)
        self.assertEqual(packet.deltas["pass_to_pass_failed_count_delta"], 0)
        self.assertEqual(packet.deltas["files_opened_before_first_edit_delta"], 2)


if __name__ == "__main__":
    unittest.main()
