"""Tests for Stage 5 run execution orchestration."""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

import pytest

from src.profiles import repo_profile_from_dict
from src.workflow import stage5_runner


def test_execute_stage5_runs_writes_result_and_metrics(tmp_path: Path, monkeypatch):
    run_plan_dir = tmp_path / "run_plans"
    output_dir = tmp_path / "runs"
    clones_dir = tmp_path / "clones"
    run_plan_dir.mkdir()

    run_plan = {
        "repo": "encode/httpx",
        "repo_short": "httpx",
        "stage5_status": {"status": "READY"},
        "runs": [
            {
                "run_id": "httpx__httpx_pr_1__claude_code__clean__rep1",
                "repo": "encode/httpx",
                "candidate_id": "httpx_pr_1",
                "pr_number": 1,
                "condition": "clean",
                "replication": 1,
                "harness": {"id": "claude_code", "runner": "claude-code"},
                "output_paths": {
                    "root": "runs/httpx/httpx_pr_1/claude_code/clean/rep_1",
                },
            }
        ],
    }
    (run_plan_dir / "httpx_run_plan.json").write_text(json.dumps(run_plan), encoding="utf-8")

    def fake_materialize(**kwargs):
        run_root = output_dir / "runs/httpx/httpx_pr_1/claude_code/clean/rep_1"
        workspace = run_root / "workspace"
        logs = run_root / "logs"
        workspace.mkdir(parents=True)
        logs.mkdir(parents=True)
        metadata = {
            "workspace": {"path": str(workspace)},
            "oracle": {
                "fail_to_pass_tests": ["tests/test_api.py::test_fix"],
                "pass_to_pass_tests": ["tests/test_api.py::test_existing"],
            },
            "task_prompt": {
                "title": "Fix stale connection reuse",
                "description": "Reproduce and fix the stale connection behavior.",
            },
            "condition": "clean",
        }
        (run_root / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
        return output_dir / "httpx_stage4_materialization.json"

    monkeypatch.setattr(stage5_runner, "materialize_stage4_runs", fake_materialize)
    monkeypatch.setattr(
        stage5_runner,
        "_run_agent_harness",
        lambda **kwargs: stage5_runner.HarnessRunResult(
            harness_id="claude_code",
            runner="claude-code",
            command=["claude", "-p", "prompt"],
            started_at="2026-04-21T00:00:00+00:00",
            completed_at="2026-04-21T00:00:05+00:00",
            duration_seconds=5.0,
            exit_code=0,
            stdout_path=str(output_dir / "stdout.log"),
            stderr_path=str(output_dir / "stderr.log"),
            final_message_path=None,
            parsed_response={"summary": "done", "outcome": "completed", "tests_run": [], "files_changed": [], "blockers": []},
        ),
    )
    monkeypatch.setattr(
        stage5_runner,
        "_run_post_run_oracle",
        lambda **kwargs: {
            "task_success": True,
            "execution_error": False,
            "reason": "oracle_pass",
            "duration_seconds": 2.0,
            "command": "python -m pytest tests/test_api.py::test_fix",
            "passed": ["tests/test_api.py::test_fix", "tests/test_api.py::test_existing"],
            "failed": [],
            "fail_to_pass_tests": ["tests/test_api.py::test_fix"],
            "pass_to_pass_tests": ["tests/test_api.py::test_existing"],
            "fail_to_pass_passed": ["tests/test_api.py::test_fix"],
            "fail_to_pass_failed": [],
            "pass_to_pass_failed": [],
            "output_path": str(output_dir / "post_run_test_output.txt"),
        },
    )
    def fake_write_git_diff(workspace_path: Path, output_path: Path) -> Path:
        output_path.write_text("diff", encoding="utf-8")
        return output_path

    monkeypatch.setattr(stage5_runner, "_write_git_diff", fake_write_git_diff)
    monkeypatch.setattr(stage5_runner, "_changed_files", lambda workspace_path: ["httpx/_client.py"])

    summary_path = stage5_runner.execute_stage5_runs(
        repo="encode/httpx",
        run_plan_dir=run_plan_dir,
        clones_dir=clones_dir,
        output_dir=output_dir,
    )

    summary = json.loads(summary_path.read_text())
    assert summary["summary"]["success"] == 1

    run_root = output_dir / "runs/httpx/httpx_pr_1/claude_code/clean/rep_1"
    result = json.loads((run_root / "result.json").read_text())
    metrics = json.loads((run_root / "metrics.json").read_text())
    assert result["status"] == "SUCCESS"
    assert result["completion_reason"] == "oracle_pass"
    assert metrics["task_success"] is True
    assert metrics["edits_applied"] == 1


def test_execute_stage5_runs_skips_existing_results(tmp_path: Path, monkeypatch):
    run_plan_dir = tmp_path / "run_plans"
    output_dir = tmp_path / "runs"
    clones_dir = tmp_path / "clones"
    run_plan_dir.mkdir()

    run_plan = {
        "repo": "encode/httpx",
        "repo_short": "httpx",
        "stage5_status": {"status": "READY"},
        "runs": [
            {
                "run_id": "httpx__httpx_pr_1__claude_code__clean__rep1",
                "repo": "encode/httpx",
                "candidate_id": "httpx_pr_1",
                "condition": "clean",
                "replication": 1,
                "harness": {"id": "claude_code", "runner": "claude-code"},
                "output_paths": {
                    "root": "runs/httpx/httpx_pr_1/claude_code/clean/rep_1",
                },
            }
        ],
    }
    (run_plan_dir / "httpx_run_plan.json").write_text(json.dumps(run_plan), encoding="utf-8")

    run_root = output_dir / "runs/httpx/httpx_pr_1/claude_code/clean/rep_1"
    run_root.mkdir(parents=True)
    (run_root / "result.json").write_text(json.dumps({"status": "SUCCESS"}), encoding="utf-8")
    (run_root / "metrics.json").write_text(json.dumps({"task_success": True}), encoding="utf-8")

    monkeypatch.setattr(stage5_runner, "materialize_stage4_runs", lambda **kwargs: output_dir / "noop.json")

    summary_path = stage5_runner.execute_stage5_runs(
        repo="encode/httpx",
        run_plan_dir=run_plan_dir,
        clones_dir=clones_dir,
        output_dir=output_dir,
    )

    summary = json.loads(summary_path.read_text())
    assert summary["summary"]["skipped"] == 1
    assert summary["results"][0]["result_path"] == str(run_root / "result.json")
    assert summary["results"][0]["metrics_path"] == str(run_root / "metrics.json")


def test_build_agent_prompt_summarizes_large_pass_to_pass_surface():
    metadata = {
        "task_prompt": {
            "title": "Fix auth behavior",
            "description": "Implement the requested auth change.",
        },
        "oracle": {
            "fail_to_pass_tests": [
                "tests/client/test_auth.py::test_fix_one",
                "tests/client/test_auth.py::test_fix_two",
            ],
            "pass_to_pass_tests": [
                "tests/client/test_auth.py::test_regression_a",
                "tests/client/test_auth.py::test_regression_b",
                "tests/client/test_auth.py::test_regression_c",
                "tests/client/test_auth.py::test_regression_d",
                "tests/client/test_auth.py::test_regression_e",
                "tests/client/test_auth.py::test_regression_f",
                "tests/client/test_properties.py::test_regression_g",
                "tests/client/test_properties.py::test_regression_h",
                "tests/test_utils.py::test_regression_i",
            ],
        },
    }

    prompt = stage5_runner._build_agent_prompt(metadata)

    assert "You get one final submission for this task." in prompt
    assert "run as many local checks as you want before you submit" in prompt
    assert "Work however you think is best. Read, test, and validate as much as you need before submitting." in prompt
    assert "Submit only when you are ready." in prompt
    assert "Do not attempt exhaustive full-suite validation" not in prompt
    assert "minimal targeted regression subset" not in prompt
    assert "Final oracle evaluation will check the broader regression surface below." in prompt
    assert "- `9` regression checks across `3` files" in prompt
    assert "- `tests/client/test_auth.py` (6 checks)" in prompt
    assert "- `tests/client/test_properties.py` (2 checks)" in prompt
    assert "- `tests/test_utils.py` (1 check)" in prompt
    assert "test_regression_a" not in prompt


def test_build_agent_prompt_condenses_long_task_description():
    metadata = {
        "task_prompt": {
            "title": "Fix auth behavior",
            "description": "\n".join(
                [
                    "This task changes netrc auth behavior.",
                    "",
                    "```python",
                    "client = httpx.Client()",
                    "client.get('https://example.com')",
                    "```",
                    "",
                    "After the example, the description keeps going with more context.",
                ]
            ),
        },
        "oracle": {
            "fail_to_pass_tests": ["tests/client/test_auth.py::test_fix_one"],
            "pass_to_pass_tests": [],
        },
    }

    prompt = stage5_runner._build_agent_prompt(metadata)

    assert "This task changes netrc auth behavior." in prompt
    assert "[code example omitted for brevity]" in prompt
    assert "client = httpx.Client()" not in prompt
    assert "After the example, the description keeps going with more context." in prompt


def test_condense_task_description_truncates_large_bodies():
    description = ("Important context. " * 300).strip()

    condensed = stage5_runner._condense_task_description(description, max_chars=400)

    assert len(condensed) <= 450
    assert condensed.endswith("[description truncated for prompt efficiency]")


def test_run_agent_harness_adds_isolation_flags(monkeypatch, tmp_path: Path):
    workspace = tmp_path / "workspace"
    logs = tmp_path / "logs"
    workspace.mkdir()
    logs.mkdir()

    calls: list[dict[str, object]] = []

    def fake_run_process(command, *, cwd, timeout, env):
        calls.append({"command": command, "cwd": cwd, "timeout": timeout, "env": env})
        return 0, json.dumps({"summary": "done", "outcome": "completed", "tests_run": [], "files_changed": [], "blockers": []}), ""

    monkeypatch.setattr(stage5_runner, "_run_process_with_timeout", fake_run_process)
    monkeypatch.setattr(stage5_runner, "_prepare_codex_home", lambda: tmp_path / "codex-home")
    monkeypatch.setattr(stage5_runner.shutil, "which", lambda binary: f"/usr/bin/{binary}")

    claude_result = stage5_runner._run_agent_harness(
        run={"harness": {"id": "claude_code", "runner": "claude-code"}},
        workspace_path=workspace,
        logs_dir=logs,
        prompt="fix the bug",
        timeout_seconds=30,
    )
    codex_result = stage5_runner._run_agent_harness(
        run={"harness": {"id": "codex_cli", "runner": "codex-cli"}},
        workspace_path=workspace,
        logs_dir=logs,
        prompt="fix the bug",
        timeout_seconds=30,
    )

    claude_command = calls[0]["command"]
    codex_command = calls[1]["command"]
    assert "--effort" in claude_command
    assert "medium" in claude_command
    assert "--allowedTools" in claude_command
    assert "Bash,Read,Edit,MultiEdit,Write,Glob,Grep,LS" in claude_command
    assert "--setting-sources" in claude_command
    assert "local" in claude_command
    assert "--disable-slash-commands" in claude_command
    assert "--strict-mcp-config" in claude_command
    assert "--ignore-user-config" in codex_command
    assert "--ignore-rules" in codex_command
    assert Path(codex_command[codex_command.index("-C") + 1]).is_absolute()
    assert Path(codex_command[codex_command.index("-o") + 1]).is_absolute()
    assert Path(codex_command[codex_command.index("--output-schema") + 1]).is_absolute()
    assert Path(claude_command[claude_command.index("--add-dir") + 1]).is_absolute()
    assert Path(claude_command[claude_command.index("--debug-file") + 1]).is_absolute()
    assert claude_result.exit_code == 0
    assert codex_result.exit_code == 0


def test_changed_files_filters_harness_artifacts_and_normalizes_renames(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    subprocess.run(["git", "init"], cwd=workspace, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "LLM-J Tests"], cwd=workspace, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "llmj@example.com"], cwd=workspace, check=True, capture_output=True, text=True)

    tracked = workspace / "tracked.py"
    tracked.write_text("print('old')\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.py"], cwd=workspace, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=workspace, check=True, capture_output=True, text=True)

    subprocess.run(["git", "mv", "tracked.py", "renamed.py"], cwd=workspace, check=True, capture_output=True, text=True)
    (workspace / ".codex").mkdir()
    (workspace / ".codex" / "session.json").write_text("{}", encoding="utf-8")
    (workspace / ".claude").mkdir()
    (workspace / ".claude" / "trace.json").write_text("{}", encoding="utf-8")
    (workspace / "new_module.py").write_text("print('new')\n", encoding="utf-8")

    changed = sorted(stage5_runner._changed_files(workspace))
    assert changed == ["new_module.py", "renamed.py"]


