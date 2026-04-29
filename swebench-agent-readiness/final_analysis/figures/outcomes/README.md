# Outcome Figures

These figures answer: did the degraded workspace make Codex fail tasks or create regressions?

- `task_success_rate_by_condition_ci/`: success rate after degradation, with 95% Wilson confidence intervals. Black diamonds show clean-run success rates.
- `clean_success_to_degraded_failure_counts/`: number of paired comparisons where clean passed but degraded failed.
- `target_test_failure_burden_by_condition/`: net degraded-minus-clean change in failed official target tests. Positive values mean the degraded side missed more bug-fix target tests; negative values mean the degraded side missed fewer.
- `regression_test_failure_burden_by_condition/`: extra failed official regression tests. These are tests that should have stayed passing.
- `per_repo_clean_pass_to_degraded_fail_heatmap/`: where the clean-pass/degraded-fail cases occur by repo.
- `task_by_degradation_outcome_matrix/`: compact task-level view of outcome categories.
- `baseline_hard_vs_degradation_induced_outcome_split/`: separates new degraded failures from tasks that already failed clean.

Main read: naming dominates outcome damage.
