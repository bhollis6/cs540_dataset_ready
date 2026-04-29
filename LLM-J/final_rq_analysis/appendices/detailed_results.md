# Detailed Results Appendix

This appendix preserves the expanded RQ notes and row-level examples behind the main report.

## RQ1 Detailed Notes

RQ1 asks which codebase properties mattered most for Codex final performance.

Naming is the strongest measured outcome signal. It solved `14/30` runs, compared with clean at `21/30`, and has the largest regression burden.

| condition | n | success | fail | success_rate | wilson_ci_low | wilson_ci_high | risk_difference_vs_clean | risk_ratio_vs_clean | odds_ratio_vs_clean | hidden_bug_fix_only_failures | regression_only_failures | hidden_bug_fix_and_regression_failures | uncategorized_scoring_failures | hidden_bug_fix_test_failures_total | previously_passing_test_failures_total | mean_total_duration_seconds | median_total_duration_seconds | mean_total_tokens_including_cache | median_total_tokens_including_cache | mean_edits_applied | mean_files_opened_before_first_edit | mean_exploration_efficiency |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| clean | 30 | 21 | 9 | 0.7 | 0.5212 | 0.8334 | 0.0 | 1.0 | 1.0 | 7 | 2 | 0 | 0 | 48 | 3 | 296.94 | 256.99 | 975795.83 | 837174.0 | 3.3 | 5.23 | 0.6725 |
| naming | 30 | 14 | 16 | 0.4667 | 0.3023 | 0.6386 | -0.2333 | 0.6667 | 0.3883 | 7 | 5 | 4 | 0 | 60 | 542 | 332.18 | 305.46 | 1290318.3 | 1148217.0 | 3.07 | 4.83 | 0.655 |
| type_hints | 30 | 21 | 9 | 0.7 | 0.5212 | 0.8334 | 0.0 | 1.0 | 1.0 | 7 | 2 | 0 | 0 | 55 | 3 | 281.29 | 253.38 | 1019786.63 | 905692.5 | 3.13 | 4.93 | 0.6863 |
| comments_docstrings | 30 | 21 | 9 | 0.7 | 0.5212 | 0.8334 | 0.0 | 1.0 | 1.0 | 9 | 0 | 0 | 0 | 55 | 0 | 274.63 | 269.64 | 1017549.7 | 792728.5 | 2.77 | 4.93 | 0.6957 |
| remove_tests | 30 | 24 | 6 | 0.8 | 0.6269 | 0.905 | 0.1 | 1.1429 | 1.6655 | 5 | 1 | 0 | 0 | 51 | 2 | 277.87 | 235.76 | 909275.1 | 779354.0 | 2.67 | 5.1 | 0.5336 |

## Paired Same-Task Read

| condition | pairs | both_success | clean_success_degraded_fail | clean_fail_degraded_success | both_fail | clean_pass_degraded_fail_rate | net_success_shift_vs_clean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| naming | 30 | 13 | 8 | 1 | 8 | 0.2667 | -7 |
| type_hints | 30 | 19 | 2 | 2 | 7 | 0.0667 | 0 |
| comments_docstrings | 30 | 18 | 3 | 3 | 6 | 0.1 | 0 |
| remove_tests | 30 | 20 | 1 | 4 | 5 | 0.0333 | 3 |

The clean-pass / degraded-fail rows are the strongest degradation-associated examples:

