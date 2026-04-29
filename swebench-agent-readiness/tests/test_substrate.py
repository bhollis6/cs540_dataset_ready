from __future__ import annotations

import unittest

from src.substrate.swebench_verified import TaskSnapshot, extract_changed_files


class SubstrateTest(unittest.TestCase):
    def test_extract_changed_files_from_unified_diff(self) -> None:
        patch = """diff --git a/src/example.py b/src/example.py
--- a/src/example.py
+++ b/src/example.py
@@ -1 +1 @@
-old = 1
+new = 2
diff --git a/tests/test_example.py b/tests/test_example.py
--- a/tests/test_example.py
+++ b/tests/test_example.py
@@ -1 +1 @@
-assert 1
+assert 2
"""

        files = extract_changed_files(patch)

        self.assertEqual(files, ["src/example.py", "tests/test_example.py"])

    def test_snapshot_can_render_back_to_swebench_instance_shape(self) -> None:
        snapshot = TaskSnapshot(
            schema_version="0.1.0",
            dataset_name="dataset",
            dataset_split="test",
            instance_id="example__1",
            repo="org/repo",
            base_commit="abc123",
            version="1.0",
            problem_statement="Fix it",
            hints_text="Hint",
            source_files=["src/example.py"],
            test_files=["tests/test_example.py"],
            fail_to_pass=["tests/test_example.py::test_one"],
            pass_to_pass=["tests/test_example.py::test_two"],
            patch="diff --git a/src/example.py b/src/example.py",
            test_patch="diff --git a/tests/test_example.py b/tests/test_example.py",
            environment_setup_commit="env456",
            difficulty="medium",
        )

        row = snapshot.to_swebench_instance()

        self.assertEqual(row["instance_id"], "example__1")
        self.assertEqual(row["FAIL_TO_PASS"], ["tests/test_example.py::test_one"])
        self.assertEqual(row["PASS_TO_PASS"], ["tests/test_example.py::test_two"])
        self.assertEqual(row["environment_setup_commit"], "env456")
        self.assertEqual(row["difficulty"], "medium")


if __name__ == "__main__":
    unittest.main()
