"""Tests for the sibling naming audit helper."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_naming_audit_module():
    module_path = Path(__file__).resolve().parents[2] / "degradation" / "naming_audit.py"
    module_dir = str(module_path.parent)
    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)

    spec = importlib.util.spec_from_file_location("degradation_naming_audit", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load naming audit from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, module)
    spec.loader.exec_module(module)
    return module


def test_build_audit_report_collects_dry_run_summary(tmp_path: Path):
    module = _load_naming_audit_module()
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "tests").mkdir()

    (repo / "src" / "service.py").write_text(
        "class UsefulService:\n"
        "    def render_output(self, value):\n"
        "        formatted_output = value + 1\n"
        "        return formatted_output\n",
        encoding="utf-8",
    )
    (repo / "tests" / "test_service.py").write_text(
        "def test_render_output():\n"
        "    actual_result = 1\n"
        "    assert actual_result == 1\n",
        encoding="utf-8",
    )
    (repo / "tests" / "conftest.py").write_text(
        "import pytest\n\n"
        "@pytest.fixture\n"
        "def service_factory():\n"
        "    created_value = 1\n"
        "    return created_value\n",
        encoding="utf-8",
    )

    report = module.build_audit_report(repo, sample_limit=2, live=False)

    assert report["repo_path"] == str(repo.resolve())
    dry_run = report["dry_run"]
    assert dry_run["candidate_symbol_count"] >= 4
    assert dry_run["rename_counts"]["classes"] >= 1
    assert dry_run["rename_counts"]["functions"] >= 1
    assert dry_run["rename_counts"]["variables"] >= 2
    assert len(dry_run["sample_symbols"]["functions"]) <= 2
    assert "live_run" not in report
