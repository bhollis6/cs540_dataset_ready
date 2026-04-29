"""Tests for targeted Stage 4 degradation application."""

from __future__ import annotations

from pathlib import Path

from src.workflow.stage4_apply import apply_stage4_condition


def test_apply_stage4_remove_tests_deletes_only_targeted_files(tmp_path: Path):
    workspace = tmp_path / "workspace"
    tests_dir = workspace / "tests"
    tests_dir.mkdir(parents=True)
    (tests_dir / "test_api.py").write_text("def test_api():\n    assert True\n", encoding="utf-8")
    (tests_dir / "conftest.py").write_text("VALUE = 1\n", encoding="utf-8")
    (workspace / "src").mkdir()
    (workspace / "src" / "app.py").write_text("def app():\n    return 1\n", encoding="utf-8")

    result = apply_stage4_condition(
        workspace,
        "remove_tests",
        {
            "delete_files": ["tests/test_api.py"],
            "preserve_files": ["tests/conftest.py"],
        },
    )

    assert result["status"] == "PASS"
    assert not (tests_dir / "test_api.py").exists()
    assert (tests_dir / "conftest.py").exists()
    assert (workspace / "src" / "app.py").exists()
    assert result["summary"]["deleted_files"] == ["tests/test_api.py"]


def test_apply_stage4_comments_docstrings_only_touches_target_files(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    targeted = workspace / "targeted.py"
    untouched = workspace / "untouched.py"
    targeted.write_text(
        '"""Module doc."""\n'
        "# comment\n"
        "def fn():\n"
        '    """Function doc."""\n'
        "    return 1\n",
        encoding="utf-8",
    )
    untouched.write_text(
        '"""Keep me."""\n'
        "def other():\n"
        "    return 2\n",
        encoding="utf-8",
    )

    result = apply_stage4_condition(
        workspace,
        "comments_docstrings",
        {
            "target_files": ["targeted.py"],
        },
    )

    assert result["status"] == "PASS"
    assert '"""Module doc."""' not in targeted.read_text(encoding="utf-8")
    assert "# comment" not in targeted.read_text(encoding="utf-8")
    assert '"""Keep me."""' in untouched.read_text(encoding="utf-8")
    assert result["summary"]["cleaned_files"] == ["targeted.py"]
