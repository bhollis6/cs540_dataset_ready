# Run Plan: copier-org/copier

## Status
- Stage 5 status: `REVIEW_REQUIRED`
- Reason: Repo packet still needs guided human approval: Repo has useful artifacts, but still needs guided human review before Stage 4/Stage 5.
- Packet decision: `REVIEW`

## Summary
- Verified tasks: 7
- Conditions per task: 5
- Harnesses: 1
- Replications: 1
- Planned runs: 35

## Harnesses
- `codex_cli` (codex-cli): Frontier Codex agent runs using the user's subscription access.

## Conditions
- `clean`
- `type_hints`
- `naming`
- `comments_docstrings`
- `remove_tests`

## Warnings
- Packet decision is REVIEW; human approval should happen before live runs.

## Layout
- Root template: `runs/{repo_short}/{candidate_id}/{harness_id}/{condition}/rep_{replication}/`
- `metadata` -> `metadata.json`
- `task_prompt` -> `issue_prompt.md`
- `workspace` -> `workspace/`
- `logs` -> `logs/`
- `result` -> `result.json`
- `metrics` -> `metrics.json`
