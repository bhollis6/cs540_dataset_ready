# Remove-Tests Stability: `pytest-dev__pytest-7432`

- Condition: `remove_tests`
- Replications: `rep_3`, `rep_4`
- Oracle success consistent: `True`
- Clean changed files consistent: `True`
- Degraded changed files consistent: `True`

## Changed-File Pattern

- clean:
  - `src/_pytest/skipping.py`
  - `testing/test_skipping.py`
- degraded:
  - `src/_pytest/skipping.py`
  - `testing/test_skipping.py`
  - `testing/test_terminal.py`

## Exploration Efficiency

- clean:
  - `rep_3 = 0.6667`
  - `rep_4 = 0.6667`
- degraded:
  - `rep_3 = 1.0`
  - `rep_4 = 0.6667`

## Readout

- `remove_tests` is now stable on oracle success.
- `remove_tests` is also stable on the changed-file strategy split between clean and degraded.
- `remove_tests` is not yet stable on efficiency direction, so the right conclusion is strategy-shift evidence rather than a repeatable efficiency gain or loss.
