# Oracle Comparison: pytest-dev__pytest-7432

- Harness: `codex-cli`
- Condition: `comments_docstrings`
- Replication: `rep_2`

## Clean
- Task success: `True`
- FAIL_TO_PASS failures: `0`
- PASS_TO_PASS failures: `0`
- Files opened before first edit: `3`
- Exploration efficiency: `1.0`

## Degraded
- Task success: `True`
- FAIL_TO_PASS failures: `0`
- PASS_TO_PASS failures: `0`
- Files opened before first edit: `3`
- Exploration efficiency: `0.6667`

## Delta
- Target success changed: `False`
- FAIL_TO_PASS failure delta: `0`
- PASS_TO_PASS failure delta: `0`
- Files-opened delta: `0`
- Exploration-efficiency delta: `-0.33330000000000004`

## Notes
- Official SWE-bench oracle replay used the task test patch and official target split.
- The oracle command for this task was pytest -rA testing/test_skipping.py.
- Agent bootstrap metrics are parsed from Codex JSONL logs using the pre-first-edit command trace.
- Rep 2 used the same task, prompt contract, and degradation targets as rep 1.
