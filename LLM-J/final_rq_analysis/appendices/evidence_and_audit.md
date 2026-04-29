# Evidence And Audit Appendix

This appendix explains what was checked and how much confidence to put in the exported scoring fields.

## Manual Audit Scope

This audit is not a full reread of all 150 runs. It is a stratified pass over high-risk and high-interpretation rows.

- All 9 clean failures.
- 9 naming failures split by regression-only, hidden-bug-fix-only, and combined failure shapes.
- 5 remove-tests examples across successes and failures.
- Strong interpretation examples from `copier`, `pydantic-settings`, `pip-tools`, and `httpx`, plus additional successful-run sanity checks from `click` and `structlog`.
- Excluded invalid artifacts: `pydantic-settings_pr_788 naming` and invalid `uvicorn` auth attempts.

The exact manifest is in `../tables/audit_and_manifests/audited_run_table/audited_run_table.csv`.

## What Was Checked

For each audited run, the manual pass inspected or summarized:

- `result.json`
- `metrics.json`
- `logs/final_repo_diff.patch`
- `logs/post_run_test_output.txt`
- the opening event sequence in `logs/agent_stdout.log`

## Audit Manifest

| audit_reason | repo | candidate_id | condition | status | failure_mode | result_path |
| --- | --- | --- | --- | --- | --- | --- |
| all_clean_failures | cattrs | cattrs_pr_142 | clean | FAIL | regression_only_failure | comparison_slices/rq1_initial_matrix_missing/runs/cattrs/cattrs_pr_142/codex_cli/clean/rep_1/result.json |
| all_clean_failures | click | click_pr_2816 | clean | FAIL | hidden_bug_fix_only_failure | runs/click/click_pr_2816/codex_cli/clean/rep_1/result.json |
| all_clean_failures | click | click_pr_3004 | clean | FAIL | regression_only_failure | runs/click/click_pr_3004/codex_cli/clean/rep_1/result.json |
| all_clean_failures | copier | copier_pr_2587 | clean | FAIL | hidden_bug_fix_only_failure | runs/copier/copier_pr_2587/codex_cli/clean/rep_1/result.json |
| all_clean_failures | pip-tools | pip-tools_pr_1893 | clean | FAIL | hidden_bug_fix_only_failure | runs/pip-tools/pip-tools_pr_1893/codex_cli/clean/rep_1/result.json |
| all_clean_failures | pip-tools | pip-tools_pr_2087 | clean | FAIL | hidden_bug_fix_only_failure | runs/pip-tools/pip-tools_pr_2087/codex_cli/clean/rep_1/result.json |
| all_clean_failures | pydantic-settings | pydantic-settings_pr_730 | clean | FAIL | hidden_bug_fix_only_failure | runs/pydantic-settings/pydantic-settings_pr_730/codex_cli/clean/rep_1/result.json |
| all_clean_failures | pydantic-settings | pydantic-settings_pr_773 | clean | FAIL | hidden_bug_fix_only_failure | runs/pydantic-settings/pydantic-settings_pr_773/codex_cli/clean/rep_1/result.json |
| all_clean_failures | starlette | starlette_pr_2422 | clean | FAIL | hidden_bug_fix_only_failure | comparison_slices/starlette_pr_2422_codex_clean/runs/starlette/starlette_pr_2422/codex_cli/clean/rep_1/result.json |
| naming_regression_only | httpx | httpx_pr_2423 | naming | FAIL | regression_only_failure | runs/httpx/httpx_pr_2423/codex_cli/naming/rep_1/result.json |
| naming_regression_only | marshmallow | marshmallow_pr_2772 | naming | FAIL | regression_only_failure | runs/marshmallow/marshmallow_pr_2772/codex_cli/naming/rep_1/result.json |
| naming_regression_only | starlette | starlette_pr_2400 | naming | FAIL | regression_only_failure | comparison_slices/rq1_initial_matrix_missing/runs/starlette/starlette_pr_2400/codex_cli/naming/rep_1/result.json |
| naming_hidden_bug_fix_only | uvicorn | uvicorn_pr_2183 | naming | FAIL | hidden_bug_fix_only_failure | runs/uvicorn/uvicorn_pr_2183/codex_cli/naming/rep_1/result.json |
| naming_hidden_bug_fix_only | pip-tools | pip-tools_pr_1893 | naming | FAIL | hidden_bug_fix_only_failure | runs/pip-tools/pip-tools_pr_1893/codex_cli/naming/rep_1/result.json |
| naming_hidden_bug_fix_only | pydantic-settings | pydantic-settings_pr_730 | naming | FAIL | hidden_bug_fix_only_failure | runs/pydantic-settings/pydantic-settings_pr_730/codex_cli/naming/rep_1/result.json |
| naming_hidden_bug_fix_and_regression | copier | copier_pr_2432 | naming | FAIL | hidden_bug_fix_and_regression_failure | runs/copier/copier_pr_2432/codex_cli/naming/rep_1/result.json |
| naming_hidden_bug_fix_and_regression | copier | copier_pr_2605 | naming | FAIL | hidden_bug_fix_and_regression_failure | runs/copier/copier_pr_2605/codex_cli/naming/rep_1/result.json |
| naming_hidden_bug_fix_and_regression | pydantic-settings | pydantic-settings_pr_780 | naming | FAIL | hidden_bug_fix_and_regression_failure | runs/pydantic-settings/pydantic-settings_pr_780/codex_cli/naming/rep_1/result.json |
| remove_tests_success | cattrs | cattrs_pr_108 | remove_tests | SUCCESS | success | comparison_slices/rq1_initial_matrix_missing/runs/cattrs/cattrs_pr_108/codex_cli/remove_tests/rep_1/result.json |
| remove_tests_success | pydantic-settings | pydantic-settings_pr_780 | remove_tests | SUCCESS | success | runs/pydantic-settings/pydantic-settings_pr_780/codex_cli/remove_tests/rep_1/result.json |
| remove_tests_failure | httpx | httpx_pr_2547 | remove_tests | FAIL | hidden_bug_fix_only_failure | comparison_slices/rq1_initial_matrix_missing/runs/httpx/httpx_pr_2547/codex_cli/remove_tests/rep_1/result.json |
| remove_tests_failure | click | click_pr_3004 | remove_tests | FAIL | regression_only_failure | runs/click/click_pr_3004/codex_cli/remove_tests/rep_1/result.json |
| remove_tests_failure | pip-tools | pip-tools_pr_2087 | remove_tests | FAIL | hidden_bug_fix_only_failure | runs/pip-tools/pip-tools_pr_2087/codex_cli/remove_tests/rep_1/result.json |
| strong_pass | click | click_pr_2846 | type_hints | SUCCESS | success | runs/click/click_pr_2846/codex_cli/type_hints/rep_1/result.json |
| strong_pass | click | click_pr_2846 | comments_docstrings | SUCCESS | success | runs/click/click_pr_2846/codex_cli/comments_docstrings/rep_1/result.json |
| strong_pass | structlog | structlog_pr_713 | comments_docstrings | SUCCESS | success | runs/structlog/structlog_pr_713/codex_cli/comments_docstrings/rep_1/result.json |

## Validation Summary

| check | expected | observed | passed | notes |
| --- | --- | --- | --- | --- |
| Matrix row count | 150 | 150 | True | One run per repo/candidate/condition. |
| Unique repositories | 10 | 10 | True |  |
| Unique historical PR tasks | 30 | 30 | True |  |
| Duplicate repo/candidate/condition rows | 0 | 0 | True |  |
| Harness ERROR rows | 0 | 0 | True | Known invalid artifacts are excluded from the final matrix. |
| Token coverage | 150/150 | 150/150 | True | Totals include cached input tokens where labeled. |
| Success/failure count | 101 SUCCESS / 49 FAIL | 101 SUCCESS / 49 FAIL | True |  |
| Process-log coverage | 150/150 | 150/150 | True | Required for enriched process metrics. |

## Audit Findings

The audited outcomes are fair scoring outcomes after excluding known invalid artifacts. The main interpretation guardrail is clean-baseline difficulty: do not count every degraded failure as degradation-caused.

The strongest examples are clean-pass / degraded-fail pairs, especially naming rows where hidden bug-fix tests passed but previously passing tests regressed.