def test_run_post_run_oracle_classifies_missing_targets(tmp_path: Path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    python_executable = tmp_path / "python"
    python_executable.write_text("", encoding="utf-8")
    output_path = tmp_path / "oracle.txt"

    monkeypatch.setattr(
        stage5_runner,
        "_prepare_oracle_evaluation_workspace",
        lambda **kwargs: {
            "success": True,
            "reason": "oracle_workspace_prepared",
            "output": "",
            "workspace": str(workspace),
            "source_patch_apply_method": "empty",
            "untracked_source_files": [],
        },
    )
    monkeypatch.setattr(
        stage5_runner,
        "_prepare_oracle_tests",
        lambda workspace_path, candidate_path: {
            "success": True,
            "reason": "oracle_tests_prepared",
            "output": "",
            "patch_apply_method": "git_apply",
            "restored_test_files": ["tests/test_api.py"],
        },
    )
    monkeypatch.setattr(stage5_runner, "_ensure_preflight_venv", lambda workspace_path: (python_executable, ""))
    monkeypatch.setattr(
        stage5_runner,
        "_install_workspace",
        lambda workspace_path, python_executable, repo_profile=None: (True, ""),
    )
    monkeypatch.setattr(
        stage5_runner,
        "_run_pytest_targets",
        lambda *args, **kwargs: {
            "passed": [],
            "failed": [],
            "output": "ERROR: not found: tests/test_api.py::test_fix\n",
            "execution_error": True,
            "missing_targets": ["tests/test_api.py::test_fix"],
        },
    )

    oracle = stage5_runner._run_post_run_oracle(
        run={"repo": "encode/httpx", "output_paths": {"root": "noop"}, "workspace": {"base_commit_sha": "abc"}, "condition": "clean"},
        run_root=tmp_path / "run_root",
        clones_dir=tmp_path / "clones",
        workspace_path=workspace,
        candidate_path=tmp_path / "candidate.json",
        fail_to_pass_tests=["tests/test_api.py::test_fix"],
        pass_to_pass_tests=["tests/test_api.py::test_existing"],
        output_path=output_path,
    )

    assert oracle["execution_error"] is True
    assert oracle["reason"] == "oracle_targets_not_found"
    assert oracle["missing_targets"] == [
        "tests/test_api.py::test_existing",
        "tests/test_api.py::test_fix",
    ]


def test_run_process_with_timeout_terminates_process_group(tmp_path: Path):
    marker = tmp_path / "child-alive.txt"
    script = tmp_path / "fake-claude.sh"
    script.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "set -eu",
                f"(sleep 2; printf 'alive' > {marker}) &",
                "sleep 30",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | 0o111)

    with pytest.raises(subprocess.TimeoutExpired):
        stage5_runner._run_process_with_timeout(
            [str(script)],
            cwd=str(tmp_path),
            timeout=1,
            env={**os.environ, "PYTHONUTF8": "1"},
        )

    time.sleep(3)
    assert not marker.exists()


