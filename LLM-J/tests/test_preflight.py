"""Tests for Stage 2 preflight helpers."""

from __future__ import annotations

from pathlib import Path

from src.deep_eval import preflight
from src.deep_eval.models import PreflightResult
from src.deep_eval.preflight import (
    _build_install_commands,
    _build_post_install_commands,
    _looks_like_pytest_execution_error,
    _parse_pytest_result_line,
    _python_module_available,
    _run_pytest,
    _venv_python_path,
)
from src.profiles import repo_profile_from_dict


def test_build_install_commands_prefers_repo_requirements(tmp_path: Path):
    (tmp_path / "requirements.txt").write_text("-e .\ntrio\n")
    (tmp_path / "requirements-test.txt").write_text("pytest\n")
    python_executable = tmp_path / ".llmj-preflight-venv" / "bin" / "python"

    commands = _build_install_commands(tmp_path, python_executable=python_executable)

    assert commands[0][:4] == [str(python_executable), "-m", "pip", "install"]
    assert commands[0][-2:] == ["-r", str(tmp_path / "requirements.txt")]
    assert commands[1][-2:] == ["-r", str(tmp_path / "requirements-test.txt")]
    assert any(command[-2:] == ["-e", f"{tmp_path}[test,tests,dev]"] for command in commands)
    assert commands[-1][-2:] == ["-e", str(tmp_path)]


def test_build_install_commands_prefers_repo_profile_commands(tmp_path: Path) -> None:
    python_executable = tmp_path / ".llmj-preflight-venv" / "bin" / "python"
    profile = repo_profile_from_dict({
        "repo": "encode/httpx",
        "environment": {
            "install_commands": ["uv pip install -e .[dev]"],
            "install_fallbacks": ["pip install -e ."],
        },
        "test": {"plugin_policy": {"mode": "default", "explicit_plugins": []}},
    })

    commands = _build_install_commands(
        tmp_path,
        python_executable=python_executable,
        repo_profile=profile,
    )

    assert commands[0][:4] == [str(python_executable), "-m", "pip", "install"]
    assert commands[0][-2:] == ["-e", ".[dev]"]
    assert commands[1][:4] == [str(python_executable), "-m", "pip", "install"]
    assert commands[1][-2:] == ["-e", "."]
    assert any(command[-2:] == ["-e", str(tmp_path)] for command in commands)


def test_normalize_profile_command_retargets_uv_pip_to_target_python(tmp_path: Path) -> None:
    python_executable = tmp_path / ".llmj-preflight-venv" / "bin" / "python"

    normalized = preflight._normalize_profile_command(
        "uv pip install -e .",
        python_executable=python_executable,
    )

    assert normalized == [str(python_executable), "-m", "pip", "install", "-e", "."]


def test_build_probe_environment_includes_environment_and_test_env_vars() -> None:
    profile = repo_profile_from_dict({
        "repo": "python-attrs/cattrs",
        "environment": {"env_vars": {"SETUPTOOLS_SCM_PRETEND_VERSION_FOR_CATTRS": "0.0"}},
        "test": {
            "env_vars": {"PYTEST_ADDOPTS": "-q"},
            "plugin_policy": {"mode": "default", "explicit_plugins": []},
        },
    })

    env = preflight.build_probe_environment(repo_profile=profile)

    assert env["SETUPTOOLS_SCM_PRETEND_VERSION_FOR_CATTRS"] == "0.0"
    assert env["PYTEST_ADDOPTS"] == "-q"
    assert env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"


