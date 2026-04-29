from __future__ import annotations

import unittest

from src.degradation.comments_docstrings import strip_comments_and_docstrings


class CommentsDocstringsTest(unittest.TestCase):
    def test_removes_docstrings_and_comments_but_keeps_literals(self) -> None:
        source = '''"""module docs"""

# top comment
VALUE = "keep me"  # inline comment

def example() -> str:
    """function docs"""
    payload = "still here"
    return payload
'''
        transformed = strip_comments_and_docstrings(source)

        self.assertNotIn("module docs", transformed)
        self.assertNotIn("function docs", transformed)
        self.assertNotIn("# top comment", transformed)
        self.assertNotIn("# inline comment", transformed)
        self.assertIn('VALUE = "keep me"', transformed)
        self.assertIn('payload = "still here"', transformed)

    def test_preserves_shebang_and_encoding_comments(self) -> None:
        source = """#!/usr/bin/env python\n# -*- coding: utf-8 -*-\n# remove me\nx = 1\n"""
        transformed = strip_comments_and_docstrings(source)

        self.assertIn("#!/usr/bin/env python", transformed)
        self.assertIn("coding: utf-8", transformed)
        self.assertNotIn("# remove me", transformed)


if __name__ == "__main__":
    unittest.main()
