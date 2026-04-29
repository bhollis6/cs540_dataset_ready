# SWE-bench Agent Readiness Report

This is the main report for the SWE-bench agent-readiness study.

## Short Answer

We tested whether degrading specific codebase properties changed Codex's ability to fix SWE-bench Verified bugs.

The clearest result is naming. When we made names less meaningful, Codex was much more likely to fail tasks it could solve in the clean workspace. All 11 clean-pass to degraded-fail cases came from the naming condition.

The process results are useful but weaker. Other degradations often changed how Codex searched, validated, spent tokens, or shaped patches, even when the final pass/fail result stayed the same.

The readiness-tool result is cautious: these data support a narrow naming/semantic-navigation signal better than a broad all-purpose readiness score.

## Experiment Setup

Each comparison used one SWE-bench Verified bug-fix task. Codex ran twice:

1. **Clean run**: Codex worked in the original task workspace.
2. **Degraded run**: Codex worked on the same task after we changed one property of the workspace.

Both patches were scored with the same official SWE-bench oracle tests. The paired design is the point: the clean and degraded runs are matched on the same task.

We tested four degradations:

| Degradation | What changed |
| --- | --- |
| Naming | Local identifiers were made less meaningful. |
| Type hints | Python type annotations were removed. |
| Comments/docstrings | Explanatory comments and docstrings were removed. |
| Remove tests | Changed visible test files were removed before Codex worked. Official tests were restored for scoring. |

The remove-tests condition is easy to misread. It changed what Codex could see while working; it did not permanently remove official scoring tests.

## Dataset

- 128 paired clean-vs-degraded comparisons.
- 256 individual clean/degraded run rows in the RQ2 process export.
- 32 unique SWE-bench Verified tasks.
- 11 represented repos.
- 10 fully complete repos.

A fully complete repo means at least three selected tasks from that repo, with all four degradation types represented for each selected task.

## Terms You Need

- **Target tests**: official tests that check whether the bug was fixed.
- **Regression tests**: official tests that were already passing and should keep passing.
- **Clean-pass to degraded-fail**: Codex solved the task clean but failed after degradation. This is the strongest outcome evidence.
- **Clean-already-failed**: Codex failed even on the clean workspace. If degraded also failed, that is not strong evidence that the degradation caused the target failure.
- **Corrected tokens**: `input_tokens + output_tokens`. Cached input tokens are not added.
- **Exploration efficiency**: among files Codex opened before its first edit, the share that later appeared in the final patch.
- **Oracle replay**: the scoring step that restores official SWE-bench tests and records target/regression outcomes.

## RQ1: What Hurt Actual Repair Success?

RQ1 is the strongest result.

Naming quality was the clearest measured risk factor. In 30 naming comparisons, clean success rate was 80.0% and degraded success rate was 43.3%.

Naming produced:

- all 11 clean-pass to degraded-fail cases,
- 10 of 11 regression-damage rows,
- 94 additional failed regression tests,
- 9 net additional failed target tests,
- the largest average changed-file increase,
- the largest average token increase.

This was not explained by one repo. Naming clean-pass to degraded-fail cases appeared across xarray, Sympy, Requests, Matplotlib, scikit-learn, and Astropy. Leave-one-repo-out checks still preserve at least 8 naming clean-pass to degraded-fail cases under every omission.

The other conditions were weaker:

- **Comments/docstrings**: no clean-pass to degraded-fail cases. One Astropy row had regression damage, but the clean run already failed the target.
- **Remove tests**: no official target-success damage and no regression-damage rows. Its signal is mainly validation/process behavior: changed patch targets, lower exploration efficiency, and different command/test behavior.
- **Type hints**: no outcome damage in this matrix, but the condition is underpowered because 19 of 30 type-hints rows had zero or one annotation node.

The key interpretation rule: rows where clean already failed are useful for cost/process/regression analysis, but they are not degradation-caused target-failure evidence.

## RQ2: Did Degradations Change How Codex Worked?

Yes, but this evidence is weaker and noisier than RQ1.

Even when Codex still solved the task, degradations changed how it worked:

- how many files it opened before editing,
- how focused that early search was,
- how many files it changed,
- how many commands and test commands it ran,
- how many tokens it used.

Condition-level process read:

- **Naming**: outcome-damaging and process-cost visible. It increased first-edit event index, command counts, changed files, and tokens.
- **Comments/docstrings**: mostly cost/process visible. It changed command counts and token use without clean-pass to degraded-fail cases.
- **Remove tests**: validation and patch-target visible. It often changed which files Codex edited and reduced exploration efficiency.
- **Type hints**: mostly low-signal in this task set because many selected surfaces had little or no annotation surface.

The best simple takeaway is: final pass/fail parity does not mean process parity. A degraded run can still pass while being more expensive, more scattered, or more validation-heavy.

Important caveat: current logs do not support reliable timing claims, time-to-first-edit claims, or phase-specific token claims. RQ2 uses recovered action-count metrics, so frame it as suggestive process evidence.

## RQ3: Should We Build A Broad Readiness Tool?

Not from these results alone.

The evidence supports a narrower conclusion: naming and semantic navigation look important for Codex on these SWE-bench bug-fix tasks. Other dimensions are weaker, noisier, or visible mainly in process metrics.

A broad readiness score would need calibration against actual agent outcomes. Without that, it risks becoming a checklist that sounds useful but is not proven to predict repair success.

The better RQ3 takeaway is:

> A narrow naming/semantic-navigation predictor is better supported than a broad all-purpose readiness score.

This does not mean static readiness tools or engineering hygiene are useless. It means this experiment does not show that all checklist dimensions equally predict Codex bug-fix performance.

## Best Evidence To Use

For slides or a short writeup, use:

- `tables/overview/condition_summary/condition_summary.csv`: best single table for the result.
- `figures/outcomes/clean_success_to_degraded_failure_counts/clean_success_to_degraded_failure_counts.png`: clearest RQ1 headline figure.
- `figures/outcomes/regression_test_failure_burden_by_condition/regression_test_failure_burden_by_condition.png`: regression-damage burden.
- `figures/outcomes/task_success_rate_by_condition_ci/task_success_rate_by_condition_ci.png`: success-rate view by condition.
- `figures/tokens/paired_token_delta_by_condition/paired_token_delta_by_condition.png`: token-cost spread.
- `claim_ledger.md`: exact claim boundaries.
- `threats_to_validity.md`: limitations to keep attached to the result.

## Safer Wording

| Avoid saying | Safer wording |
| --- | --- |
| "Naming causes all failures." | "Naming is the strongest measured degradation-associated outcome signal in this paired matrix." |
| "Type hints do not matter." | "Type-hints removal was low-signal here because many selected task surfaces had zero or one annotation node." |
| "Remove-tests had no effect." | "Remove-tests did not create official target-success damage, but it changed validation behavior, patch targets, and exploration efficiency." |
| "RQ2 proves readiness is multi-dimensional." | "RQ2 provides suggestive process evidence that degradations affect search, validation, token use, and patch shape differently." |
| "We should build a readiness score from these results." | "A narrow naming/semantic-navigation predictor is better supported than a broad readiness score." |

## Bottom Line

For these SWE-bench bug-fix tasks, unclear naming repeatedly hurt Codex's actual repair success. Other tested dimensions usually changed cost, search, validation, or patch shape more than final success. The result supports a focused naming/semantic-navigation readiness signal, not a broad readiness scoring tool yet.
