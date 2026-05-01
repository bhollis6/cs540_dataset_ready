# Signed-Rank Test Results

Wilcoxon signed-rank tests on the paired clean-vs-degraded deltas in
`../data/combined_paired_matrix.csv`. Each test is two-sided with
`H0: median(delta) = 0`. Zero-valued pairs are dropped by `scipy.stats.wilcoxon`
(default `zero_method="wilcox"`). Holm-Bonferroni adjustment is applied within
each metric family (the four conditions tested for that metric).

See `signed_rank_tests.png` for the summary figure.

## Method

- Source: combined paired matrix (245 pairs across both backends).
- Test: `scipy.stats.wilcoxon`, two-sided, default zero handling.
- Multiple-comparison correction: Holm step-down within each metric family.
- Significance threshold: Holm-adjusted p < 0.05.

## Significant Effects (Holm p < 0.05)

| metric | condition | n_pairs | n_nonzero | median_delta | p_value | p_value_holm |
| --- | --- | --- | --- | --- | --- | --- |
| Corrected tokens (% of clean) | Naming | 60 | 60 | 0.4792 | 7.537e-07 | 3.015e-06 |
| Corrected tokens (% of clean) | Comments/docstrings | 63 | 63 | 0.2076 | 1.179e-05 | 3.536e-05 |
| Corrected tokens (% of clean) | Type hints | 60 | 60 | 0.0755 | 0.01232 | 0.02463 |
| Corrected tokens (% of clean) | Remove tests | 62 | 62 | 0.0947 | 0.03453 | 0.03453 |
| Corrected tokens (absolute) | Naming | 60 | 60 | 52852.0 | 5.972e-06 | 2.389e-05 |
| Corrected tokens (absolute) | Comments/docstrings | 63 | 63 | 33543.0 | 9.753e-06 | 2.926e-05 |
| Exploration efficiency | Remove tests | 62 | 49 | -0.0928 | 3.062e-05 | 0.0001225 |
| Hidden bug-fix failures | Naming | 60 | 15 | 0.0 | 0.001308 | 0.005232 |
| Regression failures | Naming | 60 | 19 | 0.0 | 0.0001938 | 0.0005815 |

## Full Results

| metric | condition | n_pairs | n_nonzero | n_positive | n_negative | median_delta | wilcoxon_W | p_value | p_value_holm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Corrected tokens (% of clean) | Naming | 60 | 60 | 46 | 14 | 0.4792 | 243.0 | 7.537e-07 | 3.015e-06 |
| Corrected tokens (% of clean) | Type hints | 60 | 60 | 32 | 28 | 0.0755 | 575.0 | 0.01232 | 0.02463 |
| Corrected tokens (% of clean) | Comments/docstrings | 63 | 63 | 47 | 16 | 0.2076 | 368.0 | 1.179e-05 | 3.536e-05 |
| Corrected tokens (% of clean) | Remove tests | 62 | 62 | 36 | 26 | 0.0947 | 675.0 | 0.03453 | 0.03453 |
| Corrected tokens (absolute) | Naming | 60 | 60 | 46 | 14 | 52852.0 | 300.0 | 5.972e-06 | 2.389e-05 |
| Corrected tokens (absolute) | Type hints | 60 | 60 | 32 | 28 | 6875.0 | 831.0 | 0.5363 | 0.5363 |
| Corrected tokens (absolute) | Comments/docstrings | 63 | 63 | 47 | 16 | 33543.0 | 362.0 | 9.753e-06 | 2.926e-05 |
| Corrected tokens (absolute) | Remove tests | 62 | 62 | 36 | 26 | 15328.0 | 747.0 | 0.1076 | 0.2152 |
| Files opened before first edit | Naming | 60 | 36 | 22 | 14 | 0.0 | 327.0 | 0.9237 | 1 |
| Files opened before first edit | Type hints | 60 | 36 | 17 | 19 | 0.0 | 301.0 | 0.6064 | 1 |
| Files opened before first edit | Comments/docstrings | 63 | 40 | 23 | 17 | 0.0 | 400.0 | 0.891 | 1 |
| Files opened before first edit | Remove tests | 62 | 52 | 28 | 24 | 0.0 | 625.0 | 0.5537 | 1 |
| Exploration efficiency | Naming | 60 | 38 | 16 | 22 | 0.0 | 270.5 | 0.1466 | 0.4399 |
| Exploration efficiency | Type hints | 60 | 37 | 19 | 18 | 0.0 | 315.0 | 0.5816 | 0.9438 |
| Exploration efficiency | Comments/docstrings | 63 | 42 | 19 | 23 | 0.0 | 394.0 | 0.4719 | 0.9438 |
| Exploration efficiency | Remove tests | 62 | 49 | 12 | 37 | -0.0928 | 193.5 | 3.062e-05 | 0.0001225 |
| Hidden bug-fix failures | Naming | 60 | 15 | 14 | 1 | 0.0 | 6.0 | 0.001308 | 0.005232 |
| Hidden bug-fix failures | Type hints | 60 | 6 | 3 | 3 | 0.0 | 6.0 | 0.3401 | 0.6802 |
| Hidden bug-fix failures | Comments/docstrings | 63 | 8 | 6 | 2 | 0.0 | 6.0 | 0.08326 | 0.2498 |
| Hidden bug-fix failures | Remove tests | 62 | 6 | 3 | 3 | 0.0 | 7.0 | 0.4568 | 0.6802 |
| Regression failures | Naming | 60 | 19 | 18 | 1 | 0.0 | 2.5 | 0.0001938 | 0.0005815 |
| Regression failures | Type hints | 60 | 0 | 0 | 0 | 0.0 | nan | nan | nan |
| Regression failures | Comments/docstrings | 63 | 3 | 1 | 2 | 0.0 | 3.0 | 1 | 1 |
| Regression failures | Remove tests | 62 | 1 | 0 | 1 | 0.0 | 0.0 | 0.3173 | 0.6346 |

## Notes

- Sign of `median_delta` is informative: positive means the degraded run had a larger value than clean.
- For count metrics with many ties at zero (`hidden_bug_fix_failed_delta`, `regression_failed_delta`), `n_nonzero` is much smaller than `n_pairs`. The summary figure falls back to mean delta when median is exactly 0 so the bars are not flat. Treat marginal p-values cautiously.
- Tests are pooled across both backends. Per-backend and per-repo splits are intentionally out of scope here.
- These are paired marginal tests, not a multi-factor model: they tell you whether each degradation shifts a metric on average, not how degradations interact.
- `token_delta_pct` is per-pair (degraded - clean) / clean; rows where clean == 0 are dropped, so `n_pairs` may be smaller than for `token_delta`.
