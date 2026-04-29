# Claim Ledger

This is the wording guardrail for the final analysis. Use it when writing slides, report prose, or discussion notes.

The table separates:

- **Strong evidence**: safe headline claims supported by official paired outcomes or deterministic validation.
- **Suggestive evidence**: useful patterns, but weaker than the RQ1 naming result.
- **Low-confidence or caveated**: valid observations that need careful wording.
- **Not supported**: claims to avoid.

Confidence labels are qualitative, not statistical significance tests.

## Strong Evidence

| ID | Claim | RQ | Evidence type | Supporting artifacts | Counterexamples | Confidence | Writeup | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C1 | Naming degradation is the strongest measured outcome-damage condition. | RQ1 | Paired official oracle outcomes | `tables/overview/condition_summary/condition_summary.*`, `tables/outcomes/transition_table/transition_table.*`, `figures/outcomes/clean_success_to_degraded_failure_counts/clean_success_to_degraded_failure_counts.*` | Some naming comparisons are outcome-stable; several clean-already-failed rows exist. | strong | `REPORT.md`, `appendices/detailed_results.md` | All 11 clean-pass to degraded-fail cases are naming. |
| C2 | Naming outcome damage is not explained by one repo. | RQ1 | Per-repo and leave-one-repo-out sensitivity | `tables/overview/repo_summary/repo_summary.*`, `tables/sensitivity_and_validation/leave_one_repo_out_condition_effects/leave_one_repo_out_condition_effects.*`, `figures/outcomes/per_repo_clean_pass_to_degraded_fail_heatmap/per_repo_clean_pass_to_degraded_fail_heatmap.*` | Sphinx, Django, Pytest, PyLint selected comparisons did not show naming clean-pass/degraded-fail cases. | strong | `REPORT.md`, `appendices/detailed_results.md` | Leave-one-repo-out retains at least 8 naming clean-pass/degraded-fail cases. |
| C3 | Regression-test damage is dominated by naming. | RQ1 | Official oracle regression-test deltas | `tables/outcomes/pass_to_pass_damage_table/pass_to_pass_damage_table.*`, `figures/outcomes/regression_test_failure_burden_by_condition/regression_test_failure_burden_by_condition.*` | One comments/docstrings Astropy clean-already-failed row has regression-test damage. | strong | `REPORT.md`, `appendices/detailed_results.md` | Naming accounts for 10 of 11 damage rows and 94 additional regression-test failures. |
| C4 | Clean baseline failures must be separated from degradation-induced failures. | RQ1 | Paired clean/degraded outcome flags | `tables/outcomes/baseline_hard_tasks/baseline_hard_tasks.*`, `figures/outcomes/baseline_hard_vs_degradation_induced_outcome_split/baseline_hard_vs_degradation_induced_outcome_split.*` | None. | strong | `REPORT.md`, `appendices/detailed_results.md`, `threats_to_validity.md` | There are 27 clean-already-failed rows. |
| C5 | Corrected token totals use `input_tokens + output_tokens`, excluding cached input. | RQ1/RQ2 | Deterministic validation | `tables/sensitivity_and_validation/validation_summary/validation_summary.*`, `scripts/validate_exports.py` | None in current export. | strong | `appendices/methods_data_manifest.md` | Validation checks both clean and degraded sides. |

## Suggestive Evidence

