# SWE-bench Agent Readiness Study

This repository contains the SWE-bench branch of the LLM-J degradation study. It asks a focused question:

> When the same bug-fix task is run in a clean workspace and in a deliberately degraded workspace, which codebase properties measurably change Codex's repair success or repair process?

The current result is based on SWE-bench Verified tasks, paired clean-vs-degraded Codex runs, and oracle replay against the official target and regression tests.

## Current Result

The clearest measured signal is naming quality. In this matrix, all 11 cases where Codex passed clean and failed after degradation came from the naming condition. Naming also produced 10 of the 11 regression-damage rows.

The process evidence is useful but weaker. Other degradations changed search, validation behavior, patch shape, or token use, but those process shifts did not translate into the same strong outcome-damage signal.

The readiness-tool conclusion should stay narrow: these data support a naming/semantic-navigation risk signal better than a broad all-purpose readiness score.

## Read Order

Start here:

1. `final_analysis/REPORT.md` for the main narrative.
2. `final_analysis/threats_to_validity.md` for limitations.
3. `final_analysis/claim_ledger.md` for claim boundaries and safer wording.
4. `final_analysis/appendices/` for methods, audit details, and row-level backup.

`START_HERE.md` was removed because the root README now serves that role.

## Repository Map

- `final_analysis/`: final report, appendices, generated figures, generated tables, derived data, and rebuild/validation scripts.
- `results/`: source-of-truth RQ1 and RQ2 exports used by the final analysis.
- `src/`: reusable code for task filtering, degradations, Codex harnessing, oracle replay, and packet parsing.
- `tests/`: unit tests for the reusable code.
- `schemas/`: JSON schema for task eligibility/profile files.
- `docs/`: current docs index. Historical drafts were moved out of the front door.
- `archive/`: historical notes, run-provenance files, and older packaged outputs.
- `runs/`: local raw run artifacts. This folder is intentionally ignored by Git.

## Headline Counts

- 128 paired clean-vs-degraded comparisons.
- 256 individual clean/degraded run rows in the RQ2 process export.
- 32 unique SWE-bench Verified tasks.
- 11 represented repositories.
- 10 fully complete repositories.
- 11 clean-pass to degraded-fail cases.
- 11 regression-damage rows.
- Manual audit scope: 79 paired comparisons, or 158 individual clean/degraded runs.

Corrected token totals use `input_tokens + output_tokens`. Cached input tokens are diagnostic and are not added.

## Reproduce The Final Analysis

From the repository root:

```bash
PYTHONPATH=. uv run python final_analysis/scripts/validate_exports.py
PYTHONPATH=. uv run --extra dev ruff check src tests final_analysis/scripts
PYTHONPATH=. uv run --extra dev pytest
```

To rebuild the generated final-analysis artifacts after changing the scripts:

```bash
PYTHONPATH=. uv run python final_analysis/scripts/build_analysis_tables.py
PYTHONPATH=. uv run python final_analysis/scripts/build_case_study_manifests.py
PYTHONPATH=. uv run python final_analysis/scripts/build_manual_audit.py
PYTHONPATH=. uv run python final_analysis/scripts/enrich_rq2_metrics.py
PYTHONPATH=. uv run python final_analysis/scripts/build_figures.py
PYTHONPATH=. uv run python final_analysis/scripts/organize_outputs.py
PYTHONPATH=. uv run python final_analysis/scripts/validate_exports.py
```

These commands only rebuild analysis outputs. They do not launch new SWE-bench/Codex experiment runs.

## Notes For GitHub

The repo is designed to be pushed without local raw run logs. `runs/`, caches, virtual environments, and generated Python bytecode are ignored. Historical material that explains how the experiment developed lives in `archive/` instead of the main read path.
