# Combined Analysis

This is the small, presentation-oriented folder that brings together the two backend studies:

- `../LLM-J/`: custom-repo backend.
- `../swebench-agent-readiness/`: SWE-bench backend.

Start with `REPORT.md`. The `tables/` and `figures/` folders contain only the combined summaries most likely to be useful in a paper, deck, or project handoff.

Backend-specific process and token tables stay in each backend's own final-analysis folder. This package links to them from `REPORT.md` rather than copying every detailed table here.

## Rebuild

Run from the parent directory that contains `LLM-J/`, `swebench-agent-readiness/`, and `combined_analysis/`:

```bash
python combined_analysis/scripts/build_combined_analysis.py
```

Use whichever Python environment has `pandas`, `numpy`, and `matplotlib` installed.
