# LLM-J Custom-Repo Agent Readiness Study

This repository contains the custom-repo branch of the LLM-J agent-readiness degradation study.

The study asks:

> When Codex works on the same historical bug-fix task under different codebase conditions, which codebase properties measurably change final repair success, regression risk, or repair process?

The final custom-repo result is based on 30 historical pull requests across 10 Python repositories, five workspace conditions, and final scoring against hidden bug-fix tests plus previously passing tests.

## Current Result

The clearest measured signal is naming quality. Naming degradation solved `14/30` runs, compared with clean at `21/30`, and produced the largest regression burden in previously passing tests.

Removing visible tests had the weakest final-outcome impact in this matrix: `24/30` runs succeeded. That does not mean tests are unimportant; hidden tests were still restored for scoring, and remove-tests may still affect validation and rework behavior.

The readiness-tool conclusion should stay cautious: these data support empirically calibrated, outcome-backed readiness claims better than a broad checklist-style readiness score.

## Read Order

Start here:

1. `final_rq_analysis/REPORT.md` for the main narrative.
2. `final_rq_analysis/threats_to_validity.md` for limitations.
3. `final_rq_analysis/claim_ledger.md` for claim boundaries and safer wording.
4. `final_rq_analysis/appendices/` for methods, audit details, and artifact locations.

The old split handoff docs and run-era notes were moved to `archive/`.

## Repository Map

- `final_rq_analysis/`: final report, appendices, generated figures, generated tables, derived data, and rebuild scripts.
- `src/`: reusable pipeline code for scraping, judging, deep evaluation, repo readiness, and run planning.
- `tests/`: unit tests for the reusable code.
- `docs/`: current pipeline and contract documentation.
- `candidates/`, `results/`, `deep_results/`: lightweight candidate and selection artifacts.
- `repo_profiles/`, `packets/`, `run_plans/`: experiment admission and execution planning artifacts.
- `archive/`: historical notes, stage summaries, early writeups, and references.

Local raw run artifacts are intentionally not part of the GitHub read path. `runs/`, `comparison_slices/`, `clones/`, caches, and Codex local state are ignored.

## Headline Counts

- 10 repositories.
- 30 historical PR tasks.
- 150 scored Codex runs.
- 101 successes and 49 failures.
- 0 harness errors in the final matrix.
- 150/150 token coverage.
- Manual audit manifest: 26 high-interpretation runs.

## Reproduce The Final Analysis

From the repository root:

```bash
python final_rq_analysis/scripts/enrich_rq2_metrics.py
python final_rq_analysis/scripts/build_analysis_tables.py
python final_rq_analysis/scripts/build_figures.py
python -m py_compile final_rq_analysis/scripts/*.py
```

These commands only rebuild analysis outputs. They do not onboard repos, collect new Stage 5 runs, or copy raw worktrees into the final analysis bundle.

## Developer Setup

```bash
pip install -e ".[dev]"
cp .env.example .env
```

The pipeline code expects a GitHub token for fresh scraping. Final-analysis rebuilds do not need new scraping or LLM calls.
