# Second Task Selection

## Current Readout

- `psf__requests-2317` was useful as a second-task harness trial, but it is not the right oracle-backed task-two choice.
- why:
  - clean and `comments_docstrings` both completed on `rep_2`
  - both used the corrected workspace-local pytest path
  - both passed focused visible validation
  - but the official SWE-bench oracle command is `pytest -rA test_requests.py`, and the first host-local oracle replay hung for several minutes on the clean condition
- interpretation:
  - Requests remains a good visible-run regression for the harness
  - Requests is currently a poor fit for the oracle-backed matrix because the official replay is too dependent on a large live-network-heavy suite

## Selection Rule Update

- task-two selection now needs one more criterion beyond runtime compatibility:
  - the official SWE-bench oracle must be bounded and trustworthy in this environment
- practical rule:
  - prefer Python `3.9+`
  - compact source/test surface
  - file-scoped pytest oracle
  - no known live-network dependence in the official command
  - still meaningful for `comments_docstrings`

## Astropy Outcome

- `astropy__astropy-14539` looked good on paper for task two, but it is blocked in practice on this host
- what failed:
  - the historical editable install gets deep into compiled extension builds
  - the build then fails under `/usr/bin/cc` during the Astropy extension stack
- implication:
  - Astropy remains a valid benchmark candidate in principle
  - Astropy is not the right immediate task-two choice for the host-local pilot lane

## Selected Task

- choose `scikit-learn__scikit-learn-26194` as the oracle-backed second task
- chosen first condition: `comments_docstrings`
- why this one:
  - Python `3.9` in the official spec, so it is runnable in the current host environment
  - one changed source file and one changed test file keep the run easy to interpret
  - the official oracle is a bounded file-scoped command:
    - `pytest -rA sklearn/metrics/tests/test_ranking.py`
  - the changed source diff is directly inside the `roc_curve` docstring and nearby explanatory notes, so `comments_docstrings` removes real guidance instead of becoming a near-no-op
  - the upstream repo script is simpler than Astropy's host-blocked compiled editable path:
    - `python -m pip install -v --no-use-pep517 --no-build-isolation -e .`

## Replacement Shortlist

- blocked candidate: `astropy__astropy-14539`
  - bounded oracle and good degradation fit
  - blocked by host-local editable build failure in compiled extensions
- selected task: `scikit-learn__scikit-learn-26194`
  - one source file, one test file
  - Python `3.9`
  - official command: `pytest -rA sklearn/metrics/tests/test_ranking.py`
  - `2` FAIL_TO_PASS, `186` PASS_TO_PASS
- safe fallback if cross-repo widening stalls: `pytest-dev__pytest-7205`
  - one source file, one test file
  - official command: `pytest -rA testing/test_setuponly.py`
  - `10` FAIL_TO_PASS, `16` PASS_TO_PASS

## Evidence

- machine-readable shortlist:
  - `src/profiles/second_task_candidates.json`
- machine-readable selection profile:
  - `src/profiles/scikit-learn__scikit-learn-26194_eligibility.json`
- blocked Astropy profile:
  - `src/profiles/astropy__astropy-14539_eligibility.json`
- Requests trial eligibility record:
  - `src/profiles/psf__requests-2317_eligibility.json`
- Requests trial artifacts:
  - `dev/active/bootstrap-2026-04-22/requests_rep_2_run_spec.json`
  - `dev/active/bootstrap-2026-04-22/requests_rep_2_materialization.json`
  - `runs/psf__requests-2317/codex-cli/clean/rep_2/logs/last_message.md`
  - `runs/psf__requests-2317/codex-cli/comments_docstrings/rep_2/logs/last_message.md`

## Next Step

- materialize the first clean-vs-`comments_docstrings` scikit-learn pair
- prepare workspace-local Python envs
- run clean and degraded Codex passes
- replay the official oracle and emit the first task-two comparison artifact
