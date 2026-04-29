# Methods And Data Manifest Appendix

This appendix keeps terminology, method details, and artifact locations out of the main report.

## Glossary

| Term | Plain-language meaning |
| --- | --- |
| Clean run | Codex ran on the original SWE-bench task workspace. |
| Degraded run | Codex ran on the same task after one codebase property was intentionally degraded. |
| Paired comparison | One clean run and one degraded run for the same task and degradation condition. |
| Condition | The degradation type: naming, type hints, comments/docstrings, or remove tests. |
| Replication index | The fixed run label for a condition. In this final matrix, it mostly identifies the condition family, not many repeated random trials. |
| Target tests | SWE-bench `FAIL_TO_PASS`: tests expected to fail before the bug fix and pass after a correct fix. These measure whether Codex fixed the bug. |
| Regression tests | SWE-bench `PASS_TO_PASS`: tests expected to pass before and after the fix. These measure whether Codex broke existing behavior. |
| Clean-pass to degraded-fail | The clean run passed the official task, but the degraded run failed. This is the strongest evidence that the degradation hurt Codex. |
| Clean-already-failed task | Codex failed on the clean workspace. If degraded also fails, do not count that as degradation-caused target failure. |
| Regression damage | The degraded run failed more previously-passing regression tests than the clean run. |
| Corrected tokens | `input_tokens + output_tokens`, summed over the whole Codex run. Cached input tokens are not added. |
| First edit | The first detected file modification in the Codex JSONL log. |
| Files opened before first edit | Files Codex inspected before it first modified the workspace. Used as an orientation/search proxy. |
| Exploration efficiency | Share of pre-edit opened files that later appeared in the final patch. Higher means early search was more focused. |
| Changed-file breadth | Number of files in the final patch. Higher can mean broader changes or a more scattered repair strategy. |
| Oracle replay | The scoring step that restores official SWE-bench tests, runs them, and records target/regression outcomes. |

## Pivot Rationale

This lane pivoted from custom PR mining to SWE-bench Verified because the parent custom-repo lane was expensive to reconstruct historically. SWE-bench Verified provided a controlled bug-fix substrate with official task metadata, known base commits, target/regression test splits, and a practical path to paired clean-vs-degraded comparisons.

This is not a second copy of the parent `LLM-J` custom-repo pipeline. Parent artifacts may be read for context, but this bundle is scoped to the SWE-bench agent-readiness study.

## Design

The experiment uses a paired design. For each selected SWE-bench Verified task, Codex runs once on a clean workspace and once on a degraded workspace for a single degradation family/replication index. Official oracle replay scores both sides.

Degradation families:

- `naming` / `rep_0`: scope-limited identifier obfuscation.
- `type_hints` / `rep_1`: conservative annotation stripping.
- `comments_docstrings` / `rep_2`: comment/docstring stripping.
- `remove_tests` / `rep_3`: deletion of changed visible test files; official oracle restores tests during replay.

The final export contains 128 scored paired comparisons over 32 SWE-bench Verified tasks, 11 represented repos, and 10 fully complete repos. A fully complete repo means at least three selected tasks, each with all four degradation families represented.

## Selection Criteria

Tasks were selected for:

- Verified SWE-bench membership.
- Runnable host-local historical environment.
- File-scoped or otherwise trustworthy oracle replay.
- Compact source/test surface.
- Meaningful degradation eligibility, recorded in `src/profiles/*_eligibility.json`.

Flask is represented but not fully complete because the current Verified pool exposed only one compact Flask task. `psf__requests-2317` was avoided because the official oracle path hung. Scikit-learn was expensive but ultimately completed through a stricter task set. Astropy required narrow historical build compatibility handling before its selected compact tasks could be run. Matplotlib and Astropy type-hints comparisons are low-signal because selected surfaces had zero annotation nodes.

## Harness And Scoring

Codex is the first-class harness. Each run is materialized under:

```text
runs/<instance_id>/codex-cli/<condition>/rep_<n>/
```

The agent prompt contract directs Codex to work inside the materialized workspace, prefer the workspace-local Python environment, make the bug fix, and validate with relevant tests. It is not asked to know the hidden oracle split.

Oracle replay:

- snapshots official test files,
- resets them to the base commit,
- applies the official SWE-bench `test_patch`,
- runs the official task command,
- restores the pre-oracle workspace contents,
- records target-test outcomes and regression-test outcomes.

