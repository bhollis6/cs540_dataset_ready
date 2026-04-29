# Custom-Repo Agent Readiness Report

This is the main report for the custom-repo LLM-J readiness study.

## Short Answer

We tested whether changing specific codebase properties changed Codex's ability to solve real historical Python PR tasks.

The clearest result is naming. When meaningful names were replaced with generic names, Codex was much more likely to fail tasks it could solve cleanly. Naming solved `14/30` runs, compared with clean at `21/30`, and it produced `542` failed previously passing tests.

The other conditions were weaker as final-outcome signals. Type hints and comments/docstrings had the same aggregate success count as clean, but their failures were shaped differently. Removing visible tests had the weakest final-outcome impact here.

The process evidence is useful but should stay modest: different degradations changed failure shape, validation behavior, token/runtime burden, and regression risk in different ways. That supports a multi-dimensional view, but it does not prove a complete readiness model.

The readiness-tool result is cautious: these data do not justify a broad all-purpose readiness score. A readiness checklist needs calibration against actual agent outcomes.

## Experiment Setup

Each run used one historical pull request from one of 10 Python repositories. We checked out the code before the PR and asked Codex to recreate the fix under one workspace condition:

| Condition | What Codex saw |
| --- | --- |
| `clean` | Original historical codebase. |
| `naming` | Meaningful names were replaced with generic names. |
| `type_hints` | Python type annotations were removed. |
| `comments_docstrings` | Comments and docstrings were removed. |
| `remove_tests` | Visible tests were removed while Codex worked. Hidden scoring tests were restored for evaluation. |

The remove-tests condition is easy to misread. It changed what Codex could see while working; it did not remove the final scoring tests.

## Dataset

- `150` total runs.
- `30` historical PR tasks.
- `10` repositories.
- 5 conditions per task.
- `101` successes and `49` failures.
- `0` harness errors in the final matrix.

## How Scoring Worked

After Codex finished, the harness replayed only the agent's non-test code changes into a fresh scoring workspace. It then restored the hidden tests from the original PR and ran both:

- **Hidden bug-fix tests**: tests added by the original PR that should pass after a correct fix.
- **Previously passing tests**: tests that should keep passing. Failures here are regressions.

A run succeeded only if it fixed the intended behavior and did not break previously passing tests.

## Terms You Need

- **Run**: one Codex attempt on one historical PR under one condition.
- **Same-task comparison**: compare the same PR under clean and degraded conditions.
- **Clean-pass / degraded-fail**: clean passed but degraded failed. This is the strongest evidence that the degradation hurt Codex.
- **Clean baseline failure**: clean failed too. If degraded also failed, treat the task as hard before attributing the failure to the degradation.
- **Regression**: previously passing tests failed after the agent patch.
- **Process metrics**: recoverable Codex log counts such as command count, validation command count, and edit/test/edit loops. They are not timing measurements.

## RQ1: What Hurt Final Repair Success?

Naming quality was the strongest final-outcome signal.

| condition | n | success | fail | success_rate | hidden_bug_fix_only_failures | regression_only_failures | hidden_bug_fix_and_regression_failures | previously_passing_test_failures_total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| clean | 30 | 21 | 9 | 0.7 | 7 | 2 | 0 | 3 |
| naming | 30 | 14 | 16 | 0.4667 | 7 | 5 | 4 | 542 |
| type_hints | 30 | 21 | 9 | 0.7 | 7 | 2 | 0 | 3 |
| comments_docstrings | 30 | 21 | 9 | 0.7 | 9 | 0 | 0 | 0 |
| remove_tests | 30 | 24 | 6 | 0.8 | 5 | 1 | 0 | 2 |

The paired same-task view is the safest way to interpret causality:

| condition | pairs | both_success | clean_success_degraded_fail | clean_fail_degraded_success | both_fail | clean_pass_degraded_fail_rate | net_success_shift_vs_clean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| naming | 30 | 13 | 8 | 1 | 8 | 0.2667 | -7 |
| type_hints | 30 | 19 | 2 | 2 | 7 | 0.0667 | 0 |
| comments_docstrings | 30 | 18 | 3 | 3 | 6 | 0.1 | 0 |
| remove_tests | 30 | 20 | 1 | 4 | 5 | 0.0333 | 3 |

Naming has the largest clean-pass / degraded-fail count: 8 of 30 same-task comparisons. Type hints had 2, comments/docstrings had 3, and remove-tests had 1.

Clean baseline failures matter. There were 9 clean failures:

