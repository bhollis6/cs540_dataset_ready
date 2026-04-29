# Methods And Data Manifest Appendix

This appendix keeps terminology, method details, and artifact locations out of the main report.

## Glossary

| Term | Plain-language meaning |
| --- | --- |
| Run | One Codex attempt on one historical PR under one condition. |
| Condition | The codebase version shown to Codex: clean, naming-degraded, type-hints removed, comments/docstrings removed, or visible tests removed. |
| Historical PR | A real pull request from the repo history. We check out the code before the PR and ask Codex to recreate the fix. |
| Hidden bug-fix tests | Tests added by the original PR that should pass after a correct fix. Benchmark term: FAIL_TO_PASS. |
| Previously passing tests | Tests that should keep passing. Benchmark term: PASS_TO_PASS. |
| Same-task comparison | Compare clean and degraded outcomes for the same historical PR. |
| Clean-pass / degraded-fail | Clean passed but degraded failed. Strongest degradation-associated outcome evidence. |
| Clean baseline failure | Clean failed too. Do not treat degraded failure as degradation-caused without paired support. |
| Regression | Previously passing tests failed after the agent patch. |
| Process metrics | Recovered Codex event-log counts such as commands and validation commands. |

## Pipeline Summary

The custom-repo lane uses historical GitHub PRs as controlled agent tasks. Candidate scraping collects merged PR metadata, diffs, source files, and test files. Stage 1 uses an LLM judge to shortlist plausible tasks. Stage 2 verifies candidates mechanically with hidden bug-fix tests: base plus test patch should fail, and base plus test patch plus gold source patch should pass.

Stage 4 materializes one isolated workspace per task/condition and applies exactly one degradation. Stage 5 runs Codex CLI under a single-submission contract. Final scoring replay applies only non-test agent changes in a fresh workspace, restores hidden tests, and runs the repo-profile-shaped pytest command. Stage 6 parses preserved logs and metrics. Stage 7 builds the consolidated matrix used here.

## Source Of Truth

- Consolidated matrix CSV: `final_rq_analysis/data/consolidated_matrix.csv`
- Consolidated matrix JSON: `final_rq_analysis/data/consolidated_matrix.json`
- Enriched process-metrics matrix: `data/enriched_matrix_with_process_metrics.csv`

`comparison_slices/` contains raw/provenance material locally, but it is intentionally excluded from the GitHub read path because it is large.

## Candidate And Admission Artifacts

- Candidate JSON files: `candidates/*_pr_*.json`
- Stage 1 selected manifests: `results/*_selected_prs.json`
- Stage 2 verified manifests: `deep_results/*_verified_manifest.json`
- Experiment packets: `packets/*_experiment_packet.json`
- Run plans: `run_plans/*_run_plan.json`
- Repo profiles: `repo_profiles/*.json`

## Raw Artifact Locations

Raw run directories are local/provenance artifacts and are not copied into `final_rq_analysis/`.

Valid runs follow:

```text
runs/{repo}/{candidate_id}/codex_cli/{condition}/rep_1/
comparison_slices/*/runs/{repo}/{candidate_id}/codex_cli/{condition}/rep_1/
```

Each run root should contain `result.json`, `metrics.json`, `logs/agent_stdout.log`, `logs/agent_stderr.log`, `logs/final_repo_diff.patch`, and `logs/post_run_test_output.txt`.

## Factory-Style Readiness Context

Sources accessed during analysis:

- [Factory Readiness Report Command](https://docs.factory.ai/cli/features/readiness-report): Documents `/readiness-report`, repository evaluation, five maturity levels, criteria scoring, persisted reports, and remediation plans.
- [Factory Agent Readiness Overview](https://docs.factory.ai/web/agent-readiness/overview): Documents five readiness levels, 80% gated progression, repository vs application scopes, and technical pillars such as validation, testing, documentation, development environment, observability, security, task discovery, and product/experimentation.
- [Factory Introducing Agent Readiness](https://factory.ai/news/agent-readiness): Product announcement describing readiness reports, technical pillars, binary criteria/file/config checks, and claimed variance reduction through grounding evaluations on prior reports.

This study does not show Factory-style readiness is wrong. It shows broad checklist-style readiness needs empirical calibration against actual repair outcomes.

## Generated Tables

- `tables/audit_and_manifests/audited_run_table/audited_run_table.csv`
- `tables/failure_modes/failure_mode_summary/failure_mode_summary.csv`
- `tables/metadata/per_pr_metadata_summary/per_pr_metadata_summary.csv`
- `tables/outcomes/clean_baseline_failures/clean_baseline_failures.csv`
- `tables/outcomes/clean_pass_degraded_failures/clean_pass_degraded_failures.csv`
- `tables/outcomes/paired_clean_vs_degraded_detail/paired_clean_vs_degraded_detail.csv`
- `tables/outcomes/paired_clean_vs_degraded_summary/paired_clean_vs_degraded_summary.csv`
- `tables/overview/condition_summary/condition_summary.csv`
- `tables/overview/pr_summary/pr_summary.csv`
- `tables/overview/repo_summary/repo_summary.csv`
- `tables/process/rq2_process_correlations/rq2_process_correlations.csv`
- `tables/process/rq2_process_metric_summary/rq2_process_metric_summary.csv`
- `tables/sensitivity_and_validation/leave_one_repo_out_condition_effects/leave_one_repo_out_condition_effects.csv`
- `tables/sensitivity_and_validation/validation_summary/validation_summary.csv`
- `tables/tokens_runtime/token_runtime_summary/token_runtime_summary.csv`

## Generated Figures

- `figures/failure_modes/failure_mode_stacked_bars/failure_mode_stacked_bars.png`
- `figures/failure_modes/hidden_bug_fix_test_miss_burden/hidden_bug_fix_test_miss_burden.png`
- `figures/failure_modes/regression_burden_previously_passing_tests/regression_burden_previously_passing_tests.png`
- `figures/outcomes/paired_degraded_vs_clean_outcome_shifts/paired_degraded_vs_clean_outcome_shifts.png`
- `figures/outcomes/repo_difficulty_distribution/repo_difficulty_distribution.png`
- `figures/outcomes/success_failure_counts_by_condition/success_failure_counts_by_condition.png`
- `figures/outcomes/success_rate_by_condition/success_rate_by_condition.png`
- `figures/process/process_metrics_by_condition/process_metrics_by_condition.png`
- `figures/repo_task_detail/per_repo_success_heatmap/per_repo_success_heatmap.png`
- `figures/repo_task_detail/pr_condition_outcome_matrix/pr_condition_outcome_matrix.png`
- `figures/tokens_runtime/runtime_by_condition/runtime_by_condition.png`
- `figures/tokens_runtime/token_usage_by_condition/token_usage_by_condition.png`
