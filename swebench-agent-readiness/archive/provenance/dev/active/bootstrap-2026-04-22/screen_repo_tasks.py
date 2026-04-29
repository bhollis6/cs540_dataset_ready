from __future__ import annotations

import argparse
import ast
import io
import json
import subprocess
import tokenize
from pathlib import Path
from typing import Any

from swebench.harness.test_spec.test_spec import make_test_spec

from src.harness.materialize import materialize_clean_workspace
from src.harness.oracle_replay import replay_oracle, write_oracle_replay_result
from src.harness.pilot_run import ConditionWorkspacePlan
from src.harness.python_env import prepare_workspace_env
from src.substrate.swebench_verified import TaskSnapshot, fetch_task_snapshot, write_task_snapshot


ROOT = Path(__file__).resolve().parents[3]
ACTIVE = ROOT / "dev" / "active" / "bootstrap-2026-04-22"
VENV_NAME = ".pilot-venv-py39"


def _run(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True)


def _ensure_repo_cache(repo: str) -> Path:
    cache_dir = ROOT / "runs" / "_repo_cache" / repo.split("/", 1)[1]
    if cache_dir.exists():
        return cache_dir
    cache_dir.parent.mkdir(parents=True, exist_ok=True)
    _run(["git", "clone", f"https://github.com/{repo}.git", str(cache_dir)])
    return cache_dir


def _changed_files(workspace_dir: Path) -> list[str]:
    completed = _run(["git", "-c", "core.fileMode=false", "diff", "--name-only"], cwd=workspace_dir)
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def _apply_patch(workspace_dir: Path, patch_text: str) -> None:
    subprocess.run(
        ["git", "apply", "--whitespace=nowarn"],
        cwd=workspace_dir,
        input=patch_text,
        text=True,
        check=True,
    )


def _count_comments(text: str) -> int:
    count = 0
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type == tokenize.COMMENT:
            count += 1
    return count


def _signals(workspace_dir: Path, snapshot: TaskSnapshot) -> dict[str, int]:
    totals = {
        "annotations": 0,
        "docstrings": 0,
        "comments": 0,
        "name_candidates": 0,
        "classes": 0,
        "functions": 0,
        "variables": 0,
        "total": 0,
    }
    for relative_path in [*snapshot.source_files, *snapshot.test_files]:
        path = workspace_dir / relative_path
        if path.suffix != ".py" or not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        totals["comments"] += _count_comments(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.AnnAssign):
                totals["annotations"] += 1
            elif isinstance(node, ast.arg) and node.annotation is not None:
                totals["annotations"] += 1
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.returns is not None:
                totals["annotations"] += 1
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                if ast.get_docstring(node, clean=False):
                    totals["docstrings"] += 1
            if isinstance(node, ast.ClassDef) and not node.name.startswith("Test"):
                totals["classes"] += 1
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("test"):
                totals["functions"] += 1
            elif isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Param)):
                totals["variables"] += 1
        totals["name_candidates"] = totals["classes"] + totals["functions"] + totals["variables"]
        totals["total"] = totals["name_candidates"]
    return totals


def _gold_plan(snapshot: TaskSnapshot) -> ConditionWorkspacePlan:
    run_root = ROOT / "runs" / snapshot.instance_id / "gold_preflight" / "rep_0"
    return ConditionWorkspacePlan(
        condition="gold_preflight",
        replication_index=0,
        run_root=run_root,
        workspace_dir=run_root / "workspace",
        oracle_workspace_dir=run_root / "oracle_workspace",
        prompt_path=run_root / "prompt.md",
        metadata_path=run_root / "metadata.json",
        logs_dir=run_root / "logs",
        result_path=ACTIVE / f"{snapshot.instance_id}_gold_preflight_result.json",
        metrics_path=run_root / "metrics.json",
        degradation_targets={},
    )


