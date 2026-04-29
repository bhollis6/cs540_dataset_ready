# Bootstrap Decisions

## Locked For First Pass

- SWE-bench consumption: `pypi_dependency`
- first pilot degradation: `comments_docstrings`
- second pilot degradation: `remove_tests`
- first pilot task: `pytest-dev__pytest-7432`
- second pilot task: `scikit-learn__scikit-learn-26194`
- first harness: `codex-cli`
- first materialization mode: `host_local_checkout`

## Why

- dependency-first keeps the pivot small and upstream-aligned
- comments/docstrings is the smallest fair non-test-removal degradation we can implement now
- remove-tests is the smallest next widening step because the eligibility record already marks it `GO` and the harness only needs file deletion rather than a new rewrite subsystem
- the pytest task gives a compact source/test surface and is easier to reason about than a large Django first pass
- the final second-task choice is scikit-learn rather than Astropy because Astropy exposed a real host-local editable build blocker after env prep
- scikit-learn keeps the compact one-source/one-test surface, runs on Python 3.9, preserves a bounded file-scoped oracle, and has an especially strong comments_docstrings fit in the touched roc_curve documentation
- Codex remains the first-class harness by project requirement
- Docker is not available in the current environment, so the first real workspace path uses a host-local checkout derived from the official SWE-bench task metadata

## Immediate Follow-On

1. install/pin the upstream SWE-bench dependency in the pilot environment
2. fetch the official Verified row for `pytest-dev__pytest-7432`
3. materialize clean workspace
4. materialize degraded workspace with `comments_docstrings`
5. run Codex on clean and degraded
6. score with oracle replay
7. emit the first comparison packet

## Current State

- dependency installed and pinned
- official task snapshot written
- clean workspace materialized
- degraded workspace materialized
- run prompt and metadata files written
- Codex exec wrapper implemented
