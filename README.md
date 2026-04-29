# Agent Readiness Study

This repository contains the final handoff package for the agent-readiness degradation study.

Start with the whole-study synthesis:

1. `combined_analysis/REPORT.md`
2. `combined_analysis/tables/README.md`
3. `combined_analysis/figures/README.md`

Backend-specific details live here:

- `LLM-J/`: custom-repo backend using historical Python pull requests.
- `LLM-J/final_rq_analysis/REPORT.md`: custom-repo final report.
- `swebench-agent-readiness/`: SWE-bench backend using SWE-bench Verified tasks.
- `swebench-agent-readiness/final_analysis/REPORT.md`: SWE-bench final report.

## Short Result

Across both backends, naming and semantic clarity are the strongest tested readiness signal for Codex repair success. Type hints, comments/docstrings, and visible tests showed weaker or more process-shaped evidence in these runs.

The safest conclusion is narrow: these results support outcome-calibrated readiness signals, especially around naming/semantic navigation. They do not yet support a broad all-purpose readiness score.

## What Is In Scope

- Final reports, generated tables, generated figures, and analysis scripts.
- Lightweight derived data needed to rebuild the final tables and figures.
- Historical/archive notes that explain provenance.

Raw run directories, cloned repositories, local Codex state, virtual environments, and worktrees are intentionally not part of the GitHub read path.

## Rebuild

From this repository root:

```bash
python combined_analysis/scripts/build_combined_analysis.py
```

For backend-specific rebuilds, use the commands in `LLM-J/README.md` and `swebench-agent-readiness/README.md`.

Root-level notebooks and query exports are legacy provenance artifacts. They are not the recommended way to understand or reproduce the final study.
