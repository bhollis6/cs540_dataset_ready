# Oracle Comparison: pytest-dev__pytest-7432

- Harness: `codex-cli`
- Condition: `type_hints`
- Replication: `rep_5`

## Clean
- Task success: `True`
- FAIL_TO_PASS failures: `0`
- PASS_TO_PASS failures: `0`
- Files opened before first edit: `3`
- Exploration efficiency: `0.6667`

## Degraded
- Task success: `True`
- FAIL_TO_PASS failures: `0`
- PASS_TO_PASS failures: `0`
- Files opened before first edit: `2`
- Exploration efficiency: `1.0`

## Delta
- Target success changed: `False`
- FAIL_TO_PASS failure delta: `0`
- PASS_TO_PASS failure delta: `0`
- Files-opened delta: `-1`
- Exploration-efficiency delta: `0.33330000000000004`

## Notes
- Third degradation cell on the first pytest task; type annotations were stripped from source/test target files before the degraded run.
- Official oracle replay used the existing workspace-local Python 3.9 environment.
