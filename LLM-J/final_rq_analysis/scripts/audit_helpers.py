#!/usr/bin/env python3
"""Small helpers for manually auditing final RQ runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "final_rq_analysis/data/enriched_matrix_with_process_metrics.csv"


def classify(row: pd.Series) -> str:
    if row["status"] == "SUCCESS":
        return "success"
    hidden_bug_fix_failed = int(row["fail_to_pass_failed"])
    regression_failed = int(row["pass_to_pass_failed"])
    if hidden_bug_fix_failed and regression_failed:
        return "hidden_bug_fix_and_regression_failure"
    if hidden_bug_fix_failed:
        return "hidden_bug_fix_only_failure"
    if regression_failed:
        return "regression_only_failure"
    return "uncategorized_scoring_failure"


def load_matrix() -> pd.DataFrame:
    df = pd.read_csv(MATRIX)
    df["failure_category"] = df.apply(classify, axis=1)
    return df


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def tail(path: Path, lines: int = 20) -> str:
    if not path.exists():
        return "<missing>"
    content = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(content[-lines:])


def first_agent_events(path: Path, limit: int = 12) -> list[str]:
    if not path.exists():
        return ["<missing>"]
    events: list[str] = []
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            item = event.get("item") or {}
            if not isinstance(item, dict):
                continue
            item_type = item.get("type")
            if event.get("type") == "item.completed" and item_type == "agent_message":
                text = str(item.get("text") or "").replace("\n", " ")
                events.append(f"agent_message: {text[:220]}")
            elif event.get("type") == "item.completed" and item_type == "command_execution":
                command = item.get("command")
                command_text = " ".join(command) if isinstance(command, list) else str(command)
                status = item.get("status")
                exit_code = item.get("exit_code")
                events.append(f"command[{status}/{exit_code}]: {command_text.replace(chr(10), ' ')[:220]}")
            elif event.get("type") == "item.completed" and item_type == "file_change":
                changes = item.get("changes") or []
                paths = ", ".join(str(change.get("path", "")).split("/workspace/")[-1] for change in changes)
                events.append(f"file_change: {paths}")
            if len(events) >= limit:
                break
    return events


def summarize_run(repo: str, candidate_id: str, condition: str) -> str:
    df = load_matrix()
    match = df[(df.repo == repo) & (df.candidate_id == candidate_id) & (df.condition == condition)]
    if match.empty:
        raise SystemExit(f"No run found for {repo} {candidate_id} {condition}")
    row = match.iloc[0]
    result_path = ROOT / str(row["result_path"])
    metrics_path = ROOT / str(row["metrics_path"])
    run_root = result_path.parent
    stdout_path = run_root / "logs/agent_stdout.log"
    patch_path = run_root / "logs/final_repo_diff.patch"
    oracle_path = run_root / "logs/post_run_test_output.txt"
    result = read_json(result_path)
    metrics = read_json(metrics_path)
    lines = [
        f"# {repo} / {candidate_id} / {condition}",
        "",
        f"status: {row['status']} ({row['failure_category']})",
        f"hidden bug-fix tests: {row['fail_to_pass_passed']}/{row['fail_to_pass_total']}",
        f"previously passing tests: {row['pass_to_pass_passed']}/{row['pass_to_pass_total']}",
        f"duration_seconds: {row['total_duration_seconds']}",
        f"tokens_including_cache: {row['total_tokens_including_cache']}",
        f"result_path: {row['result_path']}",
        f"metrics_path: {row['metrics_path']}",
        f"patch_path: {patch_path.relative_to(ROOT)}",
        f"oracle_output_path: {oracle_path.relative_to(ROOT)}",
        f"agent_stdout_path: {stdout_path.relative_to(ROOT)}",
        "",
        "changed_files:",
    ]
    for changed in metrics.get("changed_files") or []:
        lines.append(f"- {changed}")
    lines.extend(["", "agent first events:"])
    lines.extend(f"- {event}" for event in first_agent_events(stdout_path))
    lines.extend(["", "oracle output tail:", "```text", tail(oracle_path, 18), "```"])
    oracle = result.get("oracle") or {}
    if oracle:
        lines.extend(["", "oracle summary:"])
        lines.append(json.dumps(oracle, indent=2)[:2000])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo")
    parser.add_argument("candidate_id")
    parser.add_argument("condition")
    args = parser.parse_args()
    print(summarize_run(args.repo, args.candidate_id, args.condition))


if __name__ == "__main__":
    main()
