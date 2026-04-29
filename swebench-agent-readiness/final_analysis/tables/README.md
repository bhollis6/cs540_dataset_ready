# Tables Guide

Tables are grouped by purpose. Each table has its own subfolder containing the available formats, usually CSV, Markdown, and LaTeX.

- `overview/`: start here for high-level condition, repo, task, and paired-comparison summaries.
- `outcomes/`: official scoring results, including clean-pass to degraded-fail cases, target-test failures, regression-test failures, clean-already-failed rows, and type-hints surface caveats.
- `process_and_patch_shape/`: file exploration, changed-file breadth, and remove-tests patch-target shifts.
- `tokens/`: corrected token usage. Token values are raw cumulative tokens unless the column name says otherwise.
- `rq2_process/`: recovered phase/process metrics from Codex logs.
- `audit_and_manifests/`: audit sample, audited run table, and case-study manifests with source artifact paths.
- `sensitivity_and_validation/`: leave-one-repo-out checks and deterministic export validation.
- `figure_data/`: CSV data used to draw the figures.

Plain-language terms:

- `clean`: Codex ran on the original task workspace.
- `degraded`: Codex ran on the same task after one codebase property was degraded.
- `target tests`: official SWE-bench tests that should fail before the fix and pass after the fix.
- `regression tests`: official SWE-bench tests that already passed and should keep passing.
- `paired comparison`: one clean run compared with one degraded run for the same task and condition.