def test_sync_codex_home_files_refreshes_existing_auth(tmp_path: Path):
    source = tmp_path / "home" / ".codex"
    target = tmp_path / "repo" / ".codex-stage5-home"
    source.mkdir(parents=True)
    target.mkdir(parents=True)

    (source / "auth.json").write_text('{"token": "fresh"}', encoding="utf-8")
    (source / "config.toml").write_text("model = 'current'\n", encoding="utf-8")
    (source / "rules").mkdir()
    (source / "rules" / "default.rules").write_text("fresh rules", encoding="utf-8")

    (target / "auth.json").write_text('{"token": "stale"}', encoding="utf-8")
    (target / "config.toml").write_text("model = 'stale'\n", encoding="utf-8")

    stage5_runner._sync_codex_home_files(source=source, target=target)

    assert (target / "auth.json").read_text(encoding="utf-8") == '{"token": "fresh"}'
    assert (target / "config.toml").read_text(encoding="utf-8") == "model = 'current'\n"
    assert (target / "rules" / "default.rules").read_text(encoding="utf-8") == "fresh rules"


def test_run_process_with_timeout_closes_stdin(monkeypatch):
    captured: dict[str, object] = {}

    class DummyProcess:
        returncode = 0
        pid = 1234

        def communicate(self, timeout=None):
            captured["timeout"] = timeout
            return ("ok", "")

        def poll(self):
            return self.returncode

    def fake_popen(*args, **kwargs):
        captured["kwargs"] = kwargs
        return DummyProcess()

    monkeypatch.setattr(stage5_runner.subprocess, "Popen", fake_popen)

    exit_code, stdout, stderr = stage5_runner._run_process_with_timeout(
        ["echo", "ok"],
        cwd=".",
        timeout=5,
        env={**os.environ, "PYTHONUTF8": "1"},
    )

    assert exit_code == 0
    assert stdout == "ok"
    assert stderr == ""
    assert captured["kwargs"]["stdin"] is stage5_runner.subprocess.DEVNULL


