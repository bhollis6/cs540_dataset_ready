from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from swebench.harness.test_spec.test_spec import make_test_spec

from src.harness.oracle_replay import (
    OracleReplayResult,
    extract_test_command,
    _run_oracle_command,
    write_oracle_replay_result,
)


class OracleReplayTest(unittest.TestCase):
    def test_extracts_test_command_from_snapshot_backed_spec(self) -> None:
        snapshot = json.loads(
            Path("archive/provenance/dev/active/bootstrap-2026-04-22/first_pilot_task_snapshot.json").read_text(
                encoding="utf-8"
            )
        )
        spec = make_test_spec(snapshot, namespace=None)

        command = extract_test_command(spec)

        self.assertEqual(command, "pytest -rA testing/test_skipping.py")

    def test_writes_result_payload(self) -> None:
        result = OracleReplayResult(
            schema_version="0.1.0",
            instance_id="pytest-dev__pytest-7432",
            repo="pytest-dev/pytest",
            condition="clean",
            workspace_dir="/tmp/workspace",
            oracle_workspace_dir="/tmp/oracle_workspace",
            oracle_log_path="/tmp/oracle.log",
            oracle_report_path="/tmp/report.json",
            oracle_env_path="/tmp/env.json",
            test_command="pytest -rA testing/test_skipping.py",
            command_returncode=0,
            duration_seconds=1.25,
            task_success=True,
            fail_to_pass_passed=["one"],
            fail_to_pass_failed=[],
            pass_to_pass_passed=["two"],
            pass_to_pass_failed=[],
            changed_files=["src/_pytest/skipping.py"],
            completion_reason="oracle_pass",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "result.json"
            write_oracle_replay_result(result, path)
            payload = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(payload["condition"], "clean")
        self.assertEqual(payload["fail_to_pass_total"], 1)
        self.assertEqual(payload["pass_to_pass_total"], 1)
        self.assertEqual(payload["changed_files"], ["src/_pytest/skipping.py"])

    def test_tox_current_env_command_runs_wrapped_pytest_directly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            test_file = root / "test_sample.py"
            test_file.write_text("def test_ok():\n    assert True\n", encoding="utf-8")

            returncode, _, stdout = _run_oracle_command(
                oracle_workspace_dir=root,
                python_path=Path(sys.executable),
                test_command="tox --current-env -epy39 -v -- test_sample.py",
            )

        self.assertEqual(returncode, 0)
        self.assertIn("test_sample.py::test_ok", stdout)


if __name__ == "__main__":
    unittest.main()
