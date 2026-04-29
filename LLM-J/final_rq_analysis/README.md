# Final RQ Analysis

This folder is the final analysis bundle for the custom-repo LLM-J agent-readiness study.

## Read Order

1. `REPORT.md`: main result narrative for teammates.
2. `threats_to_validity.md`: limitations to keep attached to the result.
3. `claim_ledger.md`: claim boundaries and safer wording.
4. `appendices/README.md`: backup material for methods, audit details, and artifact locations.

The report is the main entry point. The appendices are for verification and detail.

## One-Minute Result

We ran Codex on 30 historical PR tasks across 10 Python repositories under five workspace conditions: clean, naming-degraded, type-hints removed, comments/docstrings removed, and visible tests removed.

The clearest result is naming. Naming solved `14/30` runs, compared with clean at `21/30`, and produced the largest regression burden in previously passing tests.

Removing visible tests had the weakest final-outcome impact in this matrix: `24/30` runs succeeded. That does not mean tests are unimportant; it means this experiment did not show a large final solve-rate drop from hiding visible tests while restoring hidden tests for scoring.

The readiness-tool conclusion is cautious: these data support empirically calibrated, narrower signals better than a broad checklist-style readiness score.

## Key Counts

- `150` scored runs.
- `10` repositories.
- `30` historical PR tasks.
- `101` successes and `49` failures.
- `0` harness errors in the final matrix.
- `150/150` token coverage.
- Manual audit manifest: `26` runs.

## Reproduce The Final Analysis

Run from the repository root:

```bash
python final_rq_analysis/scripts/enrich_rq2_metrics.py
python final_rq_analysis/scripts/build_analysis_tables.py
python final_rq_analysis/scripts/build_figures.py
python -m py_compile final_rq_analysis/scripts/*.py
```

These commands rebuild analysis outputs only. They do not collect new data or run new Stage 5 agent tasks.

## Folder Map

- `data/`: committed source matrix copy and generated analysis matrices.
- `tables/`: exact values behind the report, grouped by purpose.
- `figures/`: PNG/PDF/SVG exports, one folder per figure.
- `scripts/`: reproducible analysis builders.
- `appendices/`: methods, detailed results, audit notes, and data manifest.

Raw run directories and worktrees are intentionally not copied here.
