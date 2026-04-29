from __future__ import annotations

import unittest

from src.degradation.type_hints import strip_type_hints


class TypeHintsTest(unittest.TestCase):
    def test_strips_safe_annotations_without_removing_comments(self) -> None:
        source = """# keep comment
def example(value: int) -> str:
    result: str = str(value)
    return result
"""

        transformed, stats = strip_type_hints(source)

        self.assertIn("# keep comment", transformed)
        self.assertIn("def example(value):", transformed)
        self.assertIn("result = str(value)", transformed)
        self.assertNotIn("-> str", transformed)
        self.assertEqual(stats.hints_removed, 3)

    def test_preserves_dataclass_annotations(self) -> None:
        source = """from dataclasses import dataclass

@dataclass
class Item:
    value: int
"""

        transformed, stats = strip_type_hints(source)

        self.assertIn("value: int", transformed)
        self.assertEqual(stats.hints_removed, 0)


if __name__ == "__main__":
    unittest.main()
