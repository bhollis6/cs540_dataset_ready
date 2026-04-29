"""Regression tests for the sibling naming degrader."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_naming_module():
    module_path = Path(__file__).resolve().parents[2] / "degradation" / "naming_conventions.py"
    spec = importlib.util.spec_from_file_location("degradation_naming_conventions", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load naming degrader from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, module)
    spec.loader.exec_module(module)
    return module


def test_naming_degrader_preserves_test_discovery_hooks(tmp_path: Path):
    module = _load_naming_module()
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "tests").mkdir()

    (repo / "src" / "app.py").write_text(
        "def public_api(value):\n"
        "    result_value = value + 1\n"
        "    return result_value\n",
        encoding="utf-8",
    )
    (repo / "tests" / "test_sample.py").write_text(
        "import unittest\n\n"
        "def test_public_case():\n"
        "    assertion_target = 1\n"
        "    assert assertion_target == 1\n\n"
        "class TestThing(unittest.TestCase):\n"
        "    def setUp(self):\n"
        "        setup_buffer = 1\n"
        "        self.value = setup_buffer\n\n"
        "    def test_case(self):\n"
        "        case_value = self.value\n"
        "        self.assertEqual(case_value, 1)\n",
        encoding="utf-8",
    )
    (repo / "tests" / "conftest.py").write_text(
        "import pytest\n\n"
        "@pytest.fixture\n"
        "def test_client_factory():\n"
        "    hook_state = True\n"
        "    return hook_state\n\n"
        "def pytest_configure(config):\n"
        "    hook_state = True\n"
        "    return hook_state\n",
        encoding="utf-8",
    )

    forbidden = module._collect_forbidden(repo)
    symbols = module._collect_symbols(repo, forbidden)
    symbol_pairs = {(sym.kind, sym.name) for sym in symbols}

    assert ("class", "TestThing") not in symbol_pairs
    assert ("function", "test_public_case") not in symbol_pairs
    assert ("function", "setUp") not in symbol_pairs
    assert ("function", "test_client_factory") not in symbol_pairs
    assert ("function", "pytest_configure") not in symbol_pairs

    assert ("function", "public_api") in symbol_pairs
    assert ("variable", "assertion_target") in symbol_pairs
    assert ("variable", "setup_buffer") in symbol_pairs
    assert ("variable", "hook_state") in symbol_pairs


def test_naming_degrader_collects_safe_bound_locals(tmp_path: Path):
    module = _load_naming_module()
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)

    (repo / "src" / "worker.py").write_text(
        "def process_records(records):\n"
        "    total_count = 0\n"
        "    for user_record, status_flag in records:\n"
        "        total_count += 1\n"
        "        with open('data.txt') as file_handle:\n"
        "            payload_text = file_handle.read()\n"
        "        if payload_block := payload_text:\n"
        "            final_value = payload_block\n"
        "    return total_count\n",
        encoding="utf-8",
    )

    forbidden = module._collect_forbidden(repo)
    symbols = module._collect_symbols(repo, forbidden)
    variable_names = {sym.name for sym in symbols if sym.kind == "variable"}

    assert "total_count" in variable_names
    assert "user_record" in variable_names
    assert "status_flag" in variable_names
    assert "file_handle" in variable_names
    assert "payload_text" in variable_names
    assert "payload_block" in variable_names
    assert "final_value" in variable_names


def test_naming_degrader_skips_placeholders_and_short_class_names(tmp_path: Path):
    module = _load_naming_module()
    repo = tmp_path / "repo"
    (repo / "tests").mkdir(parents=True)

    (repo / "tests" / "test_short_names.py").write_text(
        "class A:\n"
        "    pass\n\n"
        "class UsefulContainer:\n"
        "    pass\n\n"
        "def helper():\n"
        "    _ = 1\n"
        "    named_value = 2\n"
        "    return named_value\n",
        encoding="utf-8",
    )

    forbidden = module._collect_forbidden(repo)
    symbols = module._collect_symbols(repo, forbidden)
    symbol_pairs = {(sym.kind, sym.name) for sym in symbols}

    assert ("class", "A") not in symbol_pairs
    assert ("variable", "_") not in symbol_pairs
    assert ("class", "UsefulContainer") in symbol_pairs
    assert ("variable", "named_value") in symbol_pairs


def test_naming_degrader_find_near_falls_back_to_whole_file_search():
    module = _load_naming_module()
    source = (
        "def alpha():\n"
        "    pass\n\n"
        "def beta():\n"
        "    pass\n"
    )

    # Simulate a stale offset that no longer lands near the symbol after
    # earlier edits shifted the file.
    stale_offset = 0
    resolved = module._find_near(source, "beta", stale_offset)

    assert resolved == source.index("beta")


def test_naming_degrader_stats_report_skip_breakdown():
    module = _load_naming_module()
    stats = module.RenameStats(classes=1, functions=2, variables=3)
    stats.record_skip("offset_not_found", "response")
    stats.record_skip("refactoring_error", "response")
    stats.record_skip("refactoring_error", "close")

    report = stats.to_dict(top_n=2)

    assert report["renamed"]["total"] == 6
    assert report["skipped"]["total"] == 3
    assert report["skipped"]["offset_not_found"] == 1
    assert report["skipped"]["refactoring_error"] == 2
    assert report["top_skipped_names"] == [
        {"name": "response", "count": 2},
        {"name": "close", "count": 1},
    ]
