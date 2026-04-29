# Claim Ledger

This is the wording guardrail for the final analysis. Use it when writing slides, report prose, or discussion notes.

## Strong Evidence

| Claim | Evidence | Safer wording |
| --- | --- | --- |
| Naming is the strongest negative condition in the final matrix. | Naming has the lowest success rate (`14/30`), the largest clean-pass/degraded-fail count (`8/30`), and the largest regression burden. | Naming is the strongest measured negative condition in this corpus. |
| The final matrix is complete and internally valid. | 150 rows, no duplicate `(repo, candidate_id, condition)` rows, 0 harness errors, and 150/150 token coverage. | The final consolidated matrix passes deterministic integrity checks. |
| Clean baseline failures must be separated from degradation-associated failures. | 9 clean failures are present. Paired comparisons identify which degraded failures occurred after clean success. | A degraded failure is strongest evidence only when the same PR passed clean. |

## Suggestive Evidence

| Claim | Evidence | Safer wording |
| --- | --- | --- |
| Readiness appears multi-dimensional. | Conditions differ in failure shape, regression burden, process counts, runtime, and token use. | The process and failure-shape evidence supports a multi-dimensional framing. |
| Type hints and comments/docstrings affect comprehension/repair shape more than aggregate success. | Aggregate success matches clean, but hidden-bug-fix miss counts differ. | These conditions were more visible in failure shape than in final solve rate. |
| Remove-tests affects validation/rework more than final outcome. | Remove-tests has `24/30` successes but distinct process/rework proxies. | Removing visible tests had weak final-outcome impact here, but may still affect process. |

## Low-Confidence Or Caveated

| Claim | Why caveated | Safer wording |
| --- | --- | --- |
| Type hints do not matter. | One corpus, one agent/harness family, one run per task/condition, and selected Python task surfaces. | Type-hints removal was not an aggregate outcome-damaging condition in this matrix. |
| Comments/docstrings do not matter. | Same aggregate success as clean does not mean same process or same task difficulty. | Comments/docstrings removal was not aggregate outcome-damaging here, but changed failure shape. |
| Lower token/runtime means a condition helped. | Shorter failed paths can use fewer tokens. | Token/runtime shifts describe cost, not necessarily benefit. |

## Not Supported

| Claim to avoid | Why not supported |
| --- | --- |
| All degraded failures were caused by degradation. | Some tasks failed clean. |
| Factory-style readiness is wrong. | Static readiness tools were not run on these repos. |
| RQ2 proves a complete readiness model. | Process metrics are coarse event-count proxies with no reliable timestamps or phase-token split. |
| This generalizes to all coding agents. | The final matrix uses one Codex CLI harness family. |
