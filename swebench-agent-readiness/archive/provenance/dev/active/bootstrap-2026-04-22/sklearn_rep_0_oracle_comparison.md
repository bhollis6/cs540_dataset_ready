# Oracle Comparison: scikit-learn__scikit-learn-26194

- Harness: `codex-cli`
- Condition: `comments_docstrings`
- Replication: `rep_0`

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
- Visible validation rerun: clean passed sklearn/metrics/tests/test_ranking.py with 206 passed.
- Visible validation rerun: degraded passed sklearn/metrics/tests/test_ranking.py with 205 passed.
- Degraded run updated an existing threshold test instead of adding the clean regression test function, so visible collection count differs by one.
