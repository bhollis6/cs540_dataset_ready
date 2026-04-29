# Scripts

These scripts rebuild and validate the final-analysis bundle from the source exports in `../../results/` and archived comparison packets in `../../archive/provenance/`.

Recommended order from the repository root:

```bash
PYTHONPATH=. uv run python final_analysis/scripts/build_analysis_tables.py
PYTHONPATH=. uv run python final_analysis/scripts/build_case_study_manifests.py
PYTHONPATH=. uv run python final_analysis/scripts/build_manual_audit.py
PYTHONPATH=. uv run python final_analysis/scripts/enrich_rq2_metrics.py
PYTHONPATH=. uv run python final_analysis/scripts/build_figures.py
PYTHONPATH=. uv run python final_analysis/scripts/organize_outputs.py
PYTHONPATH=. uv run python final_analysis/scripts/validate_exports.py
```

The scripts are analysis-only. They do not run new Codex or SWE-bench experiment cells.
