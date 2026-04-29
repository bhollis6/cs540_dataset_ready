# Run Plan: python-attrs/cattrs

## Status
- Stage 5 status: `READY`
- Reason: Verified tasks and repo packet are ready for Stage 5 run scheduling.
- Packet decision: `GO`

## Summary
- Verified tasks: 3
- Conditions per task: 5
- Harnesses: 2
- Replications: 3
- Planned runs: 90

## Harnesses
- `claude_code` (claude-code): Frontier Claude agent runs using the user's Max subscription.
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
