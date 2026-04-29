# Oracle Comparison: scikit-learn__scikit-learn-26194

- Harness: `codex-cli`
- Condition: `remove_tests`
- Replication: `rep_2`

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
- Files opened before first edit: `4`
- Exploration efficiency: `0.5`

## Delta
- Target success changed: `False`
- FAIL_TO_PASS failure delta: `0`
- PASS_TO_PASS failure delta: `0`
- Files-opened delta: `0`
- Exploration-efficiency delta: `0.0`

## Notes
- Visible validation: clean full sklearn/metrics/tests/test_ranking.py had 203 passed and 2 failed because the agent did not update every stale visible assertion/import in that file.
- Visible validation: degraded passed the relocated regression slice in sklearn/metrics/tests/test_common.py and the nearby ROC display slice in sklearn/metrics/_plot/tests/test_roc_curve_display.py.
- Degraded remove-tests behavior deleted sklearn/metrics/tests/test_ranking.py from the workspace and relocated visible regression coverage to sklearn/metrics/tests/test_common.py.