def _eligibility(snapshot: TaskSnapshot, signals: dict[str, int], result: dict[str, Any], screen_path: Path) -> dict[str, Any]:
    evidence = [result["test_command"]]
    target_files = [*snapshot.source_files, *snapshot.test_files]
    return {
        "schema_version": "0.1.0",
        "dataset_name": snapshot.dataset_name,
        "dataset_split": snapshot.dataset_split,
        "instance_id": snapshot.instance_id,
        "repo": snapshot.repo,
        "base_commit": snapshot.base_commit,
        "changed_source_files": snapshot.source_files,
        "changed_test_files": snapshot.test_files,
        "changed_test_support_files": [],
        "regression_surface_strength": "high",
        "test_signal": {
            "level": "high",
            "rationale": f"Gold preflight passed the official target split: {len(snapshot.fail_to_pass)} FAIL_TO_PASS and {len(snapshot.pass_to_pass)} PASS_TO_PASS.",
            "evidence": evidence,
        },
        "conditions": {
            "type_hints": {
                "condition": "type_hints",
                "status": "GO",
                "signal": {
                    "level": "high" if signals["annotations"] > 0 else "low",
                    "rationale": f"Target surface has {signals['annotations']} annotation nodes.",
                    "evidence": target_files,
                },
                "fairness_notes": ["Strip only target Python files."],
                "blockers": [],
            },
            "naming": {
                "condition": "naming",
                "status": "GO",
                "signal": {
                    "level": "high" if signals["name_candidates"] > 0 else "low",
                    "rationale": f"Target surface has {signals['name_candidates']} local rename candidates before safety filtering.",
                    "evidence": target_files,
                },
                "fairness_notes": ["Use scope-limited Rope renames and preserve public/test discovery names."],
                "blockers": [],
            },
            "comments_docstrings": {
                "condition": "comments_docstrings",
                "status": "GO",
                "signal": {
                    "level": "high" if signals["docstrings"] or signals["comments"] else "low",
                    "rationale": f"Target surface has {signals['docstrings']} docstrings and {signals['comments']} comments.",
                    "evidence": target_files,
                },
                "fairness_notes": ["Strip only comments/docstrings in source-like target files."],
                "blockers": [],
            },
            "remove_tests": {
                "condition": "remove_tests",
                "status": "GO",
                "signal": {
                    "level": "high",
                    "rationale": f"Gold preflight passed {len(snapshot.fail_to_pass)} FAIL_TO_PASS and {len(snapshot.pass_to_pass)} PASS_TO_PASS targets.",
                    "evidence": snapshot.test_files,
                },
                "fairness_notes": ["Delete changed test files only; official oracle restores tests during replay."],
                "blockers": [],
            },
        },
        "overall_status": "GO",
        "eligible_conditions": ["type_hints", "naming", "comments_docstrings", "remove_tests"],
        "chosen_pilot_condition": None,
        "decision_summary": f"Selected as a {snapshot.repo} task for the next Phase 1 repo after signal screening and successful host-local gold preflight.",
        "evidence_sources": [
            {"type": "signal_screen", "path": str(screen_path)},
            {"type": "gold_preflight", "path": str(ACTIVE / f"{snapshot.instance_id}_gold_preflight_result.json")},
            {"type": "snapshot", "path": str(ACTIVE / f"{snapshot.instance_id}_snapshot.json")},
        ],
        "open_questions": [],
        "notes": [],
    }


def screen(instance_id: str, screen_path: Path, write_profile: bool) -> dict[str, Any]:
    snapshot = fetch_task_snapshot(instance_id)
    write_task_snapshot(snapshot, ACTIVE / f"{instance_id}_snapshot.json")
    source_clone = _ensure_repo_cache(snapshot.repo)
    plan = _gold_plan(snapshot)
    if plan.run_root.exists():
        subprocess.run(["rm", "-rf", str(plan.run_root)], check=True)
    materialize_clean_workspace(
        snapshot=snapshot,
        target_dir=plan.workspace_dir,
        source_clone_dir=source_clone,
    )
    signals = _signals(plan.workspace_dir, snapshot)
    test_spec = make_test_spec(snapshot.to_swebench_instance(), namespace=None)
    prepare_workspace_env(
        workspace_dir=plan.workspace_dir,
        test_spec=test_spec,
        output_path=ACTIVE / f"{instance_id}_gold_preflight_env_py39.json",
        venv_name=VENV_NAME,
    )
    _apply_patch(plan.workspace_dir, snapshot.patch)
    plan.logs_dir.mkdir(parents=True, exist_ok=True)
    result = replay_oracle(
        plan=plan,
        snapshot=snapshot,
        test_spec=test_spec,
        changed_files=_changed_files(plan.workspace_dir),
    )
    write_oracle_replay_result(result, plan.result_path)
    payload = {
        "instance_id": snapshot.instance_id,
        "repo": snapshot.repo,
        "base_commit": snapshot.base_commit,
        "version": snapshot.version,
        "source_files": snapshot.source_files,
        "test_files": snapshot.test_files,
        "fail_to_pass_count": len(snapshot.fail_to_pass),
        "pass_to_pass_count": len(snapshot.pass_to_pass),
        "signals": signals,
        "gold_preflight": {
            "task_success": result.task_success,
            "fail_to_pass_failed_count": len(result.fail_to_pass_failed),
            "pass_to_pass_failed_count": len(result.pass_to_pass_failed),
            "duration_seconds": result.duration_seconds,
            "test_command": result.test_command,
        },
    }
    if write_profile and result.task_success:
        profile = _eligibility(snapshot, signals, payload["gold_preflight"], screen_path)
        profile_path = ROOT / "src" / "profiles" / f"{snapshot.instance_id}_eligibility.json"
        profile_path.write_text(json.dumps(profile, indent=2) + "\n")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_slug")
    parser.add_argument("instance_ids", nargs="+")
    parser.add_argument("--write-profiles", action="store_true")
    args = parser.parse_args()
    repo_slug = args.repo_slug.replace("/", "_")
    screen_path = ACTIVE / f"{repo_slug}_signal_screen_2026-04-27.json"
    existing = []
    if screen_path.exists():
        existing = json.loads(screen_path.read_text())
    by_id = {item["instance_id"]: item for item in existing}
    for instance_id in args.instance_ids:
        by_id[instance_id] = screen(instance_id, screen_path, args.write_profiles)
        screen_path.write_text(json.dumps(list(by_id.values()), indent=2) + "\n")
        print(json.dumps(by_id[instance_id], indent=2))


if __name__ == "__main__":
    main()
