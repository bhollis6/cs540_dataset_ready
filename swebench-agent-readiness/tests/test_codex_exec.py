from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.harness.codex_exec import CodexExecSpec, build_codex_exec_command


class CodexExecTest(unittest.TestCase):
    def test_build_codex_exec_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            spec = CodexExecSpec(
                condition="clean",
                workspace_dir=root / "workspace",
                prompt_path=root / "issue_prompt.md",
                stdout_log_path=root / "logs" / "agent_stdout.jsonl",
                stderr_log_path=root / "logs" / "agent_stderr.log",
                output_last_message_path=root / "logs" / "last_message.txt",
            )

            command = build_codex_exec_command(spec)

            self.assertEqual(command[0:2], ["codex", "exec"])
            self.assertIn("--full-auto", command)
            self.assertIn("--json", command)
            self.assertIn("--output-last-message", command)
            self.assertEqual(command[-1], "-")


if __name__ == "__main__":
    unittest.main()