| ID | Claim | RQ | Evidence type | Supporting artifacts | Counterexamples | Confidence | Writeup | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C6 | Comments/docstrings are more process/cost-visible than outcome-damaging in this matrix. | RQ1/RQ2 | Outcome parity plus token/process deltas | `tables/overview/condition_summary/condition_summary.*`, `tables/rq2_process/rq2_phase_metric_summary/rq2_phase_metric_summary.*`, `tables/tokens/high_token_delta_cases/high_token_delta_cases.*` | `astropy__astropy-14365` has regression-test damage while clean already failed. | suggestive | `REPORT.md`, `appendices/detailed_results.md` | No clean-pass to degraded-fail cases. |
| C7 | Remove-tests mostly changes validation/patch shape rather than official target success. | RQ1/RQ2 | Outcome parity plus patch-target shifts | `tables/process_and_patch_shape/remove_tests_patch_target_shifts/remove_tests_patch_target_shifts.*`, `tables/process_and_patch_shape/exploration_process_summary/exploration_process_summary.*` | Some remove-tests comparisons are much cheaper, some more expensive; effects are heterogeneous. | suggestive | `REPORT.md`, `appendices/detailed_results.md` | Official oracle restores tests, so visible-test deletion is not equivalent to hidden-test deletion. |
| C8 | RQ2 supports multi-dimensional process behavior. | RQ2 | Phase/process deltas and weak bootstrap/execution correlation | `tables/rq2_process/rq2_phase_metric_summary/rq2_phase_metric_summary.*`, `tables/rq2_process/rq2_phase_correlations/rq2_phase_correlations.*`, `figures/rq2_process/rq2_phase_process_metric_summaries/rq2_phase_process_metric_summaries.*` | Metrics are action-count proxies; no timestamps or phase-token splits. | suggestive | `REPORT.md`, `appendices/detailed_results.md` | Claim process multi-dimensionality, not proven readiness dimensions. |
| C9 | Outcome parity does not imply process parity. | RQ2 | Official pass rows with cost/exploration/patch changes | `tables/tokens/token_summary/token_summary.*`, `tables/process_and_patch_shape/exploration_process_summary/exploration_process_summary.*`, `tables/tokens/high_token_delta_cases/high_token_delta_cases.*` | Some rows show little process difference. | suggestive | `REPORT.md`, `appendices/detailed_results.md` | Stronger as a descriptive process claim than as a causal theory. |

## Low-Confidence or Caveated

| ID | Claim | RQ | Evidence type | Supporting artifacts | Counterexamples | Confidence | Writeup | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C10 | Type-hints do not matter for Codex repair performance. | RQ1 | Current outcome table | `tables/outcomes/type_hints_surface_summary/type_hints_surface_summary.*` | 19/30 type-hints rows have zero or one annotation node; selected surfaces often cannot test the condition. | weak | `REPORT.md`, `appendices/detailed_results.md` | Safer claim: type-hints was low-signal in this matrix. |
| C11 | Degraded cheaper rows mean degradation helped. | RQ1/RQ2 | Token deltas | `tables/tokens/degraded_cheaper_cases/degraded_cheaper_cases.*` | Stochasticity and shorter failed/alternate paths can reduce tokens. | weak | `appendices/detailed_results.md` | Use as "weird cases," not as benefit evidence. |
| C12 | Static readiness checklists predict Codex task performance. | RQ3 | External comparison idea | `REPORT.md`, `appendices/detailed_results.md` | Static tools were not run on these repos. | unsupported | `REPORT.md`, `appendices/detailed_results.md` | Future work only. |

## Not Supported

| ID | Claim | RQ | Evidence type | Supporting artifacts | Counterexamples | Confidence | Writeup | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N1 | All degraded failures were caused by the degradation. | RQ1 | Paired clean-already-failed analysis | `tables/outcomes/baseline_hard_tasks/baseline_hard_tasks.*` | 27 rows failed clean. | unsupported | `threats_to_validity.md` | Must compare clean and degraded side. |
| N2 | Factory-style readiness tools are wrong. | RQ3 | External claim comparison | `REPORT.md`, `appendices/detailed_results.md` | We did not run Factory on these repos. | unsupported | `REPORT.md`, `appendices/detailed_results.md` | Say challenged/narrowed/under-validated instead. |
| N3 | RQ2 proves a complete readiness dimensionality model. | RQ2 | Process metrics only | `tables/rq2_process/rq2_phase_metric_summary/rq2_phase_metric_summary.*` | Missing timestamps and phase-token splits. | unsupported | `REPORT.md`, `appendices/detailed_results.md` | RQ2 remains supporting. |
