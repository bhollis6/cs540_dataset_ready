# Oracle Comparison: pallets__flask-5014

- Harness: `codex-cli`
- Condition: `remove_tests`
- Replication: `rep_1`

## Clean
- Task success: `True`
- FAIL_TO_PASS failures: `0`
- PASS_TO_PASS failures: `0`
- Files opened before first edit: `2`
- Exploration efficiency: `1.0`

## Degraded
- Task success: `True`
- FAIL_TO_PASS failures: `0`
- PASS_TO_PASS failures: `0`
- Files opened before first edit: `4`
- Exploration efficiency: `0.25`

## Delta
- Target success changed: `False`
- FAIL_TO_PASS failure delta: `0`
- PASS_TO_PASS failure delta: `0`
- Files-opened delta: `2`
- Exploration-efficiency delta: `-0.75`

## Notes
- Visible validation rerun: clean returned 0 on tests/test_blueprints.py.
- Visible validation rerun: degraded returned 0 on tests/test_basic.py -k blueprint_name_must_not_be_empty.
- remove_tests deleted tests/test_blueprints.py before the degraded Codex run, and the agent relocated its regression to tests/test_basic.py.
- The degraded run saw unrelated pre-existing session-cookie failures when it tried the full tests/test_basic.py module, so the visible rerun uses the targeted relocated regression slice instead.
