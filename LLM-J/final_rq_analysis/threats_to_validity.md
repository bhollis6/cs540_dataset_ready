# Threats To Validity / Limitations

Keep this close to any report or slide deck that uses the custom-repo results. The strongest result is naming, but the experiment is still bounded.

## Experimental Scope

- **Single agent/harness family**: results are Codex-specific and should not be generalized to all coding agents without replication.
- **Limited replications**: the final matrix has one run per `(repo, historical PR, condition)`, so agent stochasticity is under-sampled.
- **Curated repos and PRs**: tasks were selected for feasibility, testability, and relevance. This is not a random sample of all software work.
- **Python-only corpus**: all final repos are Python projects.

## Scoring And Interpretation

- **Same-task comparison is required**: a degraded failure is strongest evidence when the clean run on the same PR passed.
- **Clean baseline failures**: 9 runs failed clean. Degraded failures on those PRs are not strong degradation-caused evidence by themselves.
- **Regression burden**: previously passing test failures are real damage, but they can appear alongside hidden-bug-fix misses or baseline-hard tasks.
- **Scoring replay assumptions**: hidden bug-fix and previously passing test counts are only as reliable as the historical test reconstruction and replay.
- **Remove-tests condition**: visible tests were removed while Codex worked, but hidden scoring tests were restored for evaluation.

## Condition-Specific Limits

- **Naming has the strongest evidence**: naming is supported by aggregate outcomes, paired outcomes, failure shape, and manual audit examples.
- **Type hints is not disproven**: type-hints removal did not hurt aggregate success here, but that does not prove type hints never matter.
- **Comments/docstrings is mostly failure-shape evidence**: it did not reduce aggregate success, but it changed the kind of misses observed.
- **Remove-tests is mostly process evidence**: it had weak final-outcome impact in this matrix, but it may still affect validation behavior.

## Process-Metric Limits

- **No reliable timing claims**: preserved Codex logs do not provide reliable per-event timestamps.
- **No phase-token claims**: logs do not expose tokens before versus after first edit.
- **Coarse metrics**: process metrics are recoverable action counts, not a full model of agent cognition.
- **Token interpretation**: total token usage includes cached input tokens where labeled; lower token use does not automatically mean a condition helped.

## Environment And Reproducibility Limits

- **Historical dependency reconstruction is hard**: repo profiles and container-backed probes reduce risk but cannot eliminate host/environment effects.
- **Some execution depended on host Codex subscription behavior**: invalid auth artifacts were excluded from the final matrix.
- **Known exclusions**: `pydantic-settings_pr_788 naming` and invalid `uvicorn` auth attempts were excluded for matrix integrity.
- **Raw artifacts remain local**: the GitHub-ready bundle contains lightweight exports and references, not copied worktrees or full run directories.

## RQ3 Limits

- **Static readiness tools were not run**: Factory-style comparison is documentary and conceptual, not an empirical head-to-head.
- **No broad readiness-score calibration yet**: these data support calibrated, outcome-backed claims better than a broad checklist score.
- **Engineering hygiene can still matter**: weak outcome signal for a tested dimension does not mean the dimension is unimportant in every workflow.
