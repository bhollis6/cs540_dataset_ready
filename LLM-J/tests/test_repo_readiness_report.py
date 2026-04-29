"""Tests for the sibling repo-readiness helper."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_repo_readiness_module():
    module_path = Path(__file__).resolve().parents[2] / "degradation" / "repo_readiness.py"
    module_dir = str(module_path.parent)
    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)

    spec = importlib.util.spec_from_file_location("degradation_repo_readiness", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load repo readiness from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, module)
    spec.loader.exec_module(module)
    return module


def test_collect_repo_readiness_reports_all_degradation_surfaces(tmp_path: Path):
    module = _load_repo_readiness_module()
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "tests" / "fixtures").mkdir(parents=True)

    (repo / "src" / "service.py").write_text(
        '"""Service docs."""\n'
        "class UsefulService:\n"
        "    def render_output(self, value: int) -> int:\n"
        "        # Important comment\n"
        "        formatted_output: int = value + 1\n"
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
    (repo / "tests" / "fixtures" / "sample.json").write_text("{}", encoding="utf-8")
    (repo / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")

    report = module.collect_repo_readiness(repo, sample_limit=2)

    assert report["type_hints"]["total_annotations"] >= 3
    assert report["comments_docstrings"]["total_signal_count"] >= 2
    assert report["test_surface"]["executable_test_file_count"] == 1
    assert report["test_surface"]["test_support_file_count"] >= 2
    assert report["naming"]["rename_counts"]["total"] >= 4
    assert set(report["readiness"]) == {
        "type_hints",
        "comments_docstrings",
        "remove_tests",
        "naming",
    }
    assert report["overall"]["status"] in {"PASS", "REVIEW"}
