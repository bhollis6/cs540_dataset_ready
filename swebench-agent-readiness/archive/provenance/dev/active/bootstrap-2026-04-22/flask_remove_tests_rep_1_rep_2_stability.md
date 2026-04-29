# Flask Remove-Tests Stability

## Scope

- task: `pallets__flask-5014`
- condition: `remove_tests`
- replications compared:
  - `rep_1`
  - `rep_2`

## Outcome Stability

- oracle success was stable:
  - clean passed in both replications
  - degraded passed in both replications
  - each side achieved `1/1` FAIL_TO_PASS and `59/59` PASS_TO_PASS
- clean changed-file strategy was stable:
  - `src/flask/blueprints.py`
  - `tests/test_blueprints.py`
- degraded changed-file strategy was stable at the file-set level:
  - `src/flask/blueprints.py`
  - `tests/test_basic.py`
  - `tests/test_blueprints.py`

## Behavioral Stability

- `rep_1`
  - clean: `files_opened=2`, `exploration_efficiency=1.0`, `total_tokens=344381`
  - degraded: `files_opened=4`, `exploration_efficiency=0.25`, `total_tokens=599656`
  - delta: `files_opened=+2`, `exploration_efficiency=-0.75`, `total_tokens=+255275`
- `rep_2`
  - clean: `files_opened=2`, `exploration_efficiency=1.0`, `total_tokens=536631`
  - degraded: `files_opened=3`, `exploration_efficiency=0.6667`, `total_tokens=564830`
  - delta: `files_opened=+1`, `exploration_efficiency=-0.3333`, `total_tokens=+28199`

## Interpretation

- the strong `rep_1` exploration penalty replicated directionally in `rep_2`
- the magnitude was not stable: `rep_2` was a milder penalty
- the more stable signal is that deleting `tests/test_blueprints.py` redirects the degraded run toward `tests/test_basic.py` while preserving oracle success
- this supports the current RQ1 read: degradation effects are behavioral and task/condition dependent, not a uniform solve-rate collapse
