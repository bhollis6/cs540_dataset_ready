from __future__ import annotations

import shutil
from pathlib import Path

from common import FIGURE_DIR, TABLE_DIR, ensure_dirs


TABLE_GROUPS = {
    "overview": [
        "condition_summary",
        "repo_summary",
        "task_summary",
        "paired_clean_degraded_summary",
    ],
    "outcomes": [
        "transition_table",
        "pass_to_pass_damage_table",
        "baseline_hard_tasks",
        "type_hints_surface_summary",
    ],
    "process_and_patch_shape": [
        "exploration_process_summary",
        "remove_tests_patch_target_shifts",
    ],
    "tokens": [
        "token_summary",
        "high_token_delta_cases",
        "degraded_cheaper_cases",
    ],
    "rq2_process": [
        "rq2_phase_metric_summary",
        "rq2_phase_correlations",
    ],
    "audit_and_manifests": [
        "audit_sample_manifest",
        "audited_run_table",
        "manual_audit_scope",
        "manual_audit_scope_summary",
        "case_study_manifest",
        "transition_manifest",
        "pass_to_pass_damage_manifest",
    ],
    "sensitivity_and_validation": [
        "leave_one_repo_out_condition_effects",
        "validation_summary",
    ],
}

FIGURE_GROUPS = {
    "outcomes": [
        "task_success_rate_by_condition_ci",
        "clean_success_to_degraded_failure_counts",
        "target_test_failure_burden_by_condition",
        "regression_test_failure_burden_by_condition",
        "per_repo_clean_pass_to_degraded_fail_heatmap",
        "task_by_degradation_outcome_matrix",
        "baseline_hard_vs_degradation_induced_outcome_split",
    ],
    "process_and_patch_shape": [
        "changed_file_delta_by_condition",
        "files_opened_exploration_by_condition",
        "exploration_efficiency_delta_by_condition",
    ],
    "tokens": [
        "corrected_token_usage_by_condition",
        "paired_token_delta_by_condition",
    ],
    "rq2_process": [
        "rq2_phase_process_metric_summaries",
    ],
}


def move_matching(stem: str, group_dir: Path) -> None:
    target_dir = group_dir / stem
    target_dir.mkdir(parents=True, exist_ok=True)
    for source_dir in [TABLE_DIR, group_dir]:
        for path in source_dir.glob(f"{stem}.*"):
            if path.is_file():
                shutil.move(str(path), target_dir / path.name)


def move_figure_matching(group: str, stem: str) -> None:
    group_dir = FIGURE_DIR / group
    target_dir = group_dir / stem
    target_dir.mkdir(parents=True, exist_ok=True)
    for path in group_dir.glob(f"{stem}.*"):
        if path.is_file():
            shutil.move(str(path), target_dir / path.name)


def organize_tables() -> None:
    for group, stems in TABLE_GROUPS.items():
        target = TABLE_DIR / group
        for stem in stems:
            move_matching(stem, target)
    figure_data = TABLE_DIR / "figure_data"
    figure_data.mkdir(parents=True, exist_ok=True)
    for source_dir in [TABLE_DIR, figure_data]:
        for path in source_dir.glob("figure_data_*.csv"):
            stem = path.stem.removeprefix("figure_data_")
            target = figure_data / stem
            target.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), target / path.name)


def organize_figures() -> None:
    for group, stems in FIGURE_GROUPS.items():
        for stem in stems:
            move_figure_matching(group, stem)


