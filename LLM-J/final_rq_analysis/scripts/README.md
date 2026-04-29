# Scripts

These scripts rebuild the custom-repo final-analysis bundle from the committed final matrix and preserved local provenance artifacts.

Recommended order from `LLM-J/`:

```bash
python final_rq_analysis/scripts/enrich_rq2_metrics.py
python final_rq_analysis/scripts/build_analysis_tables.py
python final_rq_analysis/scripts/build_figures.py
python -m py_compile final_rq_analysis/scripts/*.py
```

The scripts rebuild analysis outputs only. They do not collect new data, onboard repositories, or run new Codex tasks.
