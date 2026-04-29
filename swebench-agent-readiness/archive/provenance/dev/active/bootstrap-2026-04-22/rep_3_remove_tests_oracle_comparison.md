# Oracle Comparison: pytest-dev__pytest-7432

- Harness: `codex-cli`
- Condition: `remove_tests`
- Replication: `rep_3`

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
- remove_tests deleted testing/test_skipping.py from the degraded workspace before the Codex run.
- The clean run added its regression in testing/test_skipping.py while the degraded run pivoted to testing/test_terminal.py.