def test_pytest_file_targets_collapses_nodeids_to_unique_files():
    assert stage5_runner._pytest_file_targets(
        [
            "tests/test_api.py::test_fix",
            "tests/test_api.py::test_existing[param]",
            "tests/test_other.py::test_other",
        ]
    ) == ["tests/test_api.py", "tests/test_other.py"]


def test_evaluate_expected_targets_uses_normalized_function_fallback():
    evaluation = stage5_runner._evaluate_expected_targets(
        expected_targets=[
            "tests/test_api.py::test_parametrized[alpha]",
            "tests/test_api.py::test_fix",
        ],
        passed_targets=[
            "tests/test_api.py::test_parametrized[case0]",
            "tests/test_api.py::test_fix",
        ],
        failed_targets=[],
    )

    assert evaluation["missing_targets"] == []
    assert evaluation["status_by_target"]["tests/test_api.py::test_parametrized[alpha]"] == "passed"
    assert evaluation["status_by_target"]["tests/test_api.py::test_fix"] == "passed"


def test_capture_agent_source_changes_excludes_candidate_test_surface(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    subprocess.run(["git", "init"], cwd=workspace, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "LLM-J Tests"], cwd=workspace, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "llmj@example.com"], cwd=workspace, check=True, capture_output=True, text=True)

    (workspace / "pkg").mkdir()
    (workspace / "tests").mkdir()
    (workspace / "pkg" / "module.py").write_text("value = 1\n", encoding="utf-8")
    (workspace / "tests" / "test_api.py").write_text("def test_old():\n    pass\n", encoding="utf-8")
    subprocess.run(["git", "add", "pkg/module.py", "tests/test_api.py"], cwd=workspace, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=workspace, check=True, capture_output=True, text=True)

    (workspace / "pkg" / "module.py").write_text("value = 2\n", encoding="utf-8")
    (workspace / "pkg" / "new_file.py").write_text("created = True\n", encoding="utf-8")
    (workspace / "tests" / "test_api.py").write_text("def test_new():\n    assert True\n", encoding="utf-8")

    candidate_path = tmp_path / "candidate.json"
    candidate_path.write_text(
        json.dumps(
            {
                "test_files": ["tests/test_api.py"],
                "test_support_files": [],
            }
        ),
        encoding="utf-8",
    )

    patch, untracked = stage5_runner._capture_agent_source_changes(
        agent_workspace=workspace,
        candidate_path=candidate_path,
    )

    assert "pkg/module.py" in patch
    assert "tests/test_api.py" not in patch
    assert untracked == ["pkg/new_file.py"]


