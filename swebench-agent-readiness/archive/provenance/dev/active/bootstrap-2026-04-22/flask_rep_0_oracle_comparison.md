# Oracle Comparison: pallets__flask-5014

- Harness: `codex-cli`
- Condition: `comments_docstrings`
- Replication: `rep_0`

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
- Visible validation rerun: clean returned 0 on tests/test_blueprints.py.
- Visible validation rerun: degraded returned 0 on tests/test_blueprints.py.
- Clean added both constructor-time and registration-time empty-name guards, while degraded only added the constructor-time guard.
