# SWE-bench Agent Readiness Final Analysis

This folder is the final analysis bundle for the SWE-bench agent-readiness study.

## Read Order

Suggested read order:

1. `REPORT.md`: the main result narrative, including RQ1, RQ2, and RQ3.
2. `threats_to_validity.md`: limitations to keep attached to the result.
3. `claim_ledger.md`: exact claim boundaries and safer wording.
4. `appendices/README.md`: backup material for audit, methods, data, and detailed row-level examples.

The report is the main entry point. The appendices are there for details, audit checks, and artifact locations.

## One-Minute Result

We compared Codex on the same SWE-bench Verified bug-fix tasks before and after changing one codebase property.

The strongest result is naming. All 11 cases where Codex passed clean but failed after degradation came from the naming condition. Naming also produced 10 of 11 regression-damage rows.

The process results are useful but weaker. Other degradations often changed how Codex searched, validated, spent tokens, or shaped patches, even when the final pass/fail result stayed the same.

The readiness-tool conclusion is cautious: these data support a narrow naming/semantic-navigation risk signal better than a broad all-purpose readiness score.

## Top-Level Files

- `REPORT.md`: main report.
- `threats_to_validity.md`: limitations and caveats.
- `claim_ledger.md`: claim evidence and wording guardrails.
- `figures/`: slide-ready plots.
- `tables/`: source tables for exact values.
- `data/`: copied source exports and generated matrices/manifests.
- `scripts/`: scripts used to build the final analysis artifacts.
- `appendices/`: detailed backup docs.

## Key Counts

- 128 paired clean-vs-degraded comparisons.
- 256 individual clean/degraded run rows in the RQ2 process export.
- 32 unique SWE-bench Verified tasks.
- 11 represented repos.
- 10 fully complete repos.
- 11 clean-pass to degraded-fail cases.
- 11 regression-damage rows.
- Manual audit scope: 79 paired comparisons, or 158 individual clean/degraded runs.

Corrected token totals use `input_tokens + output_tokens`. Cached input tokens are not added.
