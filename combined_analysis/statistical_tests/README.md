# Statistical Tests

Two follow-up statistical analyses on top of the descriptive bundle in
`combined_analysis/`. Each lives in its own subfolder and writes all
outputs there.

| Subfolder | What it tests | Source data | Backends |
| --- | --- | --- | --- |
| [signed_rank/](signed_rank/) | Wilcoxon signed-rank tests on per-pair clean-vs-degraded deltas | `combined_analysis/data/combined_paired_matrix.csv` | LLM-J + SWE-bench (pooled) |
| [rq2_correlation/](rq2_correlation/) | Bootstrap × execution phase correlations + per-condition effect sizes | `swebench-agent-readiness/final_analysis/data/rq2_phase_delta_matrix.csv` | SWE-bench only |

## Prerequisites

Any Python 3 with these four packages:

- `pandas`
- `numpy`
- `scipy`
- `matplotlib`

If a package is missing, install it once into whichever Python you use:

```powershell
python -m pip install pandas numpy scipy matplotlib
```

## How to run

Run from the repository root (the parent of `combined_analysis/`).

### Signed-rank tests

```powershell
python combined_analysis\statistical_tests\signed_rank\run_signed_rank_tests.py
```



**What it does.** For each of the four degradations (naming, type hints,
comments/docstrings, remove tests), tests `H0: median(delta) = 0` for these
per-pair deltas:

- `token_delta` and `token_delta_pct` — corrected tokens (input + output, excluding cached input), absolute and as a fraction of clean.
- `files_opened_delta` — files opened before the first edit.
- `exploration_efficiency_delta` — relevant-file ratio.
- `hidden_bug_fix_failed_delta` — failures on the held-out bug-fix tests.
- `regression_failed_delta` — regressions on previously passing tests.

Test is `scipy.stats.wilcoxon`, two-sided, default zero handling
(`zero_method="wilcox"`). Holm-Bonferroni adjustment is applied within each
metric family (the four conditions tested for that metric).

**Outputs (overwritten on each run, all in `signed_rank/`):**

| File | Contents |
| --- | --- |
| `signed_rank_tests.csv` / `.md` | Full per-(metric, condition) test results. |
| `STATS.md` | Narrative report with significant findings. |
| `signed_rank_tests.png` / `.pdf` | 2×3 summary figure: median delta per condition per metric, colored by direction, annotated with significance stars. |

### RQ2 bootstrap × execution analysis

```powershell
python combined_analysis\statistical_tests\rq2_correlation\run_rq2_correlation.py
```

**What it does.** Two related analyses on the SWE-bench paired comparison
matrix. Bootstrap = events before the first meaningful code edit;
execution = events from the first edit onward
(`LLM-J/docs/experimental_pipeline.md`, Stage 6).

1. **Phase × phase correlation.** Spearman (rank-based, primary) and
   Pearson (linear, secondary) correlation between every
   `bootstrap_*_delta` and every `execution_*_delta`. Five bootstrap
   metrics × five execution metrics = 25 cells. Holm correction across
   the grid.
2. **Per-condition effect size.** For each phase metric × each of the
   four degradations, paired rank-biserial r derived from
   `scipy.stats.wilcoxon`. Bounded `[-1, +1]`. Holm correction across
   all 40 cells (10 metrics × 4 conditions).

This analysis is **SWE-bench-only** because the LLM-J enriched matrix
does not expose phase-split columns.

**Outputs (overwritten on each run, all in `rq2_correlation/`):**

| File | Contents |
| --- | --- |
| `rq2_correlation.csv` / `.md` | 25 phase × phase correlations. |
| `rq2_correlation_heatmap.png` / `.pdf` | Two-panel heatmap (Spearman + Pearson). |
| `rq2_effect_size.csv` / `.md` | 40 per-condition effect sizes. |
| `rq2_effect_size_heatmap.png` / `.pdf` | Heatmap of rank-biserial r by phase metric × degradation. |
| `RQ2_CORRELATION.md` | Narrative report covering both analyses. |

## Notes on interpretation

- All tests use `H0: no shift / no association` and report two-sided p-values with Holm-Bonferroni correction. Significance stars in figures are based on Holm-adjusted p-values: `***` p < 0.001, `**` p < 0.01, `*` p < 0.05.
- For count metrics with many ties at zero, `n_nonzero` is much smaller than `n_pairs`. Treat marginal p-values cautiously and check the raw counts.
- These are paired marginal tests, not multi-factor models. They tell you whether each effect is detectable on average, not how effects interact.
- `rq2_correlation/` cannot be pooled across backends until the LLM-J enriched matrix is enriched with bootstrap/execution phase splits.

## Rebuilding the input data

These scripts assume `combined_analysis/data/combined_paired_matrix.csv`
and `swebench-agent-readiness/final_analysis/data/rq2_phase_delta_matrix.csv`
already exist. If they do not, regenerate them from each backend's own
build pipeline first — see `combined_analysis/scripts/build_combined_analysis.py`
for the combined paired matrix.
