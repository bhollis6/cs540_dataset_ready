# Combined Agent Readiness Analysis

This folder is the small cross-backend handoff package. It combines the custom-repo backend in `LLM-J/` with the SWE-bench backend in `swebench-agent-readiness/`.

## Short Answer

Both backends point in the same direction: naming/semantic clarity is the strongest tested readiness signal for Codex repair success.

Across the paired comparison view, naming produced `19` clean-pass / degraded-fail transitions out of `60` naming comparisons. The other degradations together produced `6` such transitions across `185` comparisons.

The combined result does not support a broad checklist-style readiness score yet. It supports a narrower claim: naming and semantic navigation deserve special weight, while type hints, comments/docstrings, and visible tests showed weaker or more process-shaped evidence in these runs.

## What Is Combined

| Backend | Repos | Tasks | Paired comparisons | Clean-pass / degraded-fail |
| --- | ---: | ---: | ---: | ---: |
| Custom repos | 10 | 30 | 120 | 14 |
| SWE-bench | 10 | 31 | 125 | 11 |
| Combined | 20 | 61 | 245 | 25 |

The common unit is a same-task paired comparison: the same bug-fix task under clean and degraded conditions. This avoids pretending the two backend matrices have identical raw structure.

## Backend Results Side By Side

| Condition | Custom repos clean-pass / degraded-fail | SWE-bench clean-pass / degraded-fail | Combined |
| --- | ---: | ---: | ---: |
| Naming | 8/30 | 11/30 | 19/60 |
| Type hints | 2/30 | 0/30 | 2/60 |
| Comments/docstrings | 3/30 | 0/33 | 3/63 |
| Remove tests | 1/30 | 0/32 | 1/62 |

The important pattern is not that every backend row is identical. It is that naming is the only condition with a strong negative final-outcome signal in both backends.

## RQ1: What Hurt Final Repair Success?

Naming is the only condition that is strongly negative in both backends.

| Condition | Paired comparisons | Clean success | Degraded success | Clean-pass / degraded-fail | Success-rate shift |
| --- | ---: | ---: | ---: | ---: | ---: |
| Naming | 60 | 45 | 27 | 19 | -0.300 |
| Type hints | 60 | 43 | 44 | 2 | 0.017 |
| Comments/docstrings | 63 | 47 | 47 | 3 | 0.000 |
| Remove tests | 62 | 47 | 50 | 1 | 0.048 |

Use `figures/clean_pass_to_degraded_fail_counts.png` as the main presentation figure.

## RQ2: Did Degradations Change The Process?

Yes, but this remains supporting evidence. The clean/degraded outcome is still the headline; process metrics explain how the runs changed.

The shared combined metrics use corrected tokens: input plus output tokens, excluding cached input. That gives a more comparable token view across both backends.

| Condition | Median corrected token delta | Mean token delta % | Token-higher pairs | Mean files-opened delta | Mean exploration-efficiency delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| Naming | 52852.0 | 60.0% | 46/60 | -0.05 | -3.4 pp |
| Type hints | 6875.0 | 18.8% | 32/60 | -0.13 | 1.3 pp |
| Comments/docstrings | 33543.0 | 34.5% | 47/63 | 0.03 | -1.5 pp |
| Remove tests | 15328.0 | 21.8% | 36/62 | 0.13 | -16.6 pp |

Simple read:

- Naming is the clearest combined cost signal: it raised corrected token use by about `60.0%` on average and had higher token use in `46/60` pairs.
- Comments/docstrings and remove-tests also show token-cost movement, but without the same final-outcome damage.
- Remove-tests did not hurt final success much, but it reduced exploration efficiency the most: `-16.6` percentage points on average.
- Files-opened deltas are small in the pooled view, so they should be read as weak search-breadth evidence rather than a headline result.
- Backend-specific process metrics still matter: custom repos include runtime and validation-command deltas; SWE-bench includes changed-file deltas. See `tables/process_metric_summary_by_backend_condition.csv`.

## RQ3: Readiness Tool Takeaway

Do not build or claim a broad readiness score from these results alone.

The safer conclusion is:

> Across two backends, naming/semantic clarity is the best-supported readiness signal. Broader checklist-style readiness claims need empirical calibration against actual agent outcomes.

That is compatible with static readiness tooling, but it argues the tooling should be calibrated, outcome-backed, and honest about which dimensions are proven versus only plausible.

## Presentation Figures

- `figures/clean_pass_to_degraded_fail_counts.png`: main RQ1 result.
- `figures/combined_success_rate_shift.png`: clean versus degraded success rates in the combined paired view.
- `figures/regression_failure_delta.png`: additional previously passing test failures versus clean.
- `figures/backend_transition_heatmap.png`: backend-by-condition transition count.
- `figures/corrected_token_delta_pct.png`: combined corrected-token burden.
- `figures/files_opened_delta.png`: search breadth proxy.
- `figures/exploration_efficiency_delta.png`: search focus proxy.
- `figures/backend_token_delta_pct_heatmap.png`: backend-specific token shift.

## Backend-Specific Metric Tables

The combined tables keep only the shared, paper-level metrics. For backend-specific detail:

- Custom repos: `../LLM-J/final_rq_analysis/tables/process/rq2_process_metric_summary/rq2_process_metric_summary.csv`
- Custom repos token/runtime: `../LLM-J/final_rq_analysis/tables/tokens_runtime/token_runtime_summary/token_runtime_summary.csv`
- SWE-bench process: `../swebench-agent-readiness/final_analysis/tables/rq2_process/rq2_phase_metric_summary/rq2_phase_metric_summary.csv`
- SWE-bench patch/search shape: `../swebench-agent-readiness/final_analysis/tables/process_and_patch_shape/exploration_process_summary/exploration_process_summary.csv`
- SWE-bench tokens: `../swebench-agent-readiness/final_analysis/tables/tokens/token_summary/token_summary.csv`

## Caveats

- The custom backend and SWE-bench backend use different raw data layouts and scoring infrastructure.
- SWE-bench is restricted here to the 10 fully complete repos so the combined story is 10 custom repos plus 10 SWE-bench repos.
- Some SWE-bench complete repos have more than three represented tasks or replicated condition rows; this is why the paired-comparison count is not exactly `10 * 3 * 4`.
- This is a Codex-centered study, not a universal coding-agent benchmark.
- Same-task clean/degraded comparisons are the strongest evidence. Clean-baseline failures should not be over-attributed to degradation.
- Corrected token deltas exclude cached input. LLM-J backend-specific tables still also report total tokens including cached input.
