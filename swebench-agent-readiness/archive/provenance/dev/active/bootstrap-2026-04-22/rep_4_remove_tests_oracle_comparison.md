# Oracle Comparison: pytest-dev__pytest-7432

- Harness: `codex-cli`
- Condition: `remove_tests`
- Replication: `rep_4`

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
- Files opened before first edit: `3`
- Exploration efficiency: `0.6667`

## Delta
- Target success changed: `False`
- FAIL_TO_PASS failure delta: `0`
- PASS_TO_PASS failure delta: `0`
- Files-opened delta: `0`
- Exploration-efficiency delta: `0.0`

## Notes
- remove_tests deleted testing/test_skipping.py from the degraded workspace before the Codex run.
- Rep 4 again split the regression surface: clean used testing/test_skipping.py while degraded used testing/test_terminal.py.