| repo | candidate_id | condition | degraded_failure_mode | hidden_bug_fix_tests_failed | previously_passing_tests_failed | total_duration_seconds | total_tokens_including_cache |
| --- | --- | --- | --- | --- | --- | --- | --- |
| copier | copier_pr_2432 | naming | hidden_bug_fix_and_regression_failure | 1 | 51 | 190.61493015289307 | 824969 |
| copier | copier_pr_2605 | naming | hidden_bug_fix_and_regression_failure | 4 | 58 | 346.827342748642 | 1137689 |
| httpx | httpx_pr_2423 | naming | regression_only_failure | 0 | 26 | 312.16074681282043 | 813446 |
| marshmallow | marshmallow_pr_2772 | naming | regression_only_failure | 0 | 165 | 350.1322109699249 | 1437174 |
| pydantic-settings | pydantic-settings_pr_780 | naming | hidden_bug_fix_and_regression_failure | 1 | 184 | 464.9599528312683 | 1890931 |
| starlette | starlette_pr_2400 | naming | regression_only_failure | 0 | 8 | 299.3827180862427 | 1160862 |
| uvicorn | uvicorn_pr_2183 | naming | hidden_bug_fix_only_failure | 1 | 0 | 311.53631377220154 | 1159601 |
| uvicorn | uvicorn_pr_2561 | naming | hidden_bug_fix_only_failure | 1 | 0 | 200.3474245071411 | 530344 |
| httpx | httpx_pr_2547 | type_hints | hidden_bug_fix_only_failure | 3 | 0 | 310.12426948547363 | 797255 |
| uvicorn | uvicorn_pr_2829 | type_hints | hidden_bug_fix_only_failure | 4 | 0 | 236.90457153320312 | 888998 |
| cattrs | cattrs_pr_108 | comments_docstrings | hidden_bug_fix_only_failure | 1 | 0 | 283.4684262275696 | 684082 |
| httpx | httpx_pr_2547 | comments_docstrings | hidden_bug_fix_only_failure | 1 | 0 | 344.3958468437195 | 1096856 |
| structlog | structlog_pr_489 | comments_docstrings | hidden_bug_fix_only_failure | 2 | 0 | 565.5801804065704 | 1245190 |
| httpx | httpx_pr_2547 | remove_tests | hidden_bug_fix_only_failure | 3 | 0 | 503.37622809410095 | 1699182 |

## Repo And PR Heterogeneity

Repo difficulty is substantial. `pip-tools`, `pydantic-settings`, and `copier` contribute many hard runs, while `marshmallow` and `structlog` are mostly solved.

| repo | success | n | success_rate | clean_success_rate | naming_success_rate | type_hints_success_rate | comments_docstrings_success_rate | remove_tests_success_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pip-tools | 5 | 15 | 0.3333 | 0.3333 | 0.3333 | 0.3333 | 0.3333 | 0.3333 |
| pydantic-settings | 5 | 15 | 0.3333 | 0.3333 | 0.0 | 0.3333 | 0.3333 | 0.6667 |
| copier | 8 | 15 | 0.5333 | 0.6667 | 0.0 | 0.6667 | 0.6667 | 0.6667 |
| click | 9 | 15 | 0.6 | 0.3333 | 0.3333 | 0.6667 | 1.0 | 0.6667 |
| cattrs | 11 | 15 | 0.7333 | 0.6667 | 1.0 | 0.6667 | 0.3333 | 1.0 |
| httpx | 11 | 15 | 0.7333 | 1.0 | 0.6667 | 0.6667 | 0.6667 | 0.6667 |
| starlette | 12 | 15 | 0.8 | 0.6667 | 0.3333 | 1.0 | 1.0 | 1.0 |
| uvicorn | 12 | 15 | 0.8 | 1.0 | 0.3333 | 0.6667 | 1.0 | 1.0 |
| marshmallow | 14 | 15 | 0.9333 | 1.0 | 0.6667 | 1.0 | 1.0 | 1.0 |
| structlog | 14 | 15 | 0.9333 | 1.0 | 1.0 | 1.0 | 0.6667 | 1.0 |

## Failure Modes

| condition | failure_category | count |
| --- | --- | --- |
| clean | hidden_bug_fix_and_regression_failure | 0 |
| clean | hidden_bug_fix_only_failure | 7 |
| clean | regression_only_failure | 2 |
| clean | success | 21 |
| naming | hidden_bug_fix_and_regression_failure | 4 |
| naming | hidden_bug_fix_only_failure | 7 |
| naming | regression_only_failure | 5 |
| naming | success | 14 |
| type_hints | hidden_bug_fix_and_regression_failure | 0 |
| type_hints | hidden_bug_fix_only_failure | 7 |
| type_hints | regression_only_failure | 2 |
| type_hints | success | 21 |
| comments_docstrings | hidden_bug_fix_and_regression_failure | 0 |
| comments_docstrings | hidden_bug_fix_only_failure | 9 |
| comments_docstrings | regression_only_failure | 0 |
| comments_docstrings | success | 21 |
| remove_tests | hidden_bug_fix_and_regression_failure | 0 |
| remove_tests | hidden_bug_fix_only_failure | 5 |
| remove_tests | regression_only_failure | 1 |
| remove_tests | success | 24 |

