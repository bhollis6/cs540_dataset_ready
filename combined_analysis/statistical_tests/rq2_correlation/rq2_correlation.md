# RQ2: Bootstrap × Execution Correlation

This folder tests whether bootstrap-phase deltas (orientation) covary with
execution-phase deltas (task completion) on the same paired clean-vs-degraded
SWE-bench runs.

See `rq2_correlation_heatmap.png` for the summary figure.

## Scope

- **Source:** `swebench-agent-readiness/final_analysis/data/rq2_phase_delta_matrix.csv`
- **Unit of analysis:** paired comparison (clean vs. degraded) — 128 pairs.
- **Backend:** SWE-bench only. The LLM-J enriched matrix does not expose `bootstrap_*` / `execution_*` columns, so this analysis cannot be pooled across both backends.
- **Bootstrap metrics tested:** event count, command count, failed commands, test commands, failed test commands (all `_delta` versions).
- **Execution metrics tested:** same five families on the post-first-edit phase.

## Method

- **Spearman rank correlation** as the headline. It is robust to count-data skew and to a few high-leverage runs.
- **Pearson** reported alongside as a linearity sanity check.
- **Holm-Bonferroni** correction applied across the full 5×5 = 25-cell grid for each correlation type independently.
- Significance threshold for highlighting: Holm-adjusted p < 0.05.

## Significant Spearman Correlations (Holm p < 0.05)

_None._

## Full Results

| bootstrap_metric | execution_metric | n | spearman_rho | spearman_p | spearman_p_holm | pearson_r | pearson_p | pearson_p_holm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Bootstrap events | Execution events | 128 | 0.117 | 0.1871 | 1 | 0.054 | 0.5435 | 1 |
| Bootstrap events | Execution commands | 128 | 0.126 | 0.1549 | 1 | 0.050 | 0.578 | 1 |
| Bootstrap events | Execution failed cmds | 128 | 0.096 | 0.2808 | 1 | -0.023 | 0.7941 | 1 |
| Bootstrap events | Execution test cmds | 128 | 0.078 | 0.3803 | 1 | 0.051 | 0.5645 | 1 |
| Bootstrap events | Execution failed test cmds | 128 | 0.159 | 0.07341 | 1 | 0.103 | 0.248 | 1 |
| Bootstrap commands | Execution events | 128 | 0.102 | 0.2525 | 1 | 0.043 | 0.6326 | 1 |
| Bootstrap commands | Execution commands | 128 | 0.117 | 0.1874 | 1 | 0.041 | 0.6459 | 1 |
| Bootstrap commands | Execution failed cmds | 128 | 0.088 | 0.3235 | 1 | -0.030 | 0.7355 | 1 |
| Bootstrap commands | Execution test cmds | 128 | 0.065 | 0.4695 | 1 | 0.040 | 0.6538 | 1 |
| Bootstrap commands | Execution failed test cmds | 128 | 0.149 | 0.09248 | 1 | 0.093 | 0.2951 | 1 |
| Bootstrap failed cmds | Execution events | 128 | -0.015 | 0.87 | 1 | -0.002 | 0.9816 | 1 |
| Bootstrap failed cmds | Execution commands | 128 | -0.053 | 0.5524 | 1 | -0.024 | 0.7909 | 1 |
| Bootstrap failed cmds | Execution failed cmds | 128 | -0.066 | 0.4602 | 1 | -0.095 | 0.2846 | 1 |
| Bootstrap failed cmds | Execution test cmds | 128 | -0.018 | 0.8371 | 1 | -0.009 | 0.9167 | 1 |
| Bootstrap failed cmds | Execution failed test cmds | 128 | -0.066 | 0.4602 | 1 | -0.054 | 0.5456 | 1 |
| Bootstrap test cmds | Execution events | 128 | 0.046 | 0.6076 | 1 | -0.023 | 0.7934 | 1 |
| Bootstrap test cmds | Execution commands | 128 | -0.009 | 0.9168 | 1 | -0.019 | 0.8337 | 1 |
| Bootstrap test cmds | Execution failed cmds | 128 | -0.032 | 0.7196 | 1 | -0.126 | 0.1573 | 1 |
| Bootstrap test cmds | Execution test cmds | 128 | 0.025 | 0.7796 | 1 | -0.098 | 0.2719 | 1 |
| Bootstrap test cmds | Execution failed test cmds | 128 | -0.075 | 0.3981 | 1 | -0.141 | 0.1112 | 1 |
| Bootstrap failed test cmds | Execution events | 128 | 0.083 | 0.3507 | 1 | 0.041 | 0.6461 | 1 |
| Bootstrap failed test cmds | Execution commands | 128 | -0.009 | 0.9159 | 1 | -0.009 | 0.9179 | 1 |
| Bootstrap failed test cmds | Execution failed cmds | 128 | -0.104 | 0.2428 | 1 | -0.225 | 0.01063 | 0.2658 |
| Bootstrap failed test cmds | Execution test cmds | 128 | -0.094 | 0.2912 | 1 | -0.127 | 0.1529 | 1 |
| Bootstrap failed test cmds | Execution failed test cmds | 128 | -0.194 | 0.02812 | 0.7031 | -0.191 | 0.03043 | 0.7304 |

## Reading the heatmap

- Cell shows Spearman ρ (left panel) or Pearson r (right panel).
- Color: red = positive, blue = negative, white = near zero.
- Stars use **Holm-adjusted** p, not raw p. A cell can have ρ ≈ 0.2 and still fail to reach significance after correction.

## Caveats

- A correlation between two deltas means: **when degradation perturbs bootstrap, it tends to perturb execution in the same (or opposite) direction.** It does *not* prove that bootstrap behavior causes execution behavior — both could share an upstream cause (the degradation itself, or task difficulty).
- Same-row "x event count" vs. "y event count" correlations are mechanically related: both phases of a longer-than-clean run will tend to be longer in absolute terms. The interesting cells are off-diagonal — e.g., does extra bootstrap *failed-command* activity predict more execution test failures?
- This is paired delta analysis, so repo and task identity are partialled out *within the paired structure*. Cross-task variation still drives a lot of the spread.
- LLM-J is omitted by data availability, not by design. Re-running this analysis after enriching the LLM-J matrix with phase-split metrics would let it pool across both backends.
