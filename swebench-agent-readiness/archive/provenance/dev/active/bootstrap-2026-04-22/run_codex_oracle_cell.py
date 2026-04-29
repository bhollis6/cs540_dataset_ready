"""Run one Codex clean-vs-degraded SWE-bench oracle cell.

This is an active-session helper, not a general CLI product. It stitches
together the small harness modules so each RQ1 matrix cell leaves reproducible
run specs, environment records, Codex logs, oracle results, and comparison
packets.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from swebench.harness.test_spec.test_spec import make_test_spec

from src.analysis.oracle_packet import (
    build_oracle_comparison_artifact,
    write_oracle_comparison_artifact,
)
from src.filters.eligibility import load_task_eligibility
from src.harness.codex_exec import CodexExecSpec, run_codex_exec, write_codex_exec_spec
from src.harness.codex_metrics import parse_codex_agent_metrics
from src.harness.materialize import materialize_pilot_run
from src.harness.oracle_replay import replay_oracle, write_oracle_replay_result
from src.harness.pilot_run import build_pilot_run_spec, write_pilot_run_spec
from src.harness.python_env import prepare_workspace_env
from src.substrate.swebench_verified import TaskSnapshot


ROOT = Path(__file__).resolve().parents[3]
ACTIVE = ROOT / "dev" / "active" / "bootstrap-2026-04-22"
VENV_NAME = ".pilot-venv-py39"

SOURCE_CLONES = {
    "pytest-dev/pytest": ROOT
    / "runs"
    / "pytest-dev__pytest-7432"
    / "codex-cli"
    / "clean"
    / "rep_1"
    / "workspace",
    "scikit-learn/scikit-learn": ROOT
    / "runs"
    / "scikit-learn__scikit-learn-26194"
    / "codex-cli"
    / "clean"
    / "rep_0"
    / "workspace",
    "sphinx-doc/sphinx": ROOT / "runs" / "_repo_cache" / "sphinx",
    "pylint-dev/pylint": ROOT / "runs" / "_repo_cache" / "pylint",
    "pydata/xarray": ROOT / "runs" / "_repo_cache" / "xarray",
    "sympy/sympy": ROOT / "runs" / "_repo_cache" / "sympy",
    "django/django": ROOT / "runs" / "_repo_cache" / "django",
    "psf/requests": ROOT / "runs" / "_repo_cache" / "requests",
    "matplotlib/matplotlib": ROOT / "runs" / "_repo_cache" / "matplotlib",
}


def _load_snapshot(path: Path) -> TaskSnapshot:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return TaskSnapshot(**payload)


def _changed_files(workspace_dir: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "-c", "core.fileMode=false", "diff", "--name-only"],
        cwd=workspace_dir,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _exec_spec(plan, *, label: str) -> CodexExecSpec:
    return CodexExecSpec(
        condition=plan.condition,
        workspace_dir=plan.workspace_dir,
        prompt_path=plan.prompt_path,
        stdout_log_path=plan.logs_dir / "agent_stdout.jsonl",
        stderr_log_path=plan.logs_dir / "agent_stderr.log",
        output_last_message_path=plan.logs_dir / "last_message.md",
        env_bin_dir=plan.workspace_dir / VENV_NAME / "bin",
    )


def run_cell(instance_id: str, condition: str, replication_index: int) -> None:
    slug = instance_id.replace("__", "_")
    profile_path = ROOT / "src" / "profiles" / f"{instance_id}_eligibility.json"
    snapshot_path = ACTIVE / f"{instance_id}_snapshot.json"
    eligibility = load_task_eligibility(profile_path)
    snapshot = _load_snapshot(snapshot_path)
    source_clone = SOURCE_CLONES.get(snapshot.repo)
    if source_clone is not None and not source_clone.exists():
        raise FileNotFoundError(f"No source clone configured for {snapshot.repo}: {source_clone}")

    run_spec = build_pilot_run_spec(
        output_root=ROOT,
        eligibility=eligibility,
        eligibility_path=profile_path,
        chosen_condition=condition,
        replication_index=replication_index,
    )
    prefix = f"{slug}_{condition}_rep_{replication_index}"
    write_pilot_run_spec(run_spec, ACTIVE / f"{prefix}_run_spec.json")
    materialize_pilot_run(
        snapshot=snapshot,
        run_spec=run_spec,
        output_path=ACTIVE / f"{prefix}_materialization.json",
        source_clone_dir=source_clone,
    )

    test_spec = make_test_spec(snapshot.to_swebench_instance(), namespace=None)
    for label, plan in (("clean", run_spec.clean), (condition, run_spec.degraded)):
        prepare_workspace_env(
            workspace_dir=plan.workspace_dir,
            test_spec=test_spec,
            output_path=ACTIVE / f"{prefix}_{label}_workspace_env_py39.json",
            venv_name=VENV_NAME,
        )
        spec = _exec_spec(plan, label=label)
        write_codex_exec_spec(spec, ACTIVE / f"{prefix}_{label}_codex_exec_spec.json")
        completed = run_codex_exec(spec)
        _write_json(
            ACTIVE / f"{prefix}_{label}_codex_exit.json",
            {
                "returncode": completed.returncode,
                "stdout_log_path": str(spec.stdout_log_path),
                "stderr_log_path": str(spec.stderr_log_path),
                "last_message_path": str(spec.output_last_message_path),
            },
        )

    relevant_files = set(snapshot.source_files + snapshot.test_files)
    clean_metrics = parse_codex_agent_metrics(
        stdout_log_path=run_spec.clean.logs_dir / "agent_stdout.jsonl",
        workspace_dir=run_spec.clean.workspace_dir,
        relevant_files=relevant_files,
    )
    degraded_metrics = parse_codex_agent_metrics(
        stdout_log_path=run_spec.degraded.logs_dir / "agent_stdout.jsonl",
        workspace_dir=run_spec.degraded.workspace_dir,
        relevant_files=relevant_files,
    )
    clean_result = replay_oracle(
        plan=run_spec.clean,
        snapshot=snapshot,
        test_spec=test_spec,
        changed_files=_changed_files(run_spec.clean.workspace_dir),
    )
    degraded_result = replay_oracle(
        plan=run_spec.degraded,
        snapshot=snapshot,
        test_spec=test_spec,
        changed_files=_changed_files(run_spec.degraded.workspace_dir),
    )
    write_oracle_replay_result(clean_result, run_spec.clean.result_path)
    write_oracle_replay_result(degraded_result, run_spec.degraded.result_path)

    artifact = build_oracle_comparison_artifact(
        run_spec=run_spec,
        clean=clean_result,
        degraded=degraded_result,
        clean_metrics=clean_metrics,
        degraded_metrics=degraded_metrics,
        notes=[
            "Proper RQ1 matrix execution cell.",
            f"Active helper: {Path(__file__).relative_to(ROOT)}",
        ],
    )
    write_oracle_comparison_artifact(
        artifact,
        ACTIVE / f"{prefix}_oracle_comparison.json",
        ACTIVE / f"{prefix}_oracle_comparison.md",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("instance_id")
    parser.add_argument("condition")
    parser.add_argument("replication_index", type=int)
    args = parser.parse_args()
    run_cell(args.instance_id, args.condition, args.replication_index)


if __name__ == "__main__":
    main()
