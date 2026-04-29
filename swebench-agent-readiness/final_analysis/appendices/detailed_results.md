# Detailed Results Appendix

This appendix preserves the expanded RQ notes and row-level examples behind the main report.

## RQ1 Detailed Notes

RQ1 asks which degraded codebase properties mattered most for Codex performance on SWE-bench tasks.

Naming is the strongest measured outcome signal. In 30 naming comparisons, clean success rate was 80.0% and degraded success rate was 43.3%. Naming produced all 11 clean-pass to degraded-fail cases, 10 of 11 regression-damage rows, 94 additional failed regression tests, and 9 net additional failed target tests.

The signal is not repo-local. Naming failures occurred in xarray, Sympy, Requests, Matplotlib, scikit-learn, and Astropy. Leave-one-repo-out analysis still leaves at least 8 clean-pass/degraded-fail cases under every omission, so no single repo fully explains the effect.

Condition details:

- `naming`: strongest outcome damage; mean corrected token delta +304,501; mean changed-file delta +3.73.
- `comments_docstrings`: no clean-pass/degraded-fail cases; one regression-damage row on an Astropy task that already failed clean; mean token delta +155,158.
- `remove_tests`: no clean-pass to degraded-fail cases and no regression-damage rows; visible mainly through changed patch/test targets, validation behavior, and exploration efficiency loss.
- `type_hints`: no outcome damage and one clean-failure to degraded-success row; interpretation is low-confidence because 19/30 type-hints rows had zero or one annotation node, including 16 zero-annotation surfaces.

The paired design matters. There are 27 rows where the clean run already failed. These cannot be counted as degradation-caused target failures. The bundle separates:

- clean-pass to degraded-fail cases: `../tables/outcomes/transition_table/transition_table.*`
- target-test failure deltas: `../tables/overview/condition_summary/condition_summary.*`
- regression-test damage: `../tables/outcomes/pass_to_pass_damage_table/pass_to_pass_damage_table.*`
- rows where clean already failed: `../tables/outcomes/baseline_hard_tasks/baseline_hard_tasks.*`

There are 90 clean-pass/degraded-pass rows and 26 clean-fail/degraded-fail rows. One type-hints row is clean-fail/degraded-pass; treat it as stochastic/paired-run variation rather than evidence that type-hint removal improves readiness.

High-signal repos:

- `pydata/xarray`: 3 naming clean-pass/degraded-fail cases across all three selected tasks.
- `psf/requests`: 3 naming clean-pass/degraded-fail cases across all three selected tasks.
- `sympy/sympy`: 2 naming clean-pass/degraded-fail cases.
- `matplotlib/matplotlib`: one naming clean-pass/degraded-fail case plus one clean-already-failed naming regression-damage case.

Outcome-stable complete repos include Sphinx and Django under this selected task set. That does not mean the dimensions never matter there; it means the measured task surfaces did not show official outcome damage under these comparisons.

## RQ2 Detailed Notes

RQ2 asks whether agent-readiness appears multi-dimensional in process behavior. In this bundle, RQ2 is supporting evidence, not the headline result.

The RQ2 export has 256 phase rows: clean and degraded sides for each of 128 comparisons. It recovers action-count metrics from existing Codex JSONL logs:

- first edit event index,
- bootstrap and execution event counts,
- command counts,
- failed command counts,
- test-command counts,
- failed test-command counts,
- bootstrap vs execution split based on first edit.

Unavailable from current logs:

- exact timestamps,
- time to first edit,
- tokens before first edit,
- post-edit token usage,
- phase-specific token split.

Do not make phase-token or timing claims from this dataset.

Condition-level process effects:

- `naming`: mean first-edit event index delta +3.53, bootstrap command delta +1.70, execution command delta +3.10, total command delta +4.80.
- `comments_docstrings`: first-edit event index delta +2.91 and total command delta +3.12, suggesting orientation/process cost even when final outcomes are stable.
- `remove_tests`: total command delta +1.76, execution test-command delta +0.38, and patch-target shifts in `../tables/process_and_patch_shape/remove_tests_patch_target_shifts/remove_tests_patch_target_shifts.*`.
- `type_hints`: mean total command delta -1.03 and no outcome damage, but low annotation-surface availability makes this condition underpowered.

The bootstrap/execution command-delta correlation is weak (`pearson_r=0.041`, `spearman_r=0.117` in `../tables/rq2_process/rq2_phase_correlations/rq2_phase_correlations.*`), which is consistent with multi-dimensional process behavior. However, the metric family is coarse and action-count based. Treat this as suggestive, not proof.

Many paired comparisons preserve official target success while changing cost, file exploration, changed-file breadth, or validation behavior. This supports the claim that clean/degraded outcome parity does not imply process parity.