def test_capture_agent_source_changes_includes_staged_tracked_edits(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    subprocess.run(["git", "init"], cwd=workspace, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "LLM-J Tests"], cwd=workspace, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "llmj@example.com"], cwd=workspace, check=True, capture_output=True, text=True)

    (workspace / "pkg").mkdir()
    tracked = workspace / "pkg" / "module.py"
    tracked.write_text("value = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "pkg/module.py"], cwd=workspace, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=workspace, check=True, capture_output=True, text=True)

    tracked.write_text("value = 2\n", encoding="utf-8")
    subprocess.run(["git", "add", "pkg/module.py"], cwd=workspace, check=True, capture_output=True, text=True)

    patch, untracked = stage5_runner._capture_agent_source_changes(
        agent_workspace=workspace,
        candidate_path=None,
    )

    assert "pkg/module.py" in patch
    assert "+value = 2" in patch
    assert untracked == []


def test_write_git_diff_includes_staged_tracked_edits(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    subprocess.run(["git", "init"], cwd=workspace, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "LLM-J Tests"], cwd=workspace, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "llmj@example.com"], cwd=workspace, check=True, capture_output=True, text=True)

    tracked = workspace / "tracked.py"
    tracked.write_text("print('old')\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.py"], cwd=workspace, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=workspace, check=True, capture_output=True, text=True)

    tracked.write_text("print('new')\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.py"], cwd=workspace, check=True, capture_output=True, text=True)

    diff_path = stage5_runner._write_git_diff(workspace, tmp_path / "final.patch")

    patch = diff_path.read_text(encoding="utf-8")
    assert "tracked.py" in patch
    assert "+print('new')" in patch


