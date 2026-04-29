from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.degradation.naming import collect_forbidden, collect_symbols, obfuscate_targets


class NamingTest(unittest.TestCase):
    def test_collects_symbols_but_preserves_test_discovery_names(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            (repo / "pkg").mkdir()
            (repo / "tests").mkdir()
            (repo / "pkg" / "module.py").write_text(
                "def public_api(value):\n"
                "    result_value = value + 1\n"
                "    return result_value\n",
                encoding="utf-8",
            )
            (repo / "tests" / "test_module.py").write_text(
                "def test_public_api():\n"
                "    assertion_target = 1\n"
                "    assert assertion_target == 1\n",
                encoding="utf-8",
            )

            symbols = collect_symbols(repo, collect_forbidden(repo))
            pairs = {(symbol.kind, symbol.name) for symbol in symbols}

        self.assertIn(("function", "public_api"), pairs)
        self.assertIn(("variable", "result_value"), pairs)
        self.assertNotIn(("function", "test_public_api"), pairs)
        self.assertIn(("variable", "assertion_target"), pairs)

    def test_obfuscates_targeted_files_with_rope(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            (repo / "pkg").mkdir()
            (repo / "pkg" / "__init__.py").write_text("", encoding="utf-8")
            module = repo / "pkg" / "module.py"
            module.write_text(
                "def public_api(value):\n"
                "    result_value = value + 1\n"
                "    return result_value\n",
                encoding="utf-8",
            )

            stats, candidates = obfuscate_targets(repo, {"pkg/module.py"})
            transformed = module.read_text(encoding="utf-8")

        self.assertGreaterEqual(candidates, 2)
        self.assertGreaterEqual(stats.total(), 1)
        self.assertNotIn("public_api", transformed)


if __name__ == "__main__":
    unittest.main()