| repo | candidate_id | failure_mode | hidden_bug_fix_tests_failed | previously_passing_tests_failed |
| --- | --- | --- | --- | --- |
| cattrs | cattrs_pr_142 | regression_only_failure | 0 | 1 |
| click | click_pr_2816 | hidden_bug_fix_only_failure | 1 | 0 |
| click | click_pr_3004 | regression_only_failure | 0 | 2 |
| copier | copier_pr_2587 | hidden_bug_fix_only_failure | 1 | 0 |
| pip-tools | pip-tools_pr_1893 | hidden_bug_fix_only_failure | 39 | 0 |
| pip-tools | pip-tools_pr_2087 | hidden_bug_fix_only_failure | 1 | 0 |
| pydantic-settings | pydantic-settings_pr_730 | hidden_bug_fix_only_failure | 3 | 0 |
| pydantic-settings | pydantic-settings_pr_773 | hidden_bug_fix_only_failure | 2 | 0 |
| starlette | starlette_pr_2422 | hidden_bug_fix_only_failure | 1 | 0 |

Do not count degraded failures on those same PRs as strong degradation-caused evidence unless the paired clean/degraded pattern supports that read.

## RQ2: Did Degradations Change How Codex Worked?

Yes, but this is supporting evidence rather than the headline result.

Naming combined lower solve rate, higher token/runtime burden, and regression risk. Type-hints and comments/docstrings mostly looked like hidden-bug-fix repair misses rather than broad regressions. Remove-tests had weak final-outcome impact, but it still changed validation and rework proxies.

Compact process-metric summary:

| condition | command_count_before_first_edit_mean | command_count_after_first_edit_mean | validation_test_command_count_mean | failed_validation_test_command_count_mean | edit_test_edit_loop_proxy_count_mean |
| --- | --- | --- | --- | --- | --- |
| clean | 14.033 | 16.7 | 5.633 | 2.9 | 2.867 |
| naming | 15.533 | 20.133 | 6.8 | 3.8 | 3.733 |
| type_hints | 14.067 | 17.033 | 5.867 | 2.933 | 2.867 |
| comments_docstrings | 13.8 | 16.533 | 5.9 | 2.7 | 3.133 |
| remove_tests | 13.9 | 18.433 | 5.633 | 2.733 | 2.7 |

The full process table and correlations are in `appendices/detailed_results.md`. The best simple takeaway is: final pass/fail parity does not mean process parity. A degraded run can still pass while being more expensive, more scattered, or more validation-heavy.

Important caveat: current Codex logs do not support reliable timing claims, time-to-first-edit claims, or token-before-first-edit claims.

## RQ3: Should We Build A Broad Readiness Tool?

Not from these results alone.

The evidence challenges broad checklist-style readiness claims unless the checklist is calibrated against actual agent outcomes. Naming was the clearest repeated final-outcome signal. Other dimensions were weaker or visible mainly through process and failure shape.

This does not mean Factory-style readiness or engineering hygiene is wrong. It means this study does not show that a broad checklist reliably predicts Codex repair success on these tasks.

The better takeaway is:

> A calibrated, evidence-backed readiness signal is safer than a broad unvalidated readiness score.

## Best Evidence To Use

- `tables/overview/condition_summary/condition_summary.csv`: best single numeric summary.
- `tables/outcomes/paired_clean_vs_degraded_summary/paired_clean_vs_degraded_summary.csv`: safest same-task comparison.
- `tables/outcomes/clean_pass_degraded_failures/clean_pass_degraded_failures.csv`: strongest degradation-associated examples.
- `tables/failure_modes/failure_mode_summary/failure_mode_summary.csv`: failure-shape split.
- `figures/outcomes/success_rate_by_condition/success_rate_by_condition.png`: headline success-rate figure.
- `figures/outcomes/paired_degraded_vs_clean_outcome_shifts/paired_degraded_vs_clean_outcome_shifts.png`: paired outcome shifts.
- `claim_ledger.md`: wording guardrails.
- `threats_to_validity.md`: limitations.

## Safer Wording

| Avoid saying | Safer wording |
| --- | --- |
| "Naming causes all failures." | "Naming is the strongest measured negative condition in this matrix." |
| "Type hints do not matter." | "Type-hints removal did not reduce aggregate success here; this does not prove type hints never matter." |
| "Tests do not matter." | "Removing visible tests had weak final-outcome impact here, while hidden tests were still restored for scoring." |
| "RQ2 proves readiness is multi-dimensional." | "RQ2 provides process and failure-shape evidence that degradations affect agents differently." |
| "Factory is wrong." | "Checklist-style readiness needs empirical calibration against agent outcomes." |

## Bottom Line

For these custom historical PR tasks, naming quality was the clearest harmful codebase property for Codex. Other tested dimensions changed failure shape and process behavior more than final solve rate. The result supports careful, outcome-calibrated readiness claims, not a broad readiness score yet.