def test_ensure_stage4_baseline_commit_resets_workspace_diff_baseline(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    subprocess.run(["git", "init"], cwd=workspace, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "LLM-J Tests"], cwd=workspace, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "llmj@example.com"], cwd=workspace, check=True, capture_output=True, text=True)

    tracked = workspace / "tracked.py"
    tracked.write_text("print('base')\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.py"], cwd=workspace, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=workspace, check=True, capture_output=True, text=True)

    tracked.write_text("print('degraded')\n", encoding="utf-8")
    baseline_commit = stage5_runner._ensure_stage4_baseline_commit(workspace)

    assert baseline_commit
    assert stage5_runner._workspace_status_entries(workspace) == []

    tracked.write_text("print('agent')\n", encoding="utf-8")
    diff_path = stage5_runner._write_git_diff(workspace, tmp_path / "agent.patch")
    patch = diff_path.read_text(encoding="utf-8")
    assert "+print('agent')" in patch
    assert "degraded" in patch
    assert "base" not in patch


def test_build_dependency_only_install_commands_filters_self_requirement_lines(tmp_path: Path):
    requirements = tmp_path / "requirements.txt"
    requirements.write_text(
        "-e .[test]\npytest==8.4.2\n-r requirements-dev.txt\n",
        encoding="utf-8",
    )
    nested = tmp_path / "requirements-dev.txt"
    nested.write_text(".\ntrio==0.30.0\n", encoding="utf-8")

    commands = stage5_runner._build_dependency_only_install_commands(
        [
            ["python", "-m", "pip", "install", "-r", str(requirements)],
            ["python", "-m", "pip", "install", "-e", f"{tmp_path}[test]"],
        ]
    )

    assert len(commands) == 1
    filtered_requirements = Path(commands[0][-1])
    assert filtered_requirements.name == ".llmj-requirements-oracle.txt"
    assert filtered_requirements.read_text(encoding="utf-8") == "pytest==8.4.2\n-r requirements-dev.txt\n"


def test_run_pytest_targets_sets_pythonpath_for_workspace_and_src(tmp_path: Path, monkeypatch):
    workspace = tmp_path / "workspace"
    (workspace / "src").mkdir(parents=True)
    python_executable = tmp_path / "python"
    python_executable.write_text("", encoding="utf-8")

    captured_env: dict[str, str] = {}

    def fake_run(command, *, capture_output, text, timeout, cwd, env):
        captured_env.update(env)
        return subprocess.CompletedProcess(
            command,
            0,
            stdout="tests/test_api.py::test_fix PASSED\n",
            stderr="",
        )

    monkeypatch.setattr(stage5_runner, "_python_module_available", lambda *args, **kwargs: False)
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setenv("PYTHONPATH", "/existing/path")

    result = stage5_runner._run_pytest_targets(
        workspace,
        ["tests/test_api.py::test_fix"],
        python_executable=python_executable,
        timeout_seconds=30,
    )

    assert result["passed"] == ["tests/test_api.py::test_fix"]
    assert captured_env["PYTHONPATH"] == os.pathsep.join(
        [str(workspace), str(workspace / "src"), "/existing/path"]
    )


def test_run_pytest_targets_parses_xdist_result_lines(tmp_path: Path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    python_executable = tmp_path / "python"
    python_executable.write_text("", encoding="utf-8")

    def fake_run(command, *, capture_output, text, timeout, cwd, env):
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=(
                "[gw0] [ 83%] PASSED tests/protocols/test_http.py::test_fix[h11]\n"
                "[gw1] [ 84%] FAILED tests/protocols/test_http.py::test_fix[httptools]\n"
            ),
            stderr="",
        )

    monkeypatch.setattr(stage5_runner, "_python_module_available", lambda *args, **kwargs: False)
    monkeypatch.setattr(subprocess, "run", fake_run)

    result = stage5_runner._run_pytest_targets(
        workspace,
        ["tests/protocols/test_http.py"],
        python_executable=python_executable,
        timeout_seconds=30,
    )

    assert result["passed"] == ["tests/protocols/test_http.py::test_fix[h11]"]
    assert result["failed"] == ["tests/protocols/test_http.py::test_fix[httptools]"]


