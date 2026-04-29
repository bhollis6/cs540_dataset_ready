# Agent Brief

You are working in the SWE-bench pivot workspace.

## Mission

Make the smallest useful path for the main experiment:

- one SWE-bench Verified task
- one eligible degradation
- one Codex run
- one scored clean-vs-degraded comparison

## Priorities

1. keep the workspace small
2. do not rebuild custom PR mining
3. define or implement only what is needed for the pilot
4. reuse the current `LLM-J` ideas selectively
5. read from the main `LLM-J` tree when useful, but do **not** write outside `swebench_backend/` in this lane

## Immediate Decisions To Make

1. how SWE-bench will be consumed
2. machine-readable task eligibility schema
3. first pilot task choice
4. first degradation to support

## Good Early Output

At the end of the first implementation pass, there should be:
- a task chosen
- a clear eligibility decision
- a clean workspace and one degraded workspace
- a Codex run path
- one output artifact comparing conditions

## Optional Narrow Research

If more external context is needed, keep it tightly scoped to the brief in:

- [docs/research_brief.md](<LOCAL_SWEBENCH_RUN_ROOT>/docs/research_brief.md:1)
