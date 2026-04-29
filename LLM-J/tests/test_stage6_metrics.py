"""Tests for Stage 6 metrics parsing from Stage 5 artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from src.workflow.stage6_metrics import parse_stage6_metrics


def test_parse_stage6_metrics_enriches_codex_run(tmp_path: Path):
    execution_dir = tmp_path / "runs"
    run_root = execution_dir / "runs/httpx/httpx_pr_1/codex_cli/clean/rep_1"
    workspace = run_root / "workspace"
    logs = run_root / "logs"
    workspace.mkdir(parents=True)
    logs.mkdir(parents=True)

    for relative in ["src/app.py", "tests/test_app.py", "docs/guide.md"]:
        path = workspace / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("content\n", encoding="utf-8")

    (logs / "agent_stdout.log").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {
                            "id": "item_1",
                            "type": "command_execution",
                            "command": "/usr/bin/bash -lc \"sed -n '1,80p' src/app.py\"",
                            "aggregated_output": "print('hello')",
                            "exit_code": 0,
                            "status": "completed",
                        },
                    }
                ),
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {
                            "id": "item_2",
                            "type": "command_execution",
                            "command": "/usr/bin/bash -lc \"sed -n '1,80p' docs/guide.md\"",
                            "aggregated_output": "guide",
                            "exit_code": 0,
                            "status": "completed",
                        },
                    }
                ),
                json.dumps(
                    {
                        "type": "item.started",
                        "item": {
                            "id": "item_3",
                            "type": "command_execution",
                            "command": "/usr/bin/bash -lc \"python - <<'PY'\nfrom pathlib import Path\nPath('src/app.py').write_text('changed')\nPY\"",
                            "aggregated_output": "",
                            "exit_code": None,
                            "status": "in_progress",
                        },
                    }
                ),
                json.dumps(
                    {
                        "type": "turn.completed",
                        "usage": {
                            "input_tokens": 1000,
                            "cached_input_tokens": 800,
                            "output_tokens": 50,
                        },
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (logs / "agent_stderr.log").write_text("", encoding="utf-8")
    (logs / "post_run_test_output.txt").write_text("", encoding="utf-8")
    (logs / "final_repo_diff.patch").write_text("", encoding="utf-8")
    (logs / "agent_prompt.md").write_text("", encoding="utf-8")

    result_payload = {
        "run_id": "httpx__httpx_pr_1__codex_cli__clean__rep1",
        "repo": "encode/httpx",
        "candidate_id": "httpx_pr_1",
        "condition": "clean",
        "replication": 1,
        "status": "FAIL",
        "completion_reason": "oracle_fail",
        "harness": {"id": "codex_cli", "runner": "codex-cli"},
        "workspace": str(workspace),
        "oracle": {
            "task_success": False,
            "command": "python -m pytest tests/test_app.py",
            "oracle_setup": {
                "evaluation": {
                    "untracked_source_files": [],
                }
            },
        },
    }
    metrics_payload = {
        "run_id": result_payload["run_id"],
        "changed_files": ["src/app.py"],
        "bootstrap": {
            "tokens_before_first_edit": None,
            "files_opened_before_first_edit": None,
            "dead_end_file_opens": None,
            "relevant_files_opened": None,
            "exploration_efficiency": None,
            "time_to_first_edit_seconds": None,
        },
        "execution": {
            "task_success": False,
            "total_tokens": None,
            "total_cost_usd": None,
            "edits_applied": 1,
            "test_commands_run": 1,
            "completion_reason": "oracle_fail",
        },
    }
    (run_root / "result.json").write_text(json.dumps(result_payload), encoding="utf-8")
    (run_root / "metrics.json").write_text(json.dumps(metrics_payload), encoding="utf-8")

    execution_summary = {
        "repo": "encode/httpx",
        "results": [
            {
                "run_id": result_payload["run_id"],
                "result_path": str(run_root / "result.json"),
                "metrics_path": str(run_root / "metrics.json"),
            }
        ],
    }
    (execution_dir / "httpx_stage5_execution.json").write_text(json.dumps(execution_summary), encoding="utf-8")

    summary_path = parse_stage6_metrics(repo="encode/httpx", execution_dir=execution_dir)
    summary = json.loads(summary_path.read_text())
    metrics = json.loads((run_root / "metrics.json").read_text())

    assert summary["coverage"]["files_opened_present"] == 1
    assert metrics["bootstrap"]["files_opened_before_first_edit"] == 2
    assert metrics["bootstrap"]["relevant_files_opened"] == 1
    assert metrics["bootstrap"]["dead_end_file_opens"] == 1
    assert metrics["bootstrap"]["opened_files_before_first_edit"] == ["src/app.py", "docs/guide.md"]
    assert metrics["total_tokens"] == 1050
    assert metrics["execution"]["total_tokens"] == 1050


def test_parse_stage6_metrics_enriches_claude_run(tmp_path: Path):
    execution_dir = tmp_path / "runs"
    run_root = execution_dir / "runs/httpx/httpx_pr_2/claude_code/clean/rep_1"
    workspace = run_root / "workspace"
    logs = run_root / "logs"
    workspace.mkdir(parents=True)
    logs.mkdir(parents=True)

    (workspace / "src").mkdir()
    (workspace / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")

    (logs / "claude_debug.log").write_text(
        "\n".join(
            [
                "2026-04-22T00:00:00.000Z [DEBUG] Stream started - received first chunk",
                "2026-04-22T00:00:01.000Z [DEBUG] Spawning shell without login (-l flag skipped)",
                "2026-04-22T00:00:05.000Z [DEBUG] \"Hook PreToolUse:Edit (PreToolUse) error:\\nmissing\\n\"",
                "2026-04-22T00:00:06.000Z [DEBUG] \"Read tool input error: Read failed due to the following issue:\\nThe parameter `offset` type is expected as `number` but provided as `string`\"",
                "2026-04-22T00:00:07.000Z [ERROR] MCP server \"claude.ai Gmail\" Error: auth",
                f"2026-04-22T00:00:05.100Z [DEBUG] Writing to temp file: {workspace}/src/app.py.tmp.1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    for name in ["agent_stdout.log", "agent_stderr.log", "post_run_test_output.txt", "final_repo_diff.patch", "agent_prompt.md"]:
        (logs / name).write_text("", encoding="utf-8")

    result_payload = {
        "run_id": "httpx__httpx_pr_2__claude_code__clean__rep1",
        "repo": "encode/httpx",
        "candidate_id": "httpx_pr_2",
        "condition": "clean",
        "replication": 1,
        "status": "ERROR",
        "completion_reason": "agent_error",
        "harness": {"id": "claude_code", "runner": "claude-code"},
        "workspace": str(workspace),
        "agent": {
            "parsed_response": {
                "total_cost_usd": 1.25,
                "usage": {
                    "input_tokens": 100,
                    "cache_creation_input_tokens": 50,
                    "cache_read_input_tokens": 25,
                    "output_tokens": 10,
                },
            }
        },
        "oracle": {
            "task_success": True,
            "command": "python -m pytest tests/test_app.py",
        },
    }
    metrics_payload = {
        "run_id": result_payload["run_id"],
        "changed_files": ["src/app.py"],
        "bootstrap": {
            "tokens_before_first_edit": None,
            "files_opened_before_first_edit": None,
            "dead_end_file_opens": None,
            "relevant_files_opened": None,
            "exploration_efficiency": None,
            "time_to_first_edit_seconds": None,
        },
        "execution": {
            "task_success": True,
            "total_tokens": None,
            "total_cost_usd": None,
            "edits_applied": 1,
            "test_commands_run": 1,
            "completion_reason": "agent_error",
        },
    }
    (run_root / "result.json").write_text(json.dumps(result_payload), encoding="utf-8")
    (run_root / "metrics.json").write_text(json.dumps(metrics_payload), encoding="utf-8")

    execution_summary = {
        "repo": "encode/httpx",
        "results": [
            {
                "run_id": result_payload["run_id"],
                "result_path": str(run_root / "result.json"),
                "metrics_path": str(run_root / "metrics.json"),
            }
        ],
    }
    (execution_dir / "httpx_stage5_execution.json").write_text(json.dumps(execution_summary), encoding="utf-8")

    parse_stage6_metrics(repo="encode/httpx", execution_dir=execution_dir)
    metrics = json.loads((run_root / "metrics.json").read_text())

    assert metrics["bootstrap"]["time_to_first_edit_seconds"] == 5.0
    assert metrics["bootstrap"]["first_edit_detected"] is True
    assert metrics["execution"]["edits_applied"] == 1
    assert metrics["total_tokens"] == 185
    assert metrics["total_cost_usd"] == 1.25
    assert metrics["stage6"]["parser"] == "claude_debug_v2"
    assert metrics["stage6"]["details"]["claude_debug"]["shell_spawn_count"] == 1
    assert metrics["stage6"]["details"]["claude_debug"]["shell_spawn_count_before_first_write"] == 1
    assert metrics["stage6"]["details"]["claude_debug"]["write_event_count"] == 1
    assert metrics["stage6"]["details"]["claude_debug"]["time_to_first_write_seconds"] == 5.1
    assert metrics["stage6"]["details"]["claude_debug"]["tool_error_count"] == 1
    assert metrics["stage6"]["details"]["claude_debug"]["read_tool_error_count"] == 1
    assert metrics["stage6"]["details"]["claude_debug"]["edit_validation_error_count"] == 0
    assert metrics["stage6"]["details"]["claude_debug"]["mcp_error_count"] == 1
