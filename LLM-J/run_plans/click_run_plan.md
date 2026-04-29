# Run Plan: pallets/click

## Status
- Stage 5 status: `READY`
- Reason: Verified tasks and repo packet are ready for Stage 5 run scheduling.
- Packet decision: `GO`

## Summary
- Verified tasks: 6
- Conditions per task: 5
- Harnesses: 1
- Replications: 1
- Planned runs: 30

## Harnesses
- `codex_cli` (codex-cli): Frontier Codex agent runs using the user's subscription access.

## Conditions
- `clean`
- `type_hints`
- `naming`
- `comments_docstrings`
- `remove_tests`

## Layout
- Root template: `runs/{repo_short}/{candidate_id}/{harness_id}/{condition}/rep_{replication}/`
- `metadata` -> `metadata.json`
- `task_prompt` -> `issue_prompt.md`
- `workspace` -> `workspace/`
- `logs` -> `logs/`
- `result` -> `result.json`
- `metrics` -> `metrics.json`
