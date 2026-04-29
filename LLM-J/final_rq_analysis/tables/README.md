# Tables

Tables are grouped by purpose. Core tables are exported as `.csv`, `.md`, and `.tex`.

Plain-language terms used here:
- `Run`: one agent attempt on one historical PR under one codebase condition.
- `Success`: hidden bug-fix tests passed and previously passing tests did not regress after applying the agent's non-test code changes.
- `Hidden bug-fix tests`: tests added by the original PR that should pass after a correct repair.
- `Previously passing tests`: existing tests that should keep passing. Failures here are regressions.
- `Condition`: the codebase version shown to the agent, such as clean, naming-degraded, or tests-removed.

- `overview/`: Top-level condition, repository, PR, and paired-comparison summaries.
- `outcomes/`: Paired clean/degraded outcomes, baseline-hard tasks, and condition transitions.
- `failure_modes/`: Tables that explain how failed runs failed.
- `process/`: Recovered Codex process metrics and correlations.
- `tokens_runtime/`: Duration and token-use summaries. Token totals include cached input where labeled.
- `audit_and_manifests/`: Manual-audit sample manifests, validation checks, and raw-artifact references.
- `metadata/`: PR metadata and source-artifact lookup tables.
- `sensitivity_and_validation/`: Checks for per-repo influence and paired condition effects.
- `figure_data/`: CSV data behind the generated figures.
