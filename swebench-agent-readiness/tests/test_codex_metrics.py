from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.harness.codex_metrics import parse_codex_agent_metrics


class CodexMetricsTest(unittest.TestCase):
    def test_parses_pre_edit_opened_files_and_usage(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace"
            (workspace / "src").mkdir(parents=True)
            (workspace / "tests").mkdir(parents=True)
            (workspace / "src" / "example.py").write_text("x = 1\n", encoding="utf-8")
            (workspace / "tests" / "test_example.py").write_text("def test_ok(): pass\n", encoding="utf-8")
            log_path = root / "agent_stdout.jsonl"
            events = [
                {
                    "type": "item.completed",
                    "item": {
                        "type": "command_execution",
                        "command": "/usr/bin/bash -lc \"sed -n '1,20p' src/example.py\"",
                    },
                },
                {
                    "type": "item.completed",
                    "item": {
                        "type": "command_execution",
                        "command": "/usr/bin/bash -lc 'cat tests/test_example.py'",
                    },
                },
                {
                    "type": "item.started",
                    "item": {
                        "type": "file_change",
                        "changes": [{"path": str(workspace / "src" / "example.py"), "kind": "update"}],
                    },
                },
                {
                    "type": "turn.completed",
                    "usage": {
                        "input_tokens": 10,
                        "cached_input_tokens": 5,
                        "output_tokens": 3,
                    },
                },
            ]
            log_path.write_text(
                "\n".join(json.dumps(event) for event in events) + "\n",
                encoding="utf-8",
            )

            metrics = parse_codex_agent_metrics(
                stdout_log_path=log_path,
                workspace_dir=workspace,
                relevant_files={"src/example.py"},
            )

        self.assertTrue(metrics.first_edit_detected)
        self.assertEqual(metrics.files_opened_before_first_edit, 2)
        self.assertEqual(metrics.opened_files_before_first_edit, ["src/example.py", "tests/test_example.py"])
        self.assertEqual(metrics.relevant_files_opened, 1)
        self.assertEqual(metrics.dead_end_file_opens, 1)
        self.assertEqual(metrics.exploration_efficiency, 0.5)
        self.assertEqual(metrics.total_tokens, 13)


if __name__ == "__main__":
    unittest.main()