## RQ3 Detailed Notes

Original RQ3 asked:

> How accurately can an agent-in-the-loop scoring tool predict codebase agent-readiness compared to static heuristic approaches?

The current SWE-bench pivot results do not justify building a broad general-purpose agent-readiness scoring tool from the tested dimensions.

Naming was the dominant repeated outcome signal. Comments/docstrings and remove-tests were more often process-, cost-, validation-, or patch-shape-visible. Type-hints was underpowered because many selected task surfaces had zero or near-zero annotation nodes.

A broad readiness score built from these dimensions would risk becoming a dressed-up checklist unless calibrated against actual agent outcomes. The better near-term result is negative/reframed: broad readiness scoring is plausible, but this experiment only strongly supports a narrower naming/semantic-navigation signal plus weaker process metrics.

Factory-style readiness context:

- Factory public docs describe an Agent Readiness model with `/readiness-report`, five maturity levels, repository/application-scoped criteria, and technical pillars such as style/validation, build system, testing, documentation, development environment, debugging/observability, security, task discovery, and product/experimentation.
- Factory command docs describe language detection, sub-application discovery, criteria evaluation, report storage, and level scoring.
- Factory's launch post frames readiness as multiple technical pillars and mostly binary/file/configuration-style checks.

Our evidence should not be phrased as "Factory is wrong." It challenges, narrows, or weakens broad checklist-style claims in this SWE-bench bug-fix setting. Engineering hygiene can still be valuable even when a specific dimension does not measurably reduce Codex repair success in this matrix.

Future work:

- Run Factory-style criteria or a comparable static readiness rubric on the same repos and test correlation with observed task-level outcomes.
- Add feedback-loop, build/CI, flaky-test, environment-doc, and validation-speed degradations.
- Build a narrower naming/semantic-navigation predictor and validate it against held-out agent performance.
- Calibrate any readiness score against actual clean-vs-degraded agent outcomes instead of only file/configuration presence.
- Test more agents and repeated stochastic runs before generalizing beyond Codex.

## Case Examples

All clean-pass to degraded-fail cases are naming:

| Repo | Instance | Extra failed target tests | Extra failed regression tests | Token delta | Changed-file delta |
| --- | --- | ---: | ---: | ---: | ---: |
| astropy/astropy | `astropy__astropy-14182` | 1 | 0 | 311568 | 0 |
| matplotlib/matplotlib | `matplotlib__matplotlib-23412` | 1 | 21 | 1302387 | 34 |
| psf/requests | `psf__requests-1142` | 1 | 0 | 165431 | 0 |
| psf/requests | `psf__requests-1724` | 0 | 1 | 170381 | 1 |
| psf/requests | `psf__requests-1921` | 1 | 4 | 87581 | 0 |
| pydata/xarray | `pydata__xarray-3677` | 0 | 8 | 271338 | 14 |
| pydata/xarray | `pydata__xarray-4629` | 0 | 1 | 194022 | 0 |
| pydata/xarray | `pydata__xarray-4966` | 4 | 17 | 471093 | 2 |
| scikit-learn/scikit-learn | `scikit-learn__scikit-learn-25931` | 0 | 1 | 244183 | 0 |
| sympy/sympy | `sympy__sympy-11618` | 0 | 2 | -5543 | 3 |
| sympy/sympy | `sympy__sympy-12419` | 1 | 7 | 202821 | 4 |

Largest absolute token deltas include:

- `astropy__astropy-14539 x naming`: +1,323,511 tokens, outcome-stable.
- `matplotlib__matplotlib-23412 x naming`: +1,302,387 tokens, clean pass to degraded fail.
- `matplotlib__matplotlib-20676 x comments_docstrings`: +1,111,918 tokens, clean-already-failed on target.
- `sympy__sympy-12419 x comments_docstrings`: +1,006,945 tokens, outcome-stable.
- `scikit-learn__scikit-learn-26194 x remove_tests`: +938,401 tokens, outcome-stable.

Largest cheaper-degraded rows include `pytest-dev__pytest-10356 x naming` (-785,242), `django__django-16631 x remove_tests` (-675,973), `django__django-16502 x comments_docstrings` (-590,973), and `pylint-dev__pylint-4604 x type_hints` (-543,644). Do not interpret cheaper as better without reading the paired outcome and path.

Remove-tests did not create official outcome damage, but it often changed visible patch targets. Examples include Flask moving visible regression coverage from `tests/test_blueprints.py` to `tests/test_basic.py`, and scikit-learn moving visible coverage from ranking tests into alternate nearby test files. Exact changed-file pairs are in `../tables/process_and_patch_shape/remove_tests_patch_target_shifts/remove_tests_patch_target_shifts.*`.
