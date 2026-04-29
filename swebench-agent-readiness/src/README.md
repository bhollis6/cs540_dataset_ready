# Source Code

This folder contains reusable code for the SWE-bench degradation study.

- `substrate/`: SWE-bench Verified loading and task access.
- `filters/`: task eligibility checks used to decide whether a task has enough surface for a degradation.
- `degradation/`: transformations for naming, type hints, comments/docstrings, and visible-test removal.
- `harness/`: Codex execution helpers, environment materialization, metrics parsing, and oracle replay.
- `analysis/`: packet builders and parsers for clean-vs-degraded comparisons.
- `profiles/`: per-task eligibility/profile JSON files.

The final report is not generated directly from this folder. The final analysis scripts read the exported data in `../results/` and the archived comparison packets under `../archive/provenance/`.
