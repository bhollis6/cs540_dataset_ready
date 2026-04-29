# Third Task Selection

## Goal

- reach a third oracle-backed repo result quickly enough to support a same-day initial RQ1 shareout

## Selected Task

- choose `pallets__flask-5014`
- repo: `pallets/flask`
- chosen first condition: `comments_docstrings`

## Why This Task

- Python `3.11` in the official spec, so it avoids the older-interpreter blocker that ruled out Django and one older scikit-learn task
- one changed source file and one changed test file keep the task surface tight:
  - `src/flask/blueprints.py`
  - `tests/test_blueprints.py`
- the official oracle is bounded and shareable:
  - `pytest -rA tests/test_blueprints.py`
- the oracle still has enough regression depth for a pilot readout:
  - `1` FAIL_TO_PASS
  - `59` PASS_TO_PASS
- compared with the scientific-stack alternatives, Flask is the fastest credible host-local bring-up for a third repo today

## Condition Fit

- `comments_docstrings`
  - `GO`
  - the exact patch is short, but the touched Blueprint file is documentation-rich overall, so stripping comments/docstrings still removes meaningful local guidance
- `remove_tests`
  - `GO`
  - the changed blueprint test file contains the direct empty-name regression while the official oracle still replays the bounded blueprint suite

## Why Not Other Repo-Three Options First

- `astropy`
  - still blocked in this host-local lane by historical editable compiled-extension builds
- `requests`
  - visible-run capable, but the official oracle path remains too heavy and unreliable for the benchmark-backed lane
- `pylint`
  - plausible, but Flask has the cleaner lightweight-env path and stronger balanced PASS_TO_PASS coverage for today

## Immediate Next Step

- materialize the first clean-vs-`comments_docstrings` Flask pair
- prepare the workspace-local envs
- run clean and degraded Codex
- replay the official oracle
- if the Flask path stays light, run `remove_tests` next on the same task
