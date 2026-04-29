# Oracle Comparison: pytest-dev__pytest-7432

- Harness: `codex-cli`
- Condition: `naming`
- Replication: `rep_6`

## Clean
- Task success: `True`
- FAIL_TO_PASS failures: `0`
- PASS_TO_PASS failures: `0`
- Files opened before first edit: `4`
- Exploration efficiency: `0.5`

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
- Files-opened delta: `-2`
- Exploration-efficiency delta: `0.5`

## Notes
- Fourth degradation family on the first pytest task; identifier names were scope-locally obfuscated in the target source/test files before the degraded run.
- Official oracle replay used the existing workspace-local Python 3.9 environment.