RQ1 exports are constructed from comparison JSON packets plus Codex agent metrics. RQ2 exports are recovered from existing Codex JSONL logs without rerunning Codex.

## Token Metric Correction

Correct total tokens are:

```text
input_tokens + output_tokens
```

`cached_input_tokens` is retained as a diagnostic field but is not additive. The validation script checks both clean and degraded corrected totals against this formula.

## Source Exports

- `results/rq1_comparisons_2026-04-26.csv`
- `results/rq1_comparisons_2026-04-26.json`
- `results/rq2_phase_metrics_2026-04-26.csv`
- `results/rq2_phase_metrics_2026-04-26.json`

Copied into:

- `../data/rq1_comparisons_2026-04-26.csv`
- `../data/rq1_comparisons_2026-04-26.json`
- `../data/rq2_phase_metrics_2026-04-26.csv`
- `../data/rq2_phase_metrics_2026-04-26.json`

## Raw Artifact Locations

Do not copy these into the final folder:

- comparison JSON: `archive/provenance/dev/active/bootstrap-2026-04-22/*_oracle_comparison.json`
- run directories: `runs/<instance_id>/codex-cli/<condition>/rep_<n>/`
- Codex logs: `runs/<instance_id>/codex-cli/<condition>/rep_<n>/logs/agent_stdout.jsonl`
- oracle logs: `runs/<instance_id>/codex-cli/<condition>/rep_<n>/logs/oracle_test_output.txt`
- eligibility profiles: `src/profiles/*_eligibility.json`

## Generated Data

- `../data/rq1_enriched_analysis_matrix.csv`
- `../data/rq2_phase_delta_matrix.csv`
- `../data/selected_task_repo_summary.csv`
- `../data/transition_manifest.csv`
- `../data/pass_to_pass_damage_manifest.csv`
- `../data/audit_sample_manifest.csv`
- `../data/case_study_manifest.csv`
- `../data/manual_audit_scope.csv`
- `../data/manual_audit_scope_summary.csv`
- `../data/validation_summary.csv`

## Key Generated Tables

- `../tables/overview/condition_summary/condition_summary.*`
- `../tables/overview/repo_summary/repo_summary.*`
- `../tables/overview/task_summary/task_summary.*`
- `../tables/overview/paired_clean_degraded_summary/paired_clean_degraded_summary.*`
- `../tables/outcomes/transition_table/transition_table.*`
- `../tables/outcomes/pass_to_pass_damage_table/pass_to_pass_damage_table.*`
- `../tables/tokens/token_summary/token_summary.*`
- `../tables/process_and_patch_shape/exploration_process_summary/exploration_process_summary.*`
- `../tables/rq2_process/rq2_phase_metric_summary/rq2_phase_metric_summary.*`
- `../tables/rq2_process/rq2_phase_correlations/rq2_phase_correlations.*`
- `../tables/sensitivity_and_validation/leave_one_repo_out_condition_effects/leave_one_repo_out_condition_effects.*`
- `../tables/outcomes/baseline_hard_tasks/baseline_hard_tasks.*`
- `../tables/outcomes/type_hints_surface_summary/type_hints_surface_summary.*`
- `../tables/audit_and_manifests/audited_run_table/audited_run_table.*`
- `../tables/audit_and_manifests/manual_audit_scope/manual_audit_scope.*`
- `../tables/audit_and_manifests/manual_audit_scope_summary/manual_audit_scope_summary.*`

## Generated Figures

Each figure stem below is exported as `.png`, `.pdf`, and `.svg`:

- `../figures/outcomes/task_success_rate_by_condition_ci`
- `../figures/outcomes/clean_success_to_degraded_failure_counts`
- `../figures/outcomes/target_test_failure_burden_by_condition`
- `../figures/outcomes/regression_test_failure_burden_by_condition`
- `../figures/outcomes/per_repo_clean_pass_to_degraded_fail_heatmap`
- `../figures/outcomes/task_by_degradation_outcome_matrix`
- `../figures/outcomes/baseline_hard_vs_degradation_induced_outcome_split`
- `../figures/process_and_patch_shape/changed_file_delta_by_condition`
- `../figures/process_and_patch_shape/files_opened_exploration_by_condition`
- `../figures/process_and_patch_shape/exploration_efficiency_delta_by_condition`
- `../figures/tokens/corrected_token_usage_by_condition`
- `../figures/tokens/paired_token_delta_by_condition`
- `../figures/rq2_process/rq2_phase_process_metric_summaries`

Figure data tables live under `../tables/figure_data/`.
