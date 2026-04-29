# Threats to Validity / Limitations

Keep this section close to any report or slide deck that uses the SWE-bench pivot results. The strongest result is naming, but the experiment is still a bounded study.

## Experimental Scope

- **Single agent/harness family**: results are Codex-specific. They should not be generalized to all coding agents without replication.
- **Limited replications**: most paired comparisons have one run per task/condition. Single-run agent stochasticity remains.
- **SWE-bench Verified task type**: the tasks are curated bug-fix tasks. They may not represent long-horizon production maintenance, design work, deployment tasks, or feature development.
- **Selected task set**: tasks were chosen for compactness, oracle trustworthiness, host-local feasibility, and degradation eligibility. This is not a random sample of all software work.

## Scoring And Interpretation

- **Paired comparison is required**: a degraded failure only means strong outcome damage when the clean side passed and the degraded side failed.
- **Clean-already-failed rows**: 27 rows failed clean. Degraded failures in those rows are not degradation-caused target failures.
- **Regression-test damage**: extra regression-test failures are real damage, but they can appear even when target success is unchanged or when the clean side already failed.
- **Oracle assumptions**: target-test and regression-test scores are only as reliable as the official SWE-bench split and local oracle replay fidelity.
- **Remove-tests condition**: visible tests were removed while Codex worked, but official oracle replay restored tests for scoring. Interpret remove-tests as a visibility/validation degradation, not as changing the final scoring standard.

## Condition-Specific Limits

- **Naming has the strongest evidence**: the naming result is supported by outcome transitions, regression damage, per-repo spread, and leave-one-repo-out checks.
- **Type-hints is underpowered**: 19 of 30 type-hints rows had zero or one annotation node, so this matrix cannot support a broad "type hints do not matter" claim.
- **Comments/docstrings is mostly process/cost evidence**: it did not produce clean-pass to degraded-fail cases, but it did affect tokens/process and had one regression-damage row on a clean-already-failed task.
- **Remove-tests is mostly process/validation evidence**: it did not produce official target-success damage, but it changed patch targets, validation behavior, and exploration efficiency.

## Process-Metric Limits

- **No reliable timing claims**: current logs do not provide reliable timestamps or time-to-first-edit.
- **No phase-token claims**: current logs do not expose tokens before versus after the first edit.
- **Coarse RQ2 metrics**: RQ2 uses recoverable action counts, such as commands and test commands, not a full behavioral trace.
- **Token interpretation**: lower token use in degraded runs does not automatically mean the degradation helped. It can also mean a shorter failed path or a different strategy.

## Environment And Reproducibility Limits

- **Historical dependency reconstruction**: local helpers approximate old package environments and may introduce host-specific behavior.
- **Bootstrap fragility**: Sphinx, PyLint, Astropy, Matplotlib, and other historical stacks required compatibility handling.
- **Known exclusions**: `psf__requests-2317` was avoided because the official oracle path hung; Flask could not fill a full repo because only one compact Verified task was available.
- **Raw artifacts remain external**: the final folder contains lightweight exports and summaries, not copied worktrees or full run directories.

## RQ3 Limits

- **Static readiness tools were not run**: Factory-style readiness criteria are external context only.
- **No broad readiness-score calibration yet**: these data support a narrower naming/semantic-navigation signal better than a general readiness score.
- **Engineering hygiene can still matter**: a condition failing to show outcome damage in this matrix does not mean that condition is unimportant in every repo or workflow.
