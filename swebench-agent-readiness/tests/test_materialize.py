from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from src.harness.materialize import (
    materialize_clean_workspace,
    materialize_degraded_workspace,
    render_issue_prompt,
)
from src.substrate.swebench_verified import TaskSnapshot


class MaterializeTest(unittest.TestCase):
    def test_render_issue_prompt_includes_workspace_python_guidance(self) -> None:
        prompt = render_issue_prompt(
            TaskSnapshot(
                schema_version="0.1.0",
                dataset_name="SWE-bench/SWE-bench_Verified",
                dataset_split="test",
                instance_id="psf__requests-2317",
                repo="psf/requests",
                base_commit="abc123",
                version="2.4",
                problem_statement="Fix the bytes method coercion bug.",
                hints_text="Use the native string helper.",
                source_files=["requests/sessions.py"],
                test_files=["test_requests.py"],
                fail_to_pass=["test_requests.py::TestTimeout::test_encoded_methods"],
                pass_to_pass=[],
                patch="",
                test_patch="",
            )
        )

        self.assertIn("./.pilot-venv-*/bin/python -m pytest", prompt)
        self.assertIn("Do not rely on `/usr/bin/python`", prompt)

    def test_materialize_degraded_workspace_copies_and_degrades_python_targets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            clean = root / "clean"
            clean.mkdir()
            target = clean / "pkg"
            target.mkdir()
            source = target / "module.py"
            source.write_text('"""docs"""\n# comment\nvalue = 1\n', encoding="utf-8")

            degraded = root / "degraded"
            materialize_degraded_workspace(
                clean_dir=clean,
                degraded_dir=degraded,
                condition="comments_docstrings",
                targets={"target_files": ["pkg/module.py"]},
            )

            degraded_source = degraded / "pkg" / "module.py"
            self.assertTrue(degraded_source.exists())
            text = degraded_source.read_text(encoding="utf-8")
            self.assertNotIn("docs", text)
            self.assertNotIn("# comment", text)
            self.assertIn("value = 1", text)

    def test_materialize_degraded_workspace_removes_selected_test_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            clean = root / "clean"
            test_dir = clean / "testing"
            helper_dir = clean / "helpers"
            test_dir.mkdir(parents=True)
            helper_dir.mkdir()
            (test_dir / "test_target.py").write_text("def test_it():\n    assert True\n", encoding="utf-8")
            (helper_dir / "support.py").write_text("VALUE = 1\n", encoding="utf-8")

            degraded = root / "degraded"
            materialize_degraded_workspace(
                clean_dir=clean,
                degraded_dir=degraded,
                condition="remove_tests",
                targets={
                    "delete_files": ["testing/test_target.py"],
                    "preserve_files": ["helpers/support.py"],
                },
            )

            self.assertFalse((degraded / "testing" / "test_target.py").exists())
            self.assertTrue((degraded / "helpers" / "support.py").exists())

    def test_materialize_clean_workspace_can_clone_from_local_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            source.mkdir()
            subprocess.run(["git", "init"], cwd=source, check=True, capture_output=True, text=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=source,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=source,
                check=True,
                capture_output=True,
                text=True,
            )
            tracked = source / "module.py"
            tracked.write_text('"""docs"""\nvalue = 1\n', encoding="utf-8")
            subprocess.run(["git", "add", "module.py"], cwd=source, check=True, capture_output=True, text=True)
            subprocess.run(
                ["git", "commit", "-m", "initial"],
                cwd=source,
                check=True,
                capture_output=True,
                text=True,
            )
            base_commit = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=source,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()

            target = root / "workspace"
            materialize_clean_workspace(
                snapshot=TaskSnapshot(
                    schema_version="0.1.0",
                    dataset_name="SWE-bench/SWE-bench_Verified",
                    dataset_split="test",
                    instance_id="example__repo-1",
                    repo="example/repo",
                    base_commit=base_commit,
                    version="0.1",
                    problem_statement="irrelevant",
                    hints_text=None,
                    source_files=["module.py"],
                    test_files=[],
                    fail_to_pass=[],
                    pass_to_pass=[],
                    patch="",
                    test_patch="",
                ),
                target_dir=target,
                source_clone_dir=source,
            )

            self.assertTrue((target / "module.py").exists())
            self.assertIn("value = 1", (target / "module.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