def write_readmes() -> None:
    (TABLE_DIR / "README.md").write_text(
        """# Tables Guide

Tables are grouped by purpose. Each table has its own subfolder containing the available formats, usually CSV, Markdown, and LaTeX.

- `overview/`: start here for high-level condition, repo, task, and paired-comparison summaries.
- `outcomes/`: official scoring results, including clean-pass to degraded-fail cases, target-test failures, regression-test failures, clean-already-failed rows, and type-hints surface caveats.
- `process_and_patch_shape/`: file exploration, changed-file breadth, and remove-tests patch-target shifts.
- `tokens/`: corrected token usage. Token values are raw cumulative tokens unless the column name says otherwise.
- `rq2_process/`: recovered phase/process metrics from Codex logs.
- `audit_and_manifests/`: audit sample, audited run table, and case-study manifests with source artifact paths.
- `sensitivity_and_validation/`: leave-one-repo-out checks and deterministic export validation.
- `figure_data/`: CSV data used to draw the figures.

Plain-language terms:

- `clean`: Codex ran on the original task workspace.
- `degraded`: Codex ran on the same task after one codebase property was degraded.
- `target tests`: official SWE-bench tests that should fail before the fix and pass after the fix.
- `regression tests`: official SWE-bench tests that already passed and should keep passing.
- `paired comparison`: one clean run compared with one degraded run for the same task and condition.
""",
    )
    (FIGURE_DIR / "README.md").write_text(
        """# Figures Guide

Each figure has its own subfolder containing PNG, PDF, and SVG exports. Use PNG for quick slides, PDF/SVG for LaTeX or vector editing.

Subfolders:

- `outcomes/`: official task success and failure results.
- `process_and_patch_shape/`: how Codex searched files and how broad its patch became.
- `tokens/`: corrected cumulative token usage. Axes use thousands of tokens where labeled.
- `rq2_process/`: recovered process-count metrics for RQ2.

The figures are descriptive summaries of paired clean-vs-degraded runs. They do not replace the row-level tables when making exact claims.
""",
    )
    table_readmes = {
        "overview": """# Overview Tables

Start here for the main numeric summaries.

- `condition_summary/`: one row per degradation type. Best table for the headline RQ1 result.
- `repo_summary/`: one row per repo. Shows which repos were complete and where failures concentrated.
- `task_summary/`: one row per SWE-bench task.
- `paired_clean_degraded_summary/`: one row per paired comparison.
""",
        "outcomes": """# Outcome Tables

These tables explain official SWE-bench scoring.

- `transition_table/`: clean passed, degraded failed. Strongest outcome evidence.
- `pass_to_pass_damage_table/`: degraded failed more previously-passing regression tests.
- `baseline_hard_tasks/`: clean already failed; do not count these as degradation-caused target failures.
- `type_hints_surface_summary/`: annotation-node counts and type-hints caveats.
""",
        "process_and_patch_shape": """# Process and Patch-Shape Tables

These tables explain behavior changes beyond final task success.

- `exploration_process_summary/`: file-opening, exploration-efficiency, and changed-file deltas by condition.
- `remove_tests_patch_target_shifts/`: cases where removing visible tests changed what files Codex edited.
""",
        "tokens": """# Token Tables

These tables use corrected cumulative tokens: `input_tokens + output_tokens`.

- `token_summary/`: aggregate clean/degraded token usage by condition.
- `high_token_delta_cases/`: largest absolute token changes.
- `degraded_cheaper_cases/`: degraded runs that used fewer tokens than clean. Cheaper does not automatically mean better.
""",
        "rq2_process": """# RQ2 Process Tables

These tables use recovered Codex JSONL event counts.

- `rq2_phase_metric_summary/`: mean process-count deltas by degradation condition.
- `rq2_phase_correlations/`: correlations among recoverable process metrics.

These are action-count proxies, not timing or phase-token measurements.
""",
        "audit_and_manifests": """# Audit and Manifest Tables

These tables make the audit trail traceable.

- `manual_audit_scope_summary/`: audit scope in comparisons and individual runs.
- `manual_audit_scope/`: every audited comparison with artifact paths and audit notes.
- `audited_run_table/`: category-expanded audit artifact checks.
- `case_study_manifest/`, `transition_manifest/`, `pass_to_pass_damage_manifest/`: row-level case-study references.
""",
        "sensitivity_and_validation": """# Sensitivity and Validation Tables

- `leave_one_repo_out_condition_effects/`: checks whether one repo dominates condition effects.
- `validation_summary/`: deterministic export checks for row counts, duplicates, complete repos, token formula, and RQ2 joins.
""",
        "figure_data": """# Figure Data Tables

Each subfolder contains the CSV data used to draw one figure. Use these when recreating plots in another tool or checking a value shown in a figure.
""",
    }
    for group, text in table_readmes.items():
        target = TABLE_DIR / group
        target.mkdir(parents=True, exist_ok=True)
        (target / "README.md").write_text(text)
    readmes = {
        "outcomes": """# Outcome Figures

These figures answer: did the degraded workspace make Codex fail tasks or create regressions?

- `task_success_rate_by_condition_ci/`: success rate after degradation, with 95% Wilson confidence intervals. Black diamonds show clean-run success rates.
- `clean_success_to_degraded_failure_counts/`: number of paired comparisons where clean passed but degraded failed.
- `target_test_failure_burden_by_condition/`: net degraded-minus-clean change in failed official target tests. Positive values mean the degraded side missed more bug-fix target tests; negative values mean the degraded side missed fewer.
- `regression_test_failure_burden_by_condition/`: extra failed official regression tests. These are tests that should have stayed passing.
- `per_repo_clean_pass_to_degraded_fail_heatmap/`: where the clean-pass/degraded-fail cases occur by repo.
- `task_by_degradation_outcome_matrix/`: compact task-level view of outcome categories.
- `baseline_hard_vs_degradation_induced_outcome_split/`: separates new degraded failures from tasks that already failed clean.

Main read: naming dominates outcome damage.
""",
        "process_and_patch_shape": """# Process and Patch-Shape Figures

These figures answer: did the degradation change how Codex searched or patched, even when official success stayed the same?

- `changed_file_delta_by_condition/`: degraded minus clean changed-file count. Positive means Codex touched more files after degradation.
- `files_opened_exploration_by_condition/`: degraded minus clean files opened before the first edit.
- `exploration_efficiency_delta_by_condition/`: degraded minus clean ratio of useful early file opens. Negative means early exploration became less focused.

Main read: non-outcome effects are real but heterogeneous.
""",
        "tokens": """# Token Figures

These figures answer: did the degradation make Codex spend more model tokens?

- `corrected_token_usage_by_condition/`: median clean vs degraded token usage by condition. Unit is thousands of corrected cumulative tokens.
- `paired_token_delta_by_condition/`: degraded minus clean token usage by paired comparison. Unit is thousands of corrected cumulative tokens.

Corrected tokens mean `input_tokens + output_tokens`. Cached input tokens are not added because they are a subset of input tokens.
""",
        "rq2_process": """# RQ2 Process Figures

These figures summarize recovered Codex process counts split around the first edit.

- `rq2_phase_process_metric_summaries/`: mean degraded minus clean command/test-command deltas by condition.

These are event-count proxies. The logs do not provide reliable timestamps or phase-specific token splits.
""",
    }
    for group, text in readmes.items():
        target = FIGURE_DIR / group
        target.mkdir(parents=True, exist_ok=True)
        (target / "README.md").write_text(text)


def main() -> None:
    ensure_dirs()
    organize_tables()
    organize_figures()
    write_readmes()
    print("Organized figure/table outputs and wrote README guides.")


if __name__ == "__main__":
    main()