Naming has the broadest failure shape: hidden-bug-fix-only failures, regression-only failures, and combined hidden-bug-fix + regression failures. Type hints and comments/docstrings mostly look like hidden-bug-fix repair misses. Remove-tests failures are fewer by final outcome.

## RQ2 Detailed Notes

RQ2 asks whether readiness appears multi-dimensional in process behavior. Treat this as supporting evidence, not the headline result.

| condition | n | command_count_before_first_edit_mean | command_count_before_first_edit_median | command_count_after_first_edit_mean | command_count_after_first_edit_median | agent_message_count_before_first_edit_mean | agent_message_count_before_first_edit_median | agent_message_count_after_first_edit_mean | agent_message_count_after_first_edit_median | edit_event_count_after_first_edit_mean | edit_event_count_after_first_edit_median | validation_test_command_count_mean | validation_test_command_count_median | validation_test_command_count_after_first_edit_mean | validation_test_command_count_after_first_edit_median | failed_validation_test_command_count_mean | failed_validation_test_command_count_median | failed_command_count_mean | failed_command_count_median | edit_test_edit_loop_proxy_count_mean | edit_test_edit_loop_proxy_count_median | failed_validation_followed_by_edit_count_mean | failed_validation_followed_by_edit_count_median |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| clean | 30 | 14.033 | 13.0 | 16.7 | 15.5 | 2.867 | 3.0 | 4.633 | 5.0 | 4.1 | 3.0 | 5.633 | 5.0 | 5.033 | 4.0 | 2.9 | 2.0 | 4.733 | 4.0 | 2.867 | 2.5 | 2.067 | 2.0 |
| naming | 30 | 15.533 | 14.5 | 20.133 | 18.5 | 3.067 | 3.0 | 4.833 | 5.0 | 4.767 | 4.5 | 6.8 | 6.5 | 5.833 | 6.0 | 3.8 | 3.5 | 5.167 | 5.0 | 3.733 | 4.0 | 2.967 | 3.0 |
| type_hints | 30 | 14.067 | 14.5 | 17.033 | 15.0 | 3.8 | 4.0 | 4.833 | 5.0 | 4.3 | 4.0 | 5.867 | 5.5 | 5.167 | 5.0 | 2.933 | 3.0 | 4.467 | 4.5 | 2.867 | 2.5 | 2.033 | 2.0 |
| comments_docstrings | 30 | 13.8 | 13.0 | 16.533 | 14.0 | 3.667 | 4.0 | 5.033 | 5.0 | 4.5 | 4.0 | 5.9 | 5.0 | 5.1 | 5.0 | 2.7 | 2.0 | 4.167 | 3.0 | 3.133 | 3.0 | 2.2 | 2.0 |
| remove_tests | 30 | 13.9 | 12.5 | 18.433 | 19.0 | 3.5 | 3.0 | 5.067 | 5.0 | 3.533 | 3.0 | 5.633 | 4.5 | 5.467 | 4.5 | 2.733 | 3.0 | 5.133 | 5.0 | 2.7 | 0.0 | 1.233 | 0.0 |

| metric | pearson_corr_with_success |
| --- | --- |
| files_opened_before_first_edit | -0.0421 |
| exploration_efficiency | 0.0474 |
| total_duration_seconds | -0.0625 |
| total_tokens_including_cache | -0.1315 |
| command_count_before_first_edit | -0.1899 |
| command_count_after_first_edit | -0.0642 |
| validation_test_command_count | 0.0109 |
| failed_validation_test_command_count | 0.0576 |
| failed_command_count | 0.0109 |
| edit_test_edit_loop_proxy_count | -0.0353 |

Unavailable from current logs: exact timestamps, reliable time to first edit, tokens before first edit, post-edit token usage, and phase-specific token split.

## RQ3 Detailed Notes

The current custom-repo results do not justify a broad general-purpose readiness scoring tool. Naming was the dominant repeated outcome signal. Other dimensions were weaker or visible mainly in process/failure shape.

Future work should run static readiness criteria on these repos, test correlation with actual agent outcomes, add feedback-loop/build/CI/environment-doc degradations, and validate any score against held-out agent performance.