def test_run_pytest_applies_profile_plugins_and_environment(tmp_path: Path, monkeypatch) -> None:
    worktree = tmp_path
    test_file = worktree / "tests" / "test_sample.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    python_executable = tmp_path / ".llmj-preflight-venv" / "bin" / "python"

    profile = repo_profile_from_dict({
        "repo": "python-attrs/cattrs",
        "environment": {"env_vars": {"SETUPTOOLS_SCM_PRETEND_VERSION": "0.0"}},
        "test": {
            "plugin_policy": {
                "mode": "explicit_only",
                "explicit_plugins": ["pytest_benchmark.plugin", "_hypothesis_pytestplugin"],
            },
            "env_vars": {"PYTEST_ADDOPTS": "-q"},
        },
    })

    captured: dict[str, object] = {}

    class DummyCompletedProcess:
        returncode = 0
        stdout = "tests/test_sample.py::test_ok PASSED\n"
        stderr = ""

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["env"] = kwargs["env"]
        return DummyCompletedProcess()

    monkeypatch.setattr(preflight, "_python_module_available", lambda *args, **kwargs: False)
    monkeypatch.setattr(preflight.subprocess, "run", fake_run)

    result = _run_pytest(
        worktree,
        ["tests/test_sample.py"],
        python_executable=python_executable,
        repo_profile=profile,
    )

    assert result.passed == {"tests/test_sample.py::test_ok"}
    assert captured["cmd"][:3] == [str(python_executable), "-m", "pytest"]
    assert "-p" in captured["cmd"]
    assert "pytest_benchmark.plugin" in captured["cmd"]
    assert "_hypothesis_pytestplugin" in captured["cmd"]
    assert captured["env"]["SETUPTOOLS_SCM_PRETEND_VERSION"] == "0.0"
    assert captured["env"]["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"


def test_install_project_records_timeout_attempts(tmp_path: Path, monkeypatch) -> None:
    python_executable = tmp_path / ".llmj-preflight-venv" / "bin" / "python"

    def fake_run(*args, **kwargs):
        raise preflight.subprocess.TimeoutExpired(cmd=kwargs.get("args", args[0]), timeout=1)

    monkeypatch.setattr(preflight.subprocess, "run", fake_run)

    result = preflight._install_project(
        tmp_path,
        python_executable=python_executable,
        install_timeout_seconds=1,
    )

    assert result.success is False
    assert result.attempts
    assert result.attempts[0]["status"] == "TIMEOUT"


def test_install_project_stops_on_terminal_install_error(tmp_path: Path, monkeypatch) -> None:
    python_executable = tmp_path / ".llmj-preflight-venv" / "bin" / "python"

    class DummyCompletedProcess:
        returncode = 1
        stdout = ""
        stderr = "WARNING: Retrying ... Failed to establish a new connection"

    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return DummyCompletedProcess()

    monkeypatch.setattr(preflight.subprocess, "run", fake_run)

    result = preflight._install_project(
        tmp_path,
        python_executable=python_executable,
        install_timeout_seconds=5,
    )

    assert result.success is False
    assert len(calls) == 1
    assert result.attempts
    assert result.attempts[0]["status"] == "FAIL"


def test_build_post_install_commands_respects_profile_and_bootstraps_pytest(
    tmp_path: Path,
    monkeypatch,
) -> None:
    python_executable = tmp_path / ".llmj-preflight-venv" / "bin" / "python"
    (tmp_path / "requirements.txt").write_text("pytest\n", encoding="utf-8")
    profile = repo_profile_from_dict({
        "repo": "encode/httpx",
        "environment": {
            "post_install": ["python -m pip install anyio"],
        },
        "test": {"plugin_policy": {"mode": "default", "explicit_plugins": []}},
    })
    monkeypatch.setattr(preflight, "_python_module_available", lambda *args, **kwargs: False)

    commands = _build_post_install_commands(
        tmp_path,
        python_executable=python_executable,
        repo_profile=profile,
    )

    assert commands[0][:4] == [str(python_executable), "-m", "pip", "install"]
    assert commands[0][-1] == "anyio"
    assert commands[1][-2:] == ["-r", str(tmp_path / "requirements.txt")]
    assert commands[2] == [str(python_executable), "-m", "pip", "install", "pytest"]


def test_install_project_runs_post_install_commands_after_success(tmp_path: Path, monkeypatch) -> None:
    python_executable = tmp_path / ".llmj-preflight-venv" / "bin" / "python"
    profile = repo_profile_from_dict({
        "repo": "encode/httpx",
        "environment": {
            "install_commands": ["python -m pip install -e ."],
            "post_install": ["python -m pip install anyio"],
        },
        "test": {"plugin_policy": {"mode": "default", "explicit_plugins": []}},
    })

    calls: list[list[str]] = []

    class DummyCompletedProcess:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setattr(preflight, "_python_module_available", lambda *args, **kwargs: False)

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return DummyCompletedProcess()

    monkeypatch.setattr(preflight.subprocess, "run", fake_run)

    result = preflight._install_project(
        tmp_path,
        python_executable=python_executable,
        repo_profile=profile,
        install_timeout_seconds=5,
    )

    assert result.success is True
    assert calls[0][-2:] == ["-e", "."]
    assert calls[1][-1] == "anyio"
    assert calls[2][-1] == "pytest"


def test_detect_pytest_execution_error_for_config_crash() -> None:
    output = (
        "Traceback (most recent call last):\n"
        "ModuleNotFoundError: No module named 'trio'\n"
        "pytest.PytestConfigWarning: failed to import filter module\n"
    )

    assert _looks_like_pytest_execution_error(output, returncode=1) is True


def test_detect_pytest_execution_error_for_missing_pytest_module() -> None:
    output = "/tmp/worktree/.llmj-preflight-venv/bin/python: No module named pytest\n"

    assert _looks_like_pytest_execution_error(output, returncode=1) is True


def test_parse_xdist_pytest_result_line_keeps_nodeid() -> None:
    line = "[gw0] [ 83%] FAILED tests/protocols/test_utils.py::test_get_local_addr"

    assert _parse_pytest_result_line(line, "FAILED") == (
        "tests/protocols/test_utils.py::test_get_local_addr"
    )


def test_preflight_treats_gold_fixed_collection_import_error_as_signal(
    tmp_path: Path,
    monkeypatch,
) -> None:
    python_executable = tmp_path / ".llmj-preflight-venv" / "bin" / "python"
    pytest_runs = iter([
        preflight.PytestRunResult(
            passed=set(),
            failed=set(),
            output=(
                "ERROR collecting tests/test_feature.py\n"
                "ImportError while importing test module\n"
                "E   ImportError: cannot import name 'NewClass' from 'pkg.module'\n"
            ),
            execution_error=True,
        ),
        preflight.PytestRunResult(
            passed={"tests/test_feature.py::test_new_behavior"},
            failed=set(),
            output="tests/test_feature.py::test_new_behavior PASSED\n",
            execution_error=False,
        ),
    ])
    applied_patches: list[str] = []

    monkeypatch.setattr(preflight, "_ensure_preflight_venv", lambda worktree: (python_executable, ""))
    monkeypatch.setattr(
        preflight,
        "_install_project",
        lambda *args, **kwargs: preflight.PreflightInstallResult(success=True),
    )
    monkeypatch.setattr(
        preflight,
        "_apply_patch",
        lambda worktree, diff_text: applied_patches.append(diff_text) or "git_apply",
    )
    monkeypatch.setattr(preflight, "_run_pytest", lambda *args, **kwargs: next(pytest_runs))

    result = preflight.run_preflight(
        worktree=tmp_path,
        candidate_id="repo_pr_1",
        patch_diff="source patch",
        test_diff="test patch",
        test_files=["tests/test_feature.py"],
    )

    assert result.status == "PASS"
    assert result.fail_to_pass_tests == ["tests/test_feature.py::test_new_behavior"]
    assert result.pass_to_pass_tests == []
    assert result.patch_apply_method == "test:git_apply, fix:git_apply"
    assert applied_patches == ["test patch", "source patch"]


def test_ignore_empty_collection_without_crash_markers() -> None:
    output = "============================= test session starts =============================\ncollected 0 items\n"

    assert _looks_like_pytest_execution_error(output, returncode=5) is False


def test_preflight_result_serializes_truncated_outputs() -> None:
    result = PreflightResult(
        candidate_id="repo_pr_1",
        status="FAIL",
        reason="No failing tests at base commit",
        base_test_output="base output",
        fixed_test_output="fixed output",
        install_success=True,
    )

    payload = result.to_dict()
    assert payload["base_test_output"] == "base output"
    assert payload["fixed_test_output"] == "fixed output"
    assert payload["install_success"] is True


def test_venv_python_path_points_inside_worktree(tmp_path: Path) -> None:
    python_executable = _venv_python_path(tmp_path / ".llmj-preflight-venv")
    assert python_executable.parts[-3:] == (".llmj-preflight-venv", "bin", "python")


def test_run_pytest_ignores_non_executable_test_assets(tmp_path: Path, monkeypatch) -> None:
    tests_dir = tmp_path / "tests"
    fixtures_dir = tests_dir / "fixtures"
    fixtures_dir.mkdir(parents=True)
    (tests_dir / "test_app.py").write_text("def test_ok():\n    assert True\n")
    (fixtures_dir / ".netrc").write_text("machine example.org\n")

    class DummyCompletedProcess:
        returncode = 0
        stdout = "tests/test_app.py::test_ok PASSED\n"
        stderr = ""

    monkeypatch.setattr(preflight, "_python_module_available", lambda *args, **kwargs: True)

    def fake_run(cmd, **kwargs):
        assert cmd[-1] == "tests/test_app.py"
        assert "tests/fixtures/.netrc" not in cmd
        assert "anyio.pytest_plugin" in cmd
        return DummyCompletedProcess()

    monkeypatch.setattr(preflight.subprocess, "run", fake_run)

    result = _run_pytest(
        tmp_path,
        ["tests/test_app.py", "tests/fixtures/.netrc"],
        python_executable=tmp_path / ".llmj-preflight-venv" / "bin" / "python",
    )

    assert result.execution_error is False
    assert result.passed == {"tests/test_app.py::test_ok"}


def test_python_module_available_uses_target_interpreter(tmp_path: Path, monkeypatch) -> None:
    python_executable = _venv_python_path(tmp_path / ".llmj-preflight-venv")

    class DummyCompletedProcess:
        returncode = 1
        stdout = ""
        stderr = ""

    def fake_run(cmd, **kwargs):
        assert cmd[0] == str(python_executable)
        assert "definitely_missing_plugin" in cmd[-1]
        return DummyCompletedProcess()

    monkeypatch.setattr(preflight.subprocess, "run", fake_run)

    assert _python_module_available(python_executable, "definitely_missing_plugin") is False