def test_run_pytest_targets_preserves_partial_results_on_timeout(tmp_path: Path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    python_executable = tmp_path / "python"
    python_executable.write_text("", encoding="utf-8")

    def fake_run(command, *, capture_output, text, timeout, cwd, env):
        raise subprocess.TimeoutExpired(
            command,
            timeout,
            output=(
                "tests/test_api.py::test_pass PASSED\n"
                "tests/test_api.py::test_fail FAILED\n"
            ),
            stderr="",
        )

    monkeypatch.setattr(stage5_runner, "_python_module_available", lambda *args, **kwargs: False)
    monkeypatch.setattr(subprocess, "run", fake_run)

    result = stage5_runner._run_pytest_targets(
        workspace,
        ["tests/test_api.py"],
        python_executable=python_executable,
        timeout_seconds=30,
    )

    assert result["execution_error"] is False
    assert result["passed"] == ["tests/test_api.py::test_pass"]
    assert result["failed"] == ["tests/test_api.py::test_fail"]
    assert "tests/test_api.py::test_fail FAILED" in result["output"]


def test_install_workspace_uses_repo_profile_for_oracle_install(tmp_path: Path, monkeypatch):
    python_executable = tmp_path / "python"
    python_executable.write_text("", encoding="utf-8")
    profile = repo_profile_from_dict({
        "repo": "encode/starlette",
        "environment": {
            "post_install": [
                'python -m pip install pytest pytest-cov "python-multipart<0.0.14"',
            ],
        },
        "test": {"plugin_policy": {"mode": "explicit_only", "explicit_plugins": ["anyio.pytest_plugin"]}},
    })

    captured: dict[str, object] = {}

    class DummyInstallResult:
        success = True
        output = "ok"

    def fake_install_project(workspace_path, *, python_executable, repo_profile, install_timeout_seconds):
        captured["workspace_path"] = workspace_path
        captured["python_executable"] = python_executable
        captured["repo_profile"] = repo_profile
        captured["install_timeout_seconds"] = install_timeout_seconds
        return DummyInstallResult()

    monkeypatch.setattr(stage5_runner, "_install_project", fake_install_project)

    success, output = stage5_runner._install_workspace(
        tmp_path / "workspace",
        python_executable=python_executable,
        repo_profile=profile,
    )

    assert success is True
    assert output == "ok"
    assert captured["repo_profile"] is profile
    assert captured["install_timeout_seconds"] == 180


def test_run_pytest_targets_uses_repo_profile_env_and_plugins(tmp_path: Path, monkeypatch):
    workspace = tmp_path / "workspace"
    (workspace / "src").mkdir(parents=True)
    python_executable = tmp_path / "python"
    python_executable.write_text("", encoding="utf-8")
    profile = repo_profile_from_dict({
        "repo": "encode/starlette",
        "environment": {"env_vars": {"STARLETTE_PROFILE": "1"}},
        "test": {
            "plugin_policy": {"mode": "explicit_only", "explicit_plugins": ["anyio.pytest_plugin"]},
            "env_vars": {"PYTEST_ADDOPTS": "-q"},
        },
    })

    captured: dict[str, object] = {}

    def fake_run(command, *, capture_output, text, timeout, cwd, env):
        captured["command"] = command
        captured["env"] = env
        return subprocess.CompletedProcess(
            command,
            0,
            stdout="tests/test_api.py::test_fix PASSED\n",
            stderr="",
        )

    monkeypatch.setattr(stage5_runner, "_python_module_available", lambda *args, **kwargs: False)
    monkeypatch.setattr(subprocess, "run", fake_run)

    result = stage5_runner._run_pytest_targets(
        workspace,
        ["tests/test_api.py::test_fix"],
        python_executable=python_executable,
        timeout_seconds=30,
        repo_profile=profile,
    )

    assert result["passed"] == ["tests/test_api.py::test_fix"]
    assert captured["env"]["STARLETTE_PROFILE"] == "1"
    assert captured["env"]["PYTEST_ADDOPTS"] == "-q"
    assert captured["env"]["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
    assert captured["command"][:3] == [str(python_executable), "-m", "pytest"]
    assert "anyio.pytest_plugin" in captured["command"]
