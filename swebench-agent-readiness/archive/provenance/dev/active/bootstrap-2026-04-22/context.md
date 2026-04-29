# Session Context

This workspace is the new parallel experiment path.

It exists because:
- the current `LLM-J` path is producing meaningful results
- but custom historical environment work is expensive
- SWE-bench can likely provide a better main task substrate for the paper

This pivot should remain focused on:
- SWE-bench task selection for this study
- degradation application
- harness execution
- analysis

It should not turn into a second copy of the full custom-repo pipeline.

## Current Bootstrap State

- SWE-bench integration is now decided as `pypi_dependency`
- the first pilot condition is `comments_docstrings`
- the first pilot task is `pytest-dev__pytest-7432`
- the first materialization mode is `host_local_checkout`

## Implemented Contracts

- `schemas/task_eligibility.schema.json`
- `src/filters/eligibility.py`
- `src/degradation/comments_docstrings.py`
- `src/substrate/swebench_verified.py`
- `src/harness/pilot_run.py`
- `src/harness/materialize.py`
- `src/harness/codex_exec.py`
- `src/harness/oracle_replay.py`
- `src/analysis/comparison_packet.py`
- `src/analysis/oracle_packet.py`

## Oracle Replay Outcome

- rep_1 now has a real oracle-backed comparison packet:
  - `dev/active/bootstrap-2026-04-22/rep_1_oracle_comparison.json`
  - `dev/active/bootstrap-2026-04-22/rep_1_oracle_comparison.md`
- both clean and `comments_docstrings` conditions passed the official target split for `pytest-dev__pytest-7432`:
  - `1 / 1` FAIL_TO_PASS passed
  - `77 / 77` PASS_TO_PASS passed
- host-local oracle replay currently runs in place against the prepared workspace env when `.pilot-venv-py39` already exists:
  - snapshot the official test files
  - reset them to `base_commit`
  - apply the official `test_patch`
  - run the official task command
  - restore the pre-oracle file contents afterward

## Rep 1 Bootstrap Metrics

- clean rep_1 opened exactly the task-relevant files before the first edit:
  - `src/_pytest/skipping.py`
  - `testing/test_skipping.py`
  - `testing/test_terminal.py`
  - exploration efficiency: `1.0`
- degraded rep_1 opened one extra dead-end file before the first edit:
  - relevant: `src/_pytest/skipping.py`, `testing/test_skipping.py`
  - dead-end: `src/_pytest/runner.py`
  - exploration efficiency: `0.6667`
- token totals from the Codex JSONL logs were also captured:
  - clean: `1,161,445`
  - degraded: `1,316,933`

## Rep 2 Outcome

- rep_2 now has matching visible and oracle-backed artifacts:
  - `dev/active/bootstrap-2026-04-22/rep_2_visible_comparison.json`
  - `dev/active/bootstrap-2026-04-22/rep_2_oracle_comparison.json`
- rep_2 again passed clean and `comments_docstrings` under the official task split:
  - clean: `1/1` FAIL_TO_PASS, `77/77` PASS_TO_PASS
  - degraded: `1/1` FAIL_TO_PASS, `77/77` PASS_TO_PASS
- rep_2 preserved the same changed-file pattern seen in rep_1:
  - clean: `src/_pytest/skipping.py`, `testing/test_terminal.py`
  - degraded: `src/_pytest/skipping.py`, `testing/test_skipping.py`
- rep_2 preserved the same exploration-efficiency gap seen in rep_1:
  - clean: `1.0`
  - degraded: `0.6667`
- rep_2 token totals were lower in absolute terms than rep_1, but the degraded run still used more tokens:
  - clean: `756,447`
  - degraded: `825,095`

## Replication Stability

- stability summary artifacts now exist:
  - `dev/active/bootstrap-2026-04-22/rep_1_rep_2_stability.json`
  - `dev/active/bootstrap-2026-04-22/rep_1_rep_2_stability.md`
- current stable pilot readout:
  - oracle success is consistent across `rep_1` and `rep_2`
  - clean changed files are consistent across `rep_1` and `rep_2`
  - degraded changed files are consistent across `rep_1` and `rep_2`
  - degraded exploration efficiency is lower than clean in both replications

## Next Degradation Decision

- the next pilot degradation is `remove_tests`
- rationale:
  - it is already marked `GO` in `src/profiles/first_pilot_eligibility.json`
  - it widens the matrix without introducing a new rewrite subsystem
  - it keeps the task fixed while strengthening the information-removal pressure
- harness status:
  - `src/harness/materialize.py` now deletes files listed under `delete_files`
  - `tests/test_materialize.py` and `tests/test_pilot_run.py` cover the `remove_tests` path

## Remove-Tests Rep 3 Outcome

- the first clean-vs-`remove_tests` run now has an oracle-backed packet:
  - `dev/active/bootstrap-2026-04-22/rep_3_remove_tests_oracle_comparison.json`
  - `dev/active/bootstrap-2026-04-22/rep_3_remove_tests_oracle_comparison.md`
- both clean and `remove_tests` again passed the official task split for `pytest-dev__pytest-7432`:
  - clean: `1/1` FAIL_TO_PASS, `77/77` PASS_TO_PASS
  - degraded: `1/1` FAIL_TO_PASS, `77/77` PASS_TO_PASS
- the condition changed the visible test strategy:
  - clean changed `src/_pytest/skipping.py` and `testing/test_skipping.py`
  - degraded changed `src/_pytest/skipping.py`, deleted `testing/test_skipping.py`, and added its regression in `testing/test_terminal.py`
- unlike `comments_docstrings`, this degradation improved early exploration efficiency on this replication:
  - clean opened `3` files before first edit with efficiency `0.6667`
  - degraded opened `2` files before first edit with efficiency `1.0`
  - clean token total: `860,647`
  - degraded token total: `434,730`
- visible validation used the surviving surfaces:
  - clean passed the focused `testing/test_skipping.py` slice plus `testing/test_terminal.py -k summary_s_alias`
  - degraded passed `testing/test_terminal.py -k summary_s_alias`

## Remove-Tests Rep 4 Outcome

- the second clean-vs-`remove_tests` run now has an oracle-backed packet:
  - `dev/active/bootstrap-2026-04-22/rep_4_remove_tests_oracle_comparison.json`
  - `dev/active/bootstrap-2026-04-22/rep_4_remove_tests_oracle_comparison.md`
- rep_4 again passed clean and `remove_tests` under the official task split:
  - clean: `1/1` FAIL_TO_PASS, `77/77` PASS_TO_PASS
  - degraded: `1/1` FAIL_TO_PASS, `77/77` PASS_TO_PASS
- rep_4 preserved the same changed-file strategy split seen in rep_3:
  - clean: `src/_pytest/skipping.py`, `testing/test_skipping.py`
  - degraded: `src/_pytest/skipping.py`, `testing/test_skipping.py`, `testing/test_terminal.py`
- rep_4 did not preserve the rep_3 exploration-efficiency advantage for degraded:
  - clean: `0.6667`
  - degraded: `0.6667`
  - degraded opened one dead-end file before first edit: `testing/test_reports.py`

## Remove-Tests Stability

- remove-tests stability summary artifacts now exist:
  - `dev/active/bootstrap-2026-04-22/rep_3_rep_4_remove_tests_stability.json`
  - `dev/active/bootstrap-2026-04-22/rep_3_rep_4_remove_tests_stability.md`
- current stable readout for `remove_tests`:
  - oracle success is consistent across `rep_3` and `rep_4`
  - clean changed files are consistent across `rep_3` and `rep_4`
  - degraded changed files are consistent across `rep_3` and `rep_4`
  - efficiency direction is not consistent across `rep_3` and `rep_4`
  - the stable signal is a changed test-surface strategy, not a stable efficiency gain or loss

## Requests Trial Outcome

- `psf__requests-2317` is now a useful harness-validation task, not the chosen oracle-backed second task
- what succeeded:
  - a clean `rep_2` run completed under the corrected prompt/env contract
  - a degraded `comments_docstrings` `rep_2` run also completed
  - both runs used `./.pilot-venv-py39/bin/python -m pytest ...` instead of falling back to the wrong interpreter
  - clean visible validation passed on a focused bytes-method slice
  - degraded visible validation passed on its focused bytes-method slice
- what blocked it:
  - the official SWE-bench oracle command is `pytest -rA test_requests.py`
  - the host-local oracle replay for the clean condition hung for several minutes
  - this makes Requests a poor fit for the oracle-backed matrix even though the visible-run path is real

## Second Task Rule Update

- second-task selection now requires:
  - runnable Python version
  - compact source/test surface
  - meaningful degradation fit
  - trustworthy oracle replay in the current environment
- practical implication:
  - prefer file-scoped pytest commands without known live-network dependence

## Replacement Shortlist

- provisional front-runner: `astropy__astropy-14539`
  - Python `3.9`
  - one source file, one test file
  - oracle command: `pytest -rA astropy/io/fits/tests/test_diff.py`
  - `2` FAIL_TO_PASS, `46` PASS_TO_PASS
- strong alternative: `scikit-learn__scikit-learn-26194`
  - Python `3.9`
  - one source file, one test file
  - oracle command: `pytest -rA sklearn/metrics/tests/test_ranking.py`
  - `2` FAIL_TO_PASS, `186` PASS_TO_PASS
- safe fallback if cross-repo widening stalls again: `pytest-dev__pytest-7205`
  - Python `3.9`
  - one source file, one test file
  - oracle command: `pytest -rA testing/test_setuponly.py`

## Second Task Decision

- selected task: `scikit-learn__scikit-learn-26194`
- chosen first condition: `comments_docstrings`
- why scikit-learn won:
  - bounded file-scoped oracle: `pytest -rA sklearn/metrics/tests/test_ranking.py`
  - Python `3.9` in the official env spec
  - one-source/one-test surface remains easy to interpret
  - the touched `roc_curve` source diff is inside the function docstring and nearby explanatory notes, so `comments_docstrings` removes meaningful local guidance

## Astropy Blocker

- `astropy__astropy-14539` remains a credible benchmark candidate in principle
- in this host-local lane it is currently blocked by the historical editable install:
  - env prep now correctly handles local editable installs, seeded `pip`, local clone materialization, and repo-setup commands
  - even with those fixes, the historical Astropy checkout still fails during compiled extension build under `/usr/bin/cc`
- practical consequence:
  - stop deepening on Astropy for now
  - switch task two to scikit-learn instead of spending more pilot budget on host-specific build triage

## Second Task Artifacts

- selection note:
  - `dev/active/bootstrap-2026-04-22/second_task_selection.md`
- machine-readable shortlist:
  - `src/profiles/second_task_candidates.json`
- Requests trial eligibility:
  - `src/profiles/psf__requests-2317_eligibility.json`
- Requests trial run artifacts:
  - `dev/active/bootstrap-2026-04-22/requests_rep_2_run_spec.json`
  - `dev/active/bootstrap-2026-04-22/requests_rep_2_materialization.json`
  - `dev/active/bootstrap-2026-04-22/requests_rep_2_clean_workspace_env_py39.json`
  - `dev/active/bootstrap-2026-04-22/requests_rep_2_degraded_workspace_env_py39.json`
- blocked-candidate inspection:
  - `runs/django__django-11728/inspection/clean`

## Remaining Work

- widen the scikit-learn matrix beyond the first `comments_docstrings` replication
- decide whether the next breadth point should be a second scikit-learn replication or `remove_tests`
- keep the current task-selection rule focused on trustworthy host-local oracle replay
- keep the in-place oracle replay path unless a concrete validity issue appears

## Matplotlib Screening and First Cell 2026-04-28

- selected `matplotlib/matplotlib` as the next breadth candidate because the remaining Verified repo pool is narrow after the six-repo checkpoint; `matplotlib` has enough compact file-scoped tasks, while sklearn/astropy remain known build-cost risks and PyLint previously had only two clean gold-preflight tasks
- added a narrow host-local env safeguard in `src/harness/python_env.py`: when the official eval command invokes `pytest` but extracted setup lines omit pytest, install `pytest` explicitly
  - this fixed false-negative gold preflights where matplotlib replay failed immediately with `No module named pytest`
  - focused verification: `PYTHONPATH=. uv run --extra dev pytest tests/test_python_env.py tests/test_oracle_replay.py tests/test_pilot_run.py` passed with `20 passed`
- accepted matplotlib task set after gold preflight:
  - `matplotlib__matplotlib-20676`: `2/2` FAIL_TO_PASS and `32/32` PASS_TO_PASS under gold replay; strong naming/comments/remove-tests surface, `0` annotation nodes
  - `matplotlib__matplotlib-23412`: `1/1` FAIL_TO_PASS and `46/46` PASS_TO_PASS under gold replay; strong naming/comments/remove-tests surface, `0` annotation nodes
  - `matplotlib__matplotlib-26291`: `1/1` FAIL_TO_PASS and `49/49` PASS_TO_PASS under gold replay; strong naming/comments/remove-tests surface, `0` annotation nodes
- executed `matplotlib__matplotlib-20676` x `naming` x `rep_0`
  - clean and degraded both failed target tests: FAIL_TO_PASS failures stayed `2 -> 2`
  - degraded introduced broad regression damage: PASS_TO_PASS failures moved `0 -> 32`
  - files opened before first edit stayed `2 -> 2`; exploration efficiency stayed `1.0 -> 1.0`
  - corrected total tokens moved `745818 -> 1172686`
  - changed files moved `2 -> 22`
  - current read: not a clean-success transition because the clean run missed the target, but it is a high-signal naming regression-damage and patch-breadth cell
- executed `matplotlib__matplotlib-20676` x `comments_docstrings` x `rep_2`
  - clean and degraded both failed target tests: FAIL_TO_PASS failures stayed `2 -> 2`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `3 -> 2`; exploration efficiency moved `0.6667 -> 1.0`
  - corrected total tokens moved `681943 -> 1793861`
  - changed files moved `2 -> 10`
  - current read: comments/docstrings did not add official outcome damage on this baseline-hard task, but it produced a large degraded token and execution-validation increase
- executed `matplotlib__matplotlib-20676` x `remove_tests` x `rep_3`
  - clean and degraded both failed target tests: FAIL_TO_PASS failures stayed `2 -> 2`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `5 -> 2`; exploration efficiency moved `0.4 -> 0.5`
  - corrected total tokens moved `891100 -> 577719`
  - changed files moved `2 -> 10`
  - current read: remove-tests did not add official outcome damage and was cheaper/more direct here, while visible validation shifted to a surviving `test_spanselector.py` path
- executed `matplotlib__matplotlib-20676` x `type_hints` x `rep_1`
  - clean and degraded both failed target tests: FAIL_TO_PASS failures stayed `2 -> 2`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit stayed `4 -> 4`; exploration efficiency stayed `0.5 -> 0.5`
  - corrected total tokens moved `778935 -> 632267`
  - changed files moved `2 -> 10`
  - current read: low-signal type-hints cell as expected because the scoped surface has `0` annotation nodes; included to complete the first matplotlib task across all four degradations
- executed `matplotlib__matplotlib-23412` x `naming` x `rep_0`
  - clean passed official SWE-bench tests; degraded failed official SWE-bench tests
  - FAIL_TO_PASS failures moved `0 -> 1`
  - PASS_TO_PASS failures moved `0 -> 21`
  - files opened before first edit moved `9 -> 7`; exploration efficiency moved `0.2222 -> 0.2857`
  - corrected total tokens moved `858611 -> 2160998`
  - changed files moved `2 -> 36`
  - current read: ninth clean-success to degraded-failure transition overall and first matplotlib transition; naming damage now crosses xarray, Sympy, Requests, and matplotlib

## Proper RQ1 Snapshot Direction

- the stricter target is now recorded in `docs/rq1_proper_snapshot_plan_2026-04-23.md`
- the proper matrix target is `3` repos x at least `3` SWE-bench Verified tasks / PRs per repo x all `4` degradation families
- Flask remains useful pilot/supporting evidence, but it cannot satisfy the proper matrix because the current SWE-bench Verified dataset exposes only one compact Flask task
- the proper repo set is now:
  - `pytest-dev/pytest`
  - `scikit-learn/scikit-learn`
  - `sphinx-doc/sphinx`
- Sphinx is the replacement third repo because it has multiple compact Verified tasks with meaningful type-hint, naming, comment/docstring, and test surfaces
- Sphinx host-local oracle compatibility changes are now implemented:
  - `tox --current-env ... -- tests/...` is normalized to direct workspace-venv pytest execution
  - `setuptools==70.0.0` is inserted when no explicit setuptools pin exists, preserving historical `pkg_resources` imports under modern uv seeds
- Sphinx gold preflight status:
  - `sphinx-doc__sphinx-9367` passed after compatibility pinning: `1/1` FAIL_TO_PASS and `25/25` PASS_TO_PASS
  - `sphinx-doc__sphinx-10323` is rejected for now because host-local gold replay produced two PASS_TO_PASS failures
- pytest proper-matrix task selection is now complete:
  - `pytest-dev__pytest-7432`
  - `pytest-dev__pytest-10081`
  - `pytest-dev__pytest-10356`
- added pytest task gold preflight:
  - `pytest-dev__pytest-10081`: `1/1` FAIL_TO_PASS and `63/63` PASS_TO_PASS
  - `pytest-dev__pytest-10356`: `1/1` FAIL_TO_PASS and `79/79` PASS_TO_PASS
- added pytest eligibility profiles:
  - `src/profiles/pytest-dev__pytest-10081_eligibility.json`
  - `src/profiles/pytest-dev__pytest-10356_eligibility.json`
- scikit-learn proper-matrix task selection is now complete:
  - `scikit-learn__scikit-learn-26194`
  - `scikit-learn__scikit-learn-25232`
  - `scikit-learn__scikit-learn-25931`
- added scikit-learn task gold preflight:
  - `scikit-learn__scikit-learn-25232`: `1/1` FAIL_TO_PASS and `214/214` PASS_TO_PASS
  - `scikit-learn__scikit-learn-25931`: `1/1` FAIL_TO_PASS and `21/21` PASS_TO_PASS
- added scikit-learn eligibility profiles:
  - `src/profiles/scikit-learn__scikit-learn-25232_eligibility.json`
  - `src/profiles/scikit-learn__scikit-learn-25931_eligibility.json`
- Sphinx proper-matrix task selection is now complete:
  - `sphinx-doc__sphinx-9367`
  - `sphinx-doc__sphinx-10449`
  - `sphinx-doc__sphinx-9673`
- added Sphinx task gold preflight:
  - `sphinx-doc__sphinx-10449`: `1/1` FAIL_TO_PASS and `30/30` PASS_TO_PASS
  - `sphinx-doc__sphinx-9673`: `1/1` FAIL_TO_PASS and `24/24` PASS_TO_PASS
- rejected or blocked Sphinx candidates:
  - `sphinx-doc__sphinx-10323`: two PASS_TO_PASS failures under host-local gold replay
  - `sphinx-doc__sphinx-10435`: failed the FAIL_TO_PASS target under gold replay
  - `sphinx-doc__sphinx-7757`, `sphinx-doc__sphinx-8265`, `sphinx-doc__sphinx-9281`: historical MarkupSafe resolver conflict before compatibility pin; kept as reserves, not selected
- `src/harness/python_env.py` now detects historical Sphinx checkouts with `markupsafe<=2.0.1` and installs `markupsafe==2.0.1` before editable workspace install
- added Sphinx eligibility profiles:
  - `src/profiles/sphinx-doc__sphinx-9367_eligibility.json`
  - `src/profiles/sphinx-doc__sphinx-10449_eligibility.json`
  - `src/profiles/sphinx-doc__sphinx-9673_eligibility.json`

## Type-Hints and Naming Degradation Status

- `src/degradation/type_hints.py` strips annotations conservatively with LibCST
- `src/degradation/naming.py` performs scope-limited identifier obfuscation with AST screening and Rope rename operations
- `src/harness/materialize.py` now supports `type_hints` and `naming`
- the local test suite covers both degradation paths and currently passes:
  - `PYTHONPATH=. uv run --extra dev pytest`
  - result: `35 passed, 1 warning`

## Pytest All-Four First Task Status

- `pytest-dev__pytest-7432` now has all four degradation families represented under official oracle replay:
  - `comments_docstrings` reps `1`, `2`
  - `remove_tests` reps `3`, `4`
  - `type_hints` rep `5`
  - `naming` rep `6`
- `type_hints` rep `5`:
  - clean and degraded both passed `1/1` FAIL_TO_PASS and `77/77` PASS_TO_PASS
  - exploration efficiency moved from `0.6667` clean to `1.0` degraded
  - degraded used `87683` fewer tokens
- `naming` rep `6`:
  - clean and degraded both passed `1/1` FAIL_TO_PASS and `77/77` PASS_TO_PASS
  - exploration efficiency moved from `0.5` clean to `1.0` degraded
  - degraded used `97284` more tokens
- aggregate RQ1 snapshot after these additions:
  - `12` oracle-backed clean-vs-degraded Codex replications
  - `3` repos and `3` tasks in the pilot evidence base
  - all `4` degradation families represented at least once
  - `0/12` target-success drops
  - `0/12` PASS_TO_PASS regression-damage deltas
  - exploration-efficiency deltas: `4` negative, `5` positive, `3` zero
  - degraded token use increased in `8/12` runs

## Scikit-Learn Artifacts

- task snapshot:
  - `dev/active/bootstrap-2026-04-22/second_task_candidate_scikit-learn__scikit-learn-26194_snapshot.json`
- run spec and materialization:
  - `dev/active/bootstrap-2026-04-22/sklearn_rep_0_run_spec.json`
  - `dev/active/bootstrap-2026-04-22/sklearn_rep_0_materialization.json`
- workspace env specs:
  - `dev/active/bootstrap-2026-04-22/sklearn_rep_0_clean_workspace_env_py39.json`
  - `dev/active/bootstrap-2026-04-22/sklearn_rep_0_degraded_workspace_env_py39.json`
- Codex exec specs:
  - `dev/active/bootstrap-2026-04-22/sklearn_rep_0_clean_codex_exec_spec.json`
  - `dev/active/bootstrap-2026-04-22/sklearn_rep_0_degraded_codex_exec_spec.json`
- oracle-backed comparison:
  - `dev/active/bootstrap-2026-04-22/sklearn_rep_0_oracle_comparison.json`
  - `dev/active/bootstrap-2026-04-22/sklearn_rep_0_oracle_comparison.md`

## Scikit-Learn Rep 0 Outcome

- `scikit-learn__scikit-learn-26194` is now a real oracle-backed second task, not just a shortlisted candidate
- both clean and `comments_docstrings` passed the official task split:
  - clean: `2/2` FAIL_TO_PASS, `186/186` PASS_TO_PASS
  - degraded: `2/2` FAIL_TO_PASS, `186/186` PASS_TO_PASS
- the semantic fix converged across conditions:
  - both runs changed the `roc_curve` threshold sentinel from a finite `thresholds[0] + 1` style prepend to `np.inf`
  - both runs updated `sklearn/metrics/_ranking.py` and `sklearn/metrics/tests/test_ranking.py`
- degraded also touched a nearby docs example:
  - `doc/modules/model_evaluation.rst`
- visible validation succeeded in both workspaces:
  - clean rerun: `206 passed`
  - degraded rerun: `205 passed`
  - the degraded run updated an existing threshold test rather than adding the clean regression-test function, so the visible collection count differs by one
- the first sklearn efficiency signal points in the opposite direction from task one:
  - clean opened `3` files before the first edit with exploration efficiency `0.6667`
  - degraded opened `2` files before the first edit with exploration efficiency `1.0`
- practical meaning:
  - the pivot now has a real `2-task x comments_docstrings` oracle-backed matrix
  - RQ1 is still not answered, but the remaining gap is experimental breadth, not whether the path works

## Scikit-Learn Rep 1 Outcome

- the second `comments_docstrings` replication is now oracle-backed:
  - `dev/active/bootstrap-2026-04-22/sklearn_rep_1_oracle_comparison.json`
  - `dev/active/bootstrap-2026-04-22/sklearn_rep_1_oracle_comparison.md`
- both clean and degraded again passed the official target split:
  - clean: `2/2` FAIL_TO_PASS, `186/186` PASS_TO_PASS
  - degraded: `2/2` FAIL_TO_PASS, `186/186` PASS_TO_PASS
- rep_1 converged more tightly than rep_0:
  - both sides changed `sklearn/metrics/_ranking.py` and `sklearn/metrics/tests/test_ranking.py`
  - neither side touched `doc/modules/model_evaluation.rst`
  - both sides opened exactly the same two files before first edit with exploration efficiency `1.0`
- visible validation succeeded in both workspaces:
  - clean rerun: `205 passed`
  - degraded rerun: `205 passed`
- practical meaning:
  - the sklearn `comments_docstrings` row is now less thin
  - task success still did not degrade
  - the early-search advantage for degraded seen in rep_0 did not replicate in rep_1

## Scikit-Learn Remove-Tests Bring-Up

## Scikit-Learn Remove-Tests Outcome

- scikit-learn now also has a real oracle-backed `remove_tests` comparison:
  - `dev/active/bootstrap-2026-04-22/sklearn_remove_tests_rep_2_oracle_comparison.json`
  - `dev/active/bootstrap-2026-04-22/sklearn_remove_tests_rep_2_oracle_comparison.md`
- setup details:
  - `dev/active/bootstrap-2026-04-22/sklearn_remove_tests_rep_2_run_spec.json`
  - `dev/active/bootstrap-2026-04-22/sklearn_remove_tests_rep_2_materialization.json`
  - `dev/active/bootstrap-2026-04-22/sklearn_remove_tests_rep_2_clean_workspace_env_py39.json`
  - `dev/active/bootstrap-2026-04-22/sklearn_remove_tests_rep_2_degraded_workspace_env_py39.json`
- both clean and degraded passed the official target split:
  - clean: `2/2` FAIL_TO_PASS, `186/186` PASS_TO_PASS
  - degraded: `2/2` FAIL_TO_PASS, `186/186` PASS_TO_PASS
- strategy shift:
  - clean changed `sklearn/metrics/_ranking.py` and `sklearn/metrics/tests/test_ranking.py`
  - degraded deleted `sklearn/metrics/tests/test_ranking.py` from the workspace and relocated visible regression coverage to `sklearn/metrics/tests/test_common.py`
- exploration and usage:
  - clean: `files_opened=4`, `exploration_efficiency=0.5`, `total_tokens=1861426`
  - degraded: `files_opened=4`, `exploration_efficiency=0.5`, `total_tokens=3729619`
- visible validation nuance:
  - clean full `sklearn/metrics/tests/test_ranking.py` still had `203 passed, 2 failed` because the agent did not update every stale visible assertion/import in that file
  - degraded passed the relocated `test_common.py` slice and a nearby ROC display slice
  - the official oracle passed on both sides, so the benchmark-backed comparison remains sound

## Third Repo Decision

- selected third oracle-backed repo: `pallets/flask`
- selected task: `pallets__flask-5014`
- why it won for today's milestone:
  - Python `3.11` in the official spec
  - bounded single-file oracle: `pytest -rA tests/test_blueprints.py`
  - one changed source file and one changed test file
  - materially lighter host-local env prep than the scientific-stack alternatives
- selection artifacts:
  - `src/profiles/pallets__flask-5014_eligibility.json`
  - `dev/active/bootstrap-2026-04-22/third_task_selection.md`
  - `dev/active/bootstrap-2026-04-22/third_task_candidate_pallets__flask-5014_snapshot.json`

## Flask Comments Outcome

- `pallets__flask-5014` now has a real oracle-backed `comments_docstrings` comparison:
  - `dev/active/bootstrap-2026-04-22/flask_rep_0_oracle_comparison.json`
  - `dev/active/bootstrap-2026-04-22/flask_rep_0_oracle_comparison.md`
- both clean and degraded passed the official target split:
  - clean: `1/1` FAIL_TO_PASS, `59/59` PASS_TO_PASS
  - degraded: `1/1` FAIL_TO_PASS, `59/59` PASS_TO_PASS
- changed-file behavior differed despite identical oracle success:
  - clean changed `src/flask/blueprints.py` and `tests/test_blueprints.py`
  - degraded changed the same two files but implemented the narrower constructor-only fix
  - clean also added a broader registration-time empty-name guard
- first-edit exploration signal:
  - clean: `files_opened=4`, `exploration_efficiency=0.5`
  - degraded: `files_opened=2`, `exploration_efficiency=1.0`

## Flask Remove-Tests Outcome

- Flask now also has a real oracle-backed `remove_tests` comparison:
  - `dev/active/bootstrap-2026-04-22/flask_remove_tests_rep_1_oracle_comparison.json`
  - `dev/active/bootstrap-2026-04-22/flask_remove_tests_rep_1_oracle_comparison.md`
- both clean and degraded again passed the official target split:
  - clean: `1/1` FAIL_TO_PASS, `59/59` PASS_TO_PASS
  - degraded: `1/1` FAIL_TO_PASS, `59/59` PASS_TO_PASS
- this condition produced the clearest strategy shift on Flask:
  - clean changed `src/flask/blueprints.py` and `tests/test_blueprints.py`
  - degraded ran without `tests/test_blueprints.py` in the workspace and relocated its regression to `tests/test_basic.py`
- remove-tests also produced the strongest exploration penalty seen so far:
  - clean: `files_opened=2`, `exploration_efficiency=1.0`
  - degraded: `files_opened=4`, `exploration_efficiency=0.25`
- visible validation nuance:
  - degraded saw unrelated pre-existing session-cookie failures when it tried the full `tests/test_basic.py` module
  - the targeted relocated regression slice still passed, and the official oracle passed

## Next Evidence Decision

- selected next evidence point: deepen existing cells rather than widen to a fourth repo
- chosen cell: `pallets__flask-5014` x `remove_tests` x `rep_2`
- rationale:
  - the first `3 repo x 2 condition` breadth slice is already complete
  - the strongest single behavioral shift in that slice was Flask `remove_tests`
  - a second replication directly tests whether that sharp interaction is stable
  - a fourth repo would add breadth before checking the most informative existing outlier

## Flask Remove-Tests Rep 2 Outcome

- the second Flask `remove_tests` replication is now oracle-backed:
  - `dev/active/bootstrap-2026-04-22/flask_remove_tests_rep_2_oracle_comparison.json`
  - `dev/active/bootstrap-2026-04-22/flask_remove_tests_rep_2_oracle_comparison.md`
- setup artifacts:
  - `dev/active/bootstrap-2026-04-22/flask_remove_tests_rep_2_run_spec.json`
  - `dev/active/bootstrap-2026-04-22/flask_remove_tests_rep_2_materialization.json`
  - `dev/active/bootstrap-2026-04-22/flask_remove_tests_rep_2_clean_workspace_env_py311.json`
  - `dev/active/bootstrap-2026-04-22/flask_remove_tests_rep_2_degraded_workspace_env_py311.json`
- both clean and degraded again passed the official target split:
  - clean: `1/1` FAIL_TO_PASS, `59/59` PASS_TO_PASS
  - degraded: `1/1` FAIL_TO_PASS, `59/59` PASS_TO_PASS
- changed-file behavior:
  - clean changed `src/flask/blueprints.py` and `tests/test_blueprints.py`
  - degraded changed `src/flask/blueprints.py`, added relocated visible coverage in `tests/test_basic.py`, and still carried the deleted `tests/test_blueprints.py` file in the final diff
- exploration signal:
  - clean: `files_opened=2`, `exploration_efficiency=1.0`, `total_tokens=536631`
  - degraded: `files_opened=3`, `exploration_efficiency=0.6667`, `total_tokens=564830`
  - delta: `files_opened=+1`, `exploration_efficiency=-0.3333`, `total_tokens=+28199`
- stability artifacts now exist:
  - `dev/active/bootstrap-2026-04-22/flask_remove_tests_rep_1_rep_2_stability.json`
  - `dev/active/bootstrap-2026-04-22/flask_remove_tests_rep_1_rep_2_stability.md`
- practical meaning:
  - the Flask `remove_tests` exploration penalty replicated directionally
  - the magnitude did not replicate exactly: `rep_2` was a milder penalty than `rep_1`
  - the stable signal is redirected test strategy plus preserved oracle success

## Initial RQ1 Snapshot

- presentation-ready snapshot:
  - `docs/rq1_snapshot_2026-04-23.md`
- aggregate metrics packet:
  - `dev/active/bootstrap-2026-04-22/rq1_snapshot_2026-04-23_metrics.json`
- headline:
  - across `12` oracle-backed clean-vs-degraded Codex replications, there are `0/12` target-success drops and `0/12` PASS_TO_PASS regression-damage deltas
  - degradation still changes behavior: exploration-efficiency deltas are mixed (`4` negative, `5` positive, `3` zero), and degraded token use increases in `8/12` runs
- current hypothesis:
  - the initial RQ1 story is behavioral sensitivity and condition-by-task interaction, not uniform solve-rate collapse
- most defensible presentation wording:
  - initial RQ1 evidence points to behavioral sensitivity, not solve-rate collapse

## Prompt Contract Fix

- `src/harness/materialize.py` now tells Codex to prefer `./.pilot-venv-*/bin/python -m pytest ...` rather than the stale hard-coded `.pilot-venv-py39` path
- `tests/test_materialize.py` covers the updated guidance
- this prevents future non-3.9 tasks from wasting time rediscovering the workspace interpreter

## Current Day-End Readout

- the oracle-backed matrix now spans three repos:
  - `pytest-dev/pytest`
  - `scikit-learn/scikit-learn`
  - `pallets/flask`
- completed oracle-backed cells:
  - `pytest-dev__pytest-7432` x `comments_docstrings` x `rep_1`
  - `pytest-dev__pytest-7432` x `comments_docstrings` x `rep_2`
  - `pytest-dev__pytest-7432` x `remove_tests` x `rep_3`
  - `pytest-dev__pytest-7432` x `remove_tests` x `rep_4`
  - `pytest-dev__pytest-7432` x `type_hints` x `rep_5`
  - `pytest-dev__pytest-7432` x `naming` x `rep_6`
  - `scikit-learn__scikit-learn-26194` x `comments_docstrings` x `rep_0`
  - `scikit-learn__scikit-learn-26194` x `comments_docstrings` x `rep_1`
  - `scikit-learn__scikit-learn-26194` x `remove_tests` x `rep_2`
  - `pallets__flask-5014` x `comments_docstrings` x `rep_0`
  - `pallets__flask-5014` x `remove_tests` x `rep_1`
  - `pallets__flask-5014` x `remove_tests` x `rep_2`
- shareable summary note:
  - `docs/initial_rq1_findings_2026-04-23.md`
- practical milestone:
  - the first `3 repo x 2 condition` oracle-backed slice is complete, the sharpest Flask `remove_tests` behavioral signal has a second replication, and the first pytest PR now covers all four degradation families

- official snapshot:
  - `dev/active/bootstrap-2026-04-22/second_task_candidate_scikit-learn__scikit-learn-26194_snapshot.json`
- run spec:
  - `dev/active/bootstrap-2026-04-22/sklearn_rep_0_run_spec.json`
- materialization summary:
  - `dev/active/bootstrap-2026-04-22/sklearn_rep_0_materialization.json`
- materialized workspaces:
  - `runs/scikit-learn__scikit-learn-26194/codex-cli/clean/rep_0/workspace`
  - `runs/scikit-learn__scikit-learn-26194/codex-cli/comments_docstrings/rep_0/workspace`
- env-prep notes:
  - `src/harness/python_env.py` now treats historical conda bootstrap packages as host-local compatibility hints instead of forcing exact compiled-package source builds
  - the current policy preserves versioned build-tool pins such as `cython==3.0.10`
  - the current policy widens the heavy scientific runtime stack to host-runnable caps, notably `numpy<2` and `scipy<1.14`
  - workspace-local editable installs now strip legacy `--no-use-pep517` when replaying historical pip commands under modern pip
  - as of this session, the clean scikit-learn env build has moved past bootstrap failures and into long-running historical extension compilation

## Verified Pilot Assets

- task snapshot: `dev/active/bootstrap-2026-04-22/first_pilot_task_snapshot.json`
- run spec: `dev/active/bootstrap-2026-04-22/first_pilot_run_spec.json`
- materialization summary: `dev/active/bootstrap-2026-04-22/first_materialization.json`
- clean run findings: `dev/active/bootstrap-2026-04-22/clean_run_findings.md`
- clean env: `dev/active/bootstrap-2026-04-22/clean_workspace_env_py39.json`
- degraded env: `dev/active/bootstrap-2026-04-22/degraded_workspace_env_py39.json`
- clean exec spec: `dev/active/bootstrap-2026-04-22/clean_codex_exec_spec.json`
- degraded exec spec: `dev/active/bootstrap-2026-04-22/degraded_codex_exec_spec.json`
- rep_1 run spec: `dev/active/bootstrap-2026-04-22/rep_1_run_spec.json`
- rep_1 materialization: `dev/active/bootstrap-2026-04-22/rep_1_materialization.json`
- rep_1 clean env: `dev/active/bootstrap-2026-04-22/rep_1_clean_workspace_env_py39.json`
- rep_1 degraded env: `dev/active/bootstrap-2026-04-22/rep_1_degraded_workspace_env_py39.json`
- rep_1 visible comparison: `dev/active/bootstrap-2026-04-22/rep_1_visible_comparison.json`
- rep_1 oracle comparison: `dev/active/bootstrap-2026-04-22/rep_1_oracle_comparison.json`
- rep_1 clean oracle log: `runs/pytest-dev__pytest-7432/codex-cli/clean/rep_1/logs/oracle_test_output.txt`
- rep_1 degraded oracle log: `runs/pytest-dev__pytest-7432/codex-cli/comments_docstrings/rep_1/logs/oracle_test_output.txt`
- rep_1 clean metrics: `runs/pytest-dev__pytest-7432/codex-cli/clean/rep_1/metrics.json`
- rep_1 degraded metrics: `runs/pytest-dev__pytest-7432/codex-cli/comments_docstrings/rep_1/metrics.json`
- rep_2 run spec: `dev/active/bootstrap-2026-04-22/rep_2_run_spec.json`
- rep_2 materialization: `dev/active/bootstrap-2026-04-22/rep_2_materialization.json`
- rep_2 clean env: `dev/active/bootstrap-2026-04-22/rep_2_clean_workspace_env_py39.json`
- rep_2 degraded env: `dev/active/bootstrap-2026-04-22/rep_2_degraded_workspace_env_py39.json`
- rep_2 visible comparison: `dev/active/bootstrap-2026-04-22/rep_2_visible_comparison.json`
- rep_2 oracle comparison: `dev/active/bootstrap-2026-04-22/rep_2_oracle_comparison.json`
- rep_2 stability summary: `dev/active/bootstrap-2026-04-22/rep_1_rep_2_stability.json`
- rep_2 clean metrics: `runs/pytest-dev__pytest-7432/codex-cli/clean/rep_2/metrics.json`
- rep_2 degraded metrics: `runs/pytest-dev__pytest-7432/codex-cli/comments_docstrings/rep_2/metrics.json`
- rep_3 remove-tests run spec: `dev/active/bootstrap-2026-04-22/rep_3_remove_tests_run_spec.json`
- rep_3 remove-tests materialization: `dev/active/bootstrap-2026-04-22/rep_3_remove_tests_materialization.json`
- rep_3 remove-tests clean env: `dev/active/bootstrap-2026-04-22/rep_3_remove_tests_clean_workspace_env_py39.json`
- rep_3 remove-tests degraded env: `dev/active/bootstrap-2026-04-22/rep_3_remove_tests_degraded_workspace_env_py39.json`
- rep_3 remove-tests comparison: `dev/active/bootstrap-2026-04-22/rep_3_remove_tests_oracle_comparison.json`
- rep_3 remove-tests clean metrics: `runs/pytest-dev__pytest-7432/codex-cli/clean/rep_3/metrics.json`
- rep_3 remove-tests degraded metrics: `runs/pytest-dev__pytest-7432/codex-cli/remove_tests/rep_3/metrics.json`
- rep_4 remove-tests run spec: `dev/active/bootstrap-2026-04-22/rep_4_remove_tests_run_spec.json`
- rep_4 remove-tests materialization: `dev/active/bootstrap-2026-04-22/rep_4_remove_tests_materialization.json`
- rep_4 remove-tests clean env: `dev/active/bootstrap-2026-04-22/rep_4_remove_tests_clean_workspace_env_py39.json`
- rep_4 remove-tests degraded env: `dev/active/bootstrap-2026-04-22/rep_4_remove_tests_degraded_workspace_env_py39.json`
- rep_4 remove-tests comparison: `dev/active/bootstrap-2026-04-22/rep_4_remove_tests_oracle_comparison.json`
- rep_4 remove-tests clean metrics: `runs/pytest-dev__pytest-7432/codex-cli/clean/rep_4/metrics.json`
- rep_4 remove-tests degraded metrics: `runs/pytest-dev__pytest-7432/codex-cli/remove_tests/rep_4/metrics.json`
- remove-tests stability summary: `dev/active/bootstrap-2026-04-22/rep_3_rep_4_remove_tests_stability.json`
- clean workspace: `runs/pytest-dev__pytest-7432/codex-cli/clean/rep_0/workspace`
- degraded workspace: `runs/pytest-dev__pytest-7432/codex-cli/comments_docstrings/rep_0/workspace`

## First Execution Result

- one real clean Codex run completed
- the run produced a plausible patch
- post-run focused validation under Python `3.9` showed `7 passed, 2 failed`
- the main observed failure was a line-number expectation mismatch in the new regression test the agent added

## Rep 1 Execution Result

- a fresh clean rep_1 Codex run completed and passed broader visible validation:
  - `testing/test_terminal.py::TestTerminalFunctional::test_summary_s_alias`
  - `testing/test_terminal.py::TestTerminalFunctional::test_summary_s_alias_with_runxfail`
  - full `testing/test_skipping.py`
- a fresh degraded rep_1 Codex run under `comments_docstrings` also completed and passed broader visible validation:
  - `testing/test_terminal.py::TestTerminalFunctional::test_summary_s_alias`
  - full `testing/test_skipping.py`
- the visible-validation comparison still exists for quick inspection, but rep_1 is now backed by a real oracle replay result
- the oracle replay scored against the official task split and both conditions passed:
  - clean: `1/1` FAIL_TO_PASS, `77/77` PASS_TO_PASS
  - degraded: `1/1` FAIL_TO_PASS, `77/77` PASS_TO_PASS

## RQ1 Teammate Snapshot Pause

- experiment execution is paused to package the current RQ1 findings for teammate review
- current completed oracle-backed evidence base:
  - `20` paired clean-vs-degraded cells
  - `40` individual Codex attempts
  - `3` repos with completed Codex cells
  - `5` unique SWE-bench Verified PRs
  - all `4` degradation families represented
- latest teammate-facing memo:
  - `docs/rq1_initial_findings_for_teammate_2026-04-23.md`
- headline:
  - `0/20` cells show clean success turning into degraded failure
  - `0/20` cells show PASS_TO_PASS regression-damage deltas
  - strongest current result is behavioral sensitivity, especially validation redirection and token-cost changes, not solve-rate collapse
- proper-frame status:
  - `pytest-dev/pytest` is complete across `3 PRs x 4 degradations`
  - `scikit-learn/scikit-learn` has `2/12` selected proper-frame cells complete
  - `sphinx-doc/sphinx` is selected and gold-preflighted, but has `0/12` Codex cells complete

## RQ1 Expanded Target

- the full RQ1 target is now `10` repos with `3-5` SWE-bench Verified PRs per repo
- each selected PR should run all current degradation families:
  - `comments_docstrings`
  - `remove_tests`
  - `type_hints`
  - `naming`
- the old `3 repos x 3 PRs x 4 degradations` frame is now Phase 1, not the endpoint
- current execution priority remains Sphinx:
  - it is already selected
  - three tasks are gold-preflighted
  - it should be cheaper to fill than the remaining scikit-learn cells
- after Sphinx has meaningful completion, screen additional repos in batches toward the `10` repo target rather than drifting PR by PR

## New Sphinx Execution Result

- completed `sphinx-doc__sphinx-9367` x `naming` x `rep_0`
- artifact:
  - `dev/active/bootstrap-2026-04-22/sphinx-doc_sphinx-9367_naming_rep_0_oracle_comparison.json`
- official SWE-bench test outcome:
  - clean passed
  - degraded passed
  - no PASS_TO_PASS regression damage
- behavior:
  - files opened before first edit: `2 -> 3`
  - exploration efficiency: `1.0 -> 0.6667`
  - total tokens: `320633 -> 586173`
- current read:
  - first Sphinx naming evidence extends the same pattern: naming changes search/cost behavior without causing an official task-success drop
- completed `sphinx-doc__sphinx-9367` x `remove_tests` x `rep_3`
- artifact:
  - `dev/active/bootstrap-2026-04-22/sphinx-doc_sphinx-9367_remove_tests_rep_3_oracle_comparison.json`
- official SWE-bench test outcome:
  - clean passed
  - degraded passed
  - no PASS_TO_PASS regression damage
- behavior:
  - files opened before first edit: `2 -> 1`
  - exploration efficiency: `1.0 -> 1.0`
  - total tokens: `404904 -> 498416`
- current read:
  - first Sphinx remove-tests evidence is not an exploration penalty, but still shows compensation cost through higher token use
- completed `sphinx-doc__sphinx-9367` x `type_hints` x `rep_1`
- artifact:
  - `dev/active/bootstrap-2026-04-22/sphinx-doc_sphinx-9367_type_hints_rep_1_oracle_comparison.json`
- official SWE-bench test outcome:
  - clean passed
  - degraded passed
  - no PASS_TO_PASS regression damage
- behavior:
  - files opened before first edit: `2 -> 2`
  - exploration efficiency: `1.0 -> 1.0`
  - total tokens: `318475 -> 606918`
- current read:
  - type-hint stripping on this Sphinx task is a token-cost signal, not a solve-rate or early-search degradation
- completed `sphinx-doc__sphinx-9367` x `comments_docstrings` x `rep_2`
- artifact:
  - `dev/active/bootstrap-2026-04-22/sphinx-doc_sphinx-9367_comments_docstrings_rep_2_oracle_comparison.json`
- official SWE-bench test outcome:
  - clean passed
  - degraded passed
  - no PASS_TO_PASS regression damage
- behavior:
  - files opened before first edit: `2 -> 2`
  - exploration efficiency: `1.0 -> 1.0`
  - total tokens: `466373 -> 571487`
- current read:
  - comments/docstrings stripping on this Sphinx task is cost-visible but not outcome-visible
- `sphinx-doc__sphinx-9367` is now complete across all four degradation families
- completed `sphinx-doc__sphinx-10449` x `naming` x `rep_0`
- artifact:
  - `dev/active/bootstrap-2026-04-22/sphinx-doc_sphinx-10449_naming_rep_0_oracle_comparison.json`
- official SWE-bench test outcome:
  - clean passed
  - degraded passed
  - no PASS_TO_PASS regression damage
- behavior:
  - files opened before first edit: `5 -> 4`
  - exploration efficiency: `0.4 -> 0.5`
  - total tokens: `781838 -> 1814093`
- current read:
  - second Sphinx naming cell again preserves outcome while exposing a large token-cost increase

## Integrity Check 2026-04-26

- focused harness tests:
  - `PYTHONPATH=. uv run --extra dev pytest tests/test_comments_docstrings.py tests/test_type_hints.py tests/test_naming.py tests/test_materialize.py tests/test_codex_metrics.py tests/test_oracle_replay.py tests/test_pilot_run.py`
  - result: `17 passed, 1 warning`
- comparison artifact consistency:
  - checked `25` `*oracle_comparison.json` files
  - required keys present
  - clean/degraded condition labels match
  - target/FAIL_TO_PASS/PASS_TO_PASS deltas recompute correctly
  - summary file-open and exploration metrics match parsed agent metrics
  - result: `0` consistency errors
- current aggregate:
  - `25` paired clean-vs-degraded comparisons
  - `0` clean-success to degraded-failure transitions
  - `0` PASS_TO_PASS damage deltas
  - complete all-four-degradation task sets:
    - `pytest-dev__pytest-7432`
    - `pytest-dev__pytest-10081`
    - `pytest-dev__pytest-10356`
    - `sphinx-doc__sphinx-9367`

## Token Metric Correction 2026-04-26

- user flagged the reported token totals as suspicious because several were larger than a single model context window
- confirmed a real accounting bug:
  - old `total_tokens`: `input_tokens + cached_input_tokens + output_tokens`
  - corrected `total_tokens`: `input_tokens + output_tokens`
  - `cached_input_tokens` is retained separately but is not additive
- repaired all current `*oracle_comparison.json` artifacts with corrected totals
- added `docs/rq1_token_metric_correction_2026-04-26.md`
- focused metric tests now pass:
  - `PYTHONPATH=. uv run --extra dev pytest tests/test_codex_metrics.py tests/test_oracle_packet.py`
  - result: `3 passed`
- current corrected aggregate:
  - `26` scored clean-vs-degraded comparisons
  - `7` unique SWE-bench tasks
  - `4` repositories represented
  - clean-success to degraded-failure transitions: `0/26`
  - benchmark regression-damage deltas: `0/26`
  - degraded corrected token usage higher than clean: `20/26`
  - degraded corrected token usage lower than clean: `6/26`
  - mean degraded-minus-clean corrected token delta: `+110798`
  - median degraded-minus-clean corrected token delta: `+58138`
- latest completed comparison:
  - `sphinx-doc__sphinx-10449` x `remove_tests` x `rep_3`
  - clean and degraded both passed official benchmark tests
  - files opened before first edit: `4 -> 6`
  - exploration efficiency: `0.5 -> 0.1667`
  - corrected total tokens: `374935 -> 762784`

## RQ2 Positioning 2026-04-26

- corrected RQ2 against the original parent project definition:
  - RQ2 asks whether agent-readiness is multi-dimensional
  - operational test: compare degradation effects across bootstrap and execution phases
- current priority:
  - RQ1 remains the headline because outcome and regression-damage deltas are still small or absent
  - RQ2 should support RQ1 by explaining phase/process differences, not replace matrix execution
- generated recoverable RQ2 phase exports from existing Codex JSONL logs:
  - `results/rq2_phase_metrics_2026-04-26.csv`
  - `results/rq2_phase_metrics_2026-04-26.json`
- no rerun required for the first RQ2 process slice
- recoverable from existing logs:
  - first edit event index
  - bootstrap and execution command counts
  - bootstrap and execution edit-event counts
  - bootstrap and execution test-command counts
  - failed validation command counts
- not recoverable reliably from existing logs:
  - time to first edit
  - tokens before first edit
  - post-edit token usage
  - phase-specific cost split
- current RQ2 posture:
  - keep collecting raw logs and refresh phase exports after batches
  - do not over-invest in RQ2 until stronger outcome or phase-specific effects appear

## Sphinx 10449 Comments/Docstrings Rep 2 2026-04-26

- executed `sphinx-doc__sphinx-10449` x `comments_docstrings` x `rep_2`
- artifact:
  - `dev/active/bootstrap-2026-04-22/sphinx-doc_sphinx-10449_comments_docstrings_rep_2_oracle_comparison.json`
  - `dev/active/bootstrap-2026-04-22/sphinx-doc_sphinx-10449_comments_docstrings_rep_2_oracle_comparison.md`
- official oracle outcome:
  - clean passed
  - degraded passed
  - FAIL_TO_PASS failures: `0 -> 0`
  - PASS_TO_PASS failures: `0 -> 0`
- behavior:
  - files opened before first edit: `5 -> 6`
  - exploration efficiency: `0.4 -> 0.3333`
  - corrected total tokens: `387291 -> 558719`
  - changed files: `4 -> 3`
- current read:
  - comments/docstrings removal on the second Sphinx PR again preserves official outcome while increasing bootstrap search cost and corrected token use
- refreshed exports:
  - `results/rq1_comparisons_2026-04-26.csv`
  - `results/rq1_comparisons_2026-04-26.json`
  - `results/rq2_phase_metrics_2026-04-26.csv`
  - `results/rq2_phase_metrics_2026-04-26.json`
- refreshed aggregate:
  - `27` scored clean-vs-degraded comparisons
  - `7` unique SWE-bench tasks
  - `4` repositories represented
  - clean-success to degraded-failure transitions: `0/27`
  - benchmark regression-damage deltas: `0/27`
  - degraded corrected token usage higher than clean: `21/27`
  - degraded corrected token usage lower than clean: `6/27`
  - mean degraded-minus-clean corrected token delta: `+113044`
  - median degraded-minus-clean corrected token delta: `+58138`

## Sphinx 10449 Type-Hints Rep 1 2026-04-26

- resumed the previously paused `sphinx-doc__sphinx-10449` x `type_hints` x `rep_1` cell
  - clean side already existed with a completed Codex exit/log
  - degraded side was missing and was executed without overwriting the clean side
- artifact:
  - `dev/active/bootstrap-2026-04-22/sphinx-doc_sphinx-10449_type_hints_rep_1_oracle_comparison.json`
  - `dev/active/bootstrap-2026-04-22/sphinx-doc_sphinx-10449_type_hints_rep_1_oracle_comparison.md`
- official oracle outcome:
  - clean passed
  - degraded passed
  - FAIL_TO_PASS failures: `0 -> 0`
  - PASS_TO_PASS failures: `0 -> 0`
- behavior:
  - files opened before first edit: `4 -> 4`
  - exploration efficiency: `0.5 -> 0.5`
  - corrected total tokens: `554643 -> 864539`
  - changed files: `3 -> 3`
- RQ2 phase note:
  - degraded execution test-command count increased from `2` to `4`
  - degraded had `1` failed execution test command before passing official oracle replay
  - refreshed RQ2 export test-command detection to avoid counting `tox.ini` file-inspection commands as tox/test executions
- current read:
  - type-hint stripping on this Sphinx task preserves official outcome and bootstrap search parity, but increases token cost and execution validation effort
- refreshed exports:
  - `results/rq1_comparisons_2026-04-26.csv`
  - `results/rq1_comparisons_2026-04-26.json`
  - `results/rq2_phase_metrics_2026-04-26.csv`
  - `results/rq2_phase_metrics_2026-04-26.json`
- refreshed aggregate:
  - `28` scored clean-vs-degraded comparisons
  - `7` unique SWE-bench tasks
  - `4` repositories represented
  - clean-success to degraded-failure transitions: `0/28`
  - benchmark regression-damage deltas: `0/28`
  - degraded corrected token usage higher than clean: `22/28`
  - degraded corrected token usage lower than clean: `6/28`
  - mean degraded-minus-clean corrected token delta: `+120074`
  - median degraded-minus-clean corrected token delta: `+61584`

## Sphinx 9673 Naming Rep 0 2026-04-26

- executed `sphinx-doc__sphinx-9673` x `naming` x `rep_0`
- artifact:
  - `dev/active/bootstrap-2026-04-22/sphinx-doc_sphinx-9673_naming_rep_0_oracle_comparison.json`
  - `dev/active/bootstrap-2026-04-22/sphinx-doc_sphinx-9673_naming_rep_0_oracle_comparison.md`
- official oracle outcome:
  - clean passed
  - degraded passed
  - FAIL_TO_PASS failures: `0 -> 0`
  - PASS_TO_PASS failures: `0 -> 0`
- behavior:
  - files opened before first edit: `6 -> 3`
  - exploration efficiency: `0.3333 -> 0.6667`
  - corrected total tokens: `392263 -> 371918`
  - changed files: `4 -> 4`
- RQ2 phase note:
  - bootstrap command count moved `9 -> 10`
  - execution command count stayed `5 -> 5`
  - execution test-command count stayed `1 -> 1`
- current read:
  - naming degradation on this Sphinx task preserved official outcome and unexpectedly reduced early file-search breadth and corrected token use
- refreshed exports:
  - `results/rq1_comparisons_2026-04-26.csv`
  - `results/rq1_comparisons_2026-04-26.json`
  - `results/rq2_phase_metrics_2026-04-26.csv`
  - `results/rq2_phase_metrics_2026-04-26.json`
- refreshed aggregate:
  - `29` scored clean-vs-degraded comparisons
  - `8` unique SWE-bench tasks
  - `4` repositories represented
  - clean-success to degraded-failure transitions: `0/29`
  - benchmark regression-damage deltas: `0/29`
  - degraded corrected token usage higher than clean: `22/29`
  - degraded corrected token usage lower than clean: `7/29`
  - mean degraded-minus-clean corrected token delta: `+115232`
  - median degraded-minus-clean corrected token delta: `+58138`

## Sphinx 9673 Type-Hints Rep 1 2026-04-26

- executed `sphinx-doc__sphinx-9673` x `type_hints` x `rep_1`
- artifact:
  - `dev/active/bootstrap-2026-04-22/sphinx-doc_sphinx-9673_type_hints_rep_1_oracle_comparison.json`
  - `dev/active/bootstrap-2026-04-22/sphinx-doc_sphinx-9673_type_hints_rep_1_oracle_comparison.md`
- official oracle outcome:
  - clean passed
  - degraded passed
  - FAIL_TO_PASS failures: `0 -> 0`
  - PASS_TO_PASS failures: `0 -> 0`
- behavior:
  - files opened before first edit: `4 -> 5`
  - exploration efficiency: `0.5 -> 0.4`
  - corrected total tokens: `718661 -> 377250`
  - changed files: `4 -> 4`
- RQ2 phase note:
  - bootstrap command count stayed `8 -> 8`
  - execution command count moved `13 -> 6`
  - execution test-command count moved `7 -> 2`
  - failed execution test-command count moved `3 -> 0`
- current read:
  - type-hint stripping on this Sphinx task slightly worsened bootstrap exploration but produced a cheaper, lower-validation-effort execution while preserving official outcome
- refreshed exports:
  - `results/rq1_comparisons_2026-04-26.csv`
  - `results/rq1_comparisons_2026-04-26.json`
  - `results/rq2_phase_metrics_2026-04-26.csv`
  - `results/rq2_phase_metrics_2026-04-26.json`
- refreshed aggregate:
  - `30` scored clean-vs-degraded comparisons
  - `8` unique SWE-bench tasks
  - `4` repositories represented
  - clean-success to degraded-failure transitions: `0/30`
  - benchmark regression-damage deltas: `0/30`
  - degraded corrected token usage higher than clean: `22/30`
  - degraded corrected token usage lower than clean: `8/30`
  - mean degraded-minus-clean corrected token delta: `+100010`
  - median degraded-minus-clean corrected token delta: `+54539`

## Sphinx 9673 Comments/Docstrings Rep 2 2026-04-26

- executed `sphinx-doc__sphinx-9673` x `comments_docstrings` x `rep_2`
- artifact:
  - `dev/active/bootstrap-2026-04-22/sphinx-doc_sphinx-9673_comments_docstrings_rep_2_oracle_comparison.json`
  - `dev/active/bootstrap-2026-04-22/sphinx-doc_sphinx-9673_comments_docstrings_rep_2_oracle_comparison.md`
- official oracle outcome:
  - clean passed
  - degraded passed
  - FAIL_TO_PASS failures: `0 -> 0`
  - PASS_TO_PASS failures: `0 -> 0`
- behavior:
  - files opened before first edit: `3 -> 6`
  - exploration efficiency: `0.6667 -> 0.3333`
  - corrected total tokens: `260101 -> 326402`
  - changed files: `4 -> 4`
- RQ2 phase note:
  - bootstrap command count moved `6 -> 12`
  - execution command count stayed `6 -> 6`
  - execution test-command count stayed `1 -> 1`
- current read:
  - comments/docstrings stripping on `sphinx-9673` preserved official outcome but sharply increased bootstrap exploration breadth and token use
- refreshed exports:
  - `results/rq1_comparisons_2026-04-26.csv`
  - `results/rq1_comparisons_2026-04-26.json`
  - `results/rq2_phase_metrics_2026-04-26.csv`
  - `results/rq2_phase_metrics_2026-04-26.json`
- refreshed aggregate:
  - `31` scored clean-vs-degraded comparisons
  - `8` unique SWE-bench tasks
  - `4` repositories represented
  - clean-success to degraded-failure transitions: `0/31`
  - benchmark regression-damage deltas: `0/31`
  - degraded corrected token usage higher than clean: `23/31`
  - degraded corrected token usage lower than clean: `8/31`
  - mean degraded-minus-clean corrected token delta: `+98923`
  - median degraded-minus-clean corrected token delta: `+58138`

## Sphinx 9673 Remove-Tests Rep 3 2026-04-26

- executed `sphinx-doc__sphinx-9673` x `remove_tests` x `rep_3`
- artifact:
  - `dev/active/bootstrap-2026-04-22/sphinx-doc_sphinx-9673_remove_tests_rep_3_oracle_comparison.json`
  - `dev/active/bootstrap-2026-04-22/sphinx-doc_sphinx-9673_remove_tests_rep_3_oracle_comparison.md`
- official oracle outcome:
  - clean passed
  - degraded passed
  - FAIL_TO_PASS failures: `0 -> 0`
  - PASS_TO_PASS failures: `0 -> 0`
- behavior:
  - files opened before first edit: `4 -> 9`
  - exploration efficiency: `0.5 -> 0.1111`
  - corrected total tokens: `403192 -> 447693`
  - changed files: `4 -> 5`
- RQ2 phase note:
  - bootstrap command count moved `9 -> 12`
  - execution command count moved `6 -> 7`
  - execution test-command count moved `2 -> 3`
  - degraded had one failed execution test command before rerunning with `HOME=/tmp`
- current read:
  - removing the directly relevant Sphinx test preserved official outcome but produced the largest `sphinx-9673` early-exploration penalty so far
  - `sphinx-doc/sphinx` is now complete across the selected `3 PRs x 4 degradations` Phase 1 tranche
- refreshed exports:
  - `results/rq1_comparisons_2026-04-26.csv`
  - `results/rq1_comparisons_2026-04-26.json`
  - `results/rq2_phase_metrics_2026-04-26.csv`
  - `results/rq2_phase_metrics_2026-04-26.json`
- refreshed aggregate:
  - `32` scored clean-vs-degraded comparisons
  - `8` unique SWE-bench tasks
  - `4` repositories represented
  - clean-success to degraded-failure transitions: `0/32`
  - benchmark regression-damage deltas: `0/32`
  - degraded corrected token usage higher than clean: `24/32`
  - degraded corrected token usage lower than clean: `8/32`
  - mean degraded-minus-clean corrected token delta: `+97222`
  - median degraded-minus-clean corrected token delta: `+54539`

## Scikit-Learn 25232 Naming Rep 0 2026-04-27

- executed `scikit-learn__scikit-learn-25232` x `naming` x `rep_0`
- artifact:
  - `dev/active/bootstrap-2026-04-22/scikit-learn_scikit-learn-25232_naming_rep_0_oracle_comparison.json`
  - `dev/active/bootstrap-2026-04-22/scikit-learn_scikit-learn-25232_naming_rep_0_oracle_comparison.md`
- official oracle outcome:
  - clean passed
  - degraded passed
  - FAIL_TO_PASS failures: `0 -> 0`
  - PASS_TO_PASS failures: `0 -> 0`
- behavior:
  - files opened before first edit: `3 -> 3`
  - exploration efficiency: `0.6667 -> 0.6667`
  - corrected total tokens: `827002 -> 977987`
  - changed files: `2 -> 3`
- RQ2 phase note:
  - bootstrap command count moved `16 -> 20`
  - execution command count moved `11 -> 13`
  - execution test-command count moved `4 -> 3`
  - degraded had `2` failed execution test commands due checkout-local validation issues before passing official oracle replay
- current read:
  - naming degradation on this sklearn task preserved official outcome and early exploration parity, but increased token use and bootstrap/command volume
  - degraded validation was noisier even though the oracle result was clean
- refreshed exports:
  - `results/rq1_comparisons_2026-04-26.csv`
  - `results/rq1_comparisons_2026-04-26.json`
  - `results/rq2_phase_metrics_2026-04-26.csv`
  - `results/rq2_phase_metrics_2026-04-26.json`
- refreshed aggregate:
  - `33` scored clean-vs-degraded comparisons
  - `9` unique SWE-bench tasks
  - `4` repositories represented
  - clean-success to degraded-failure transitions: `0/33`
  - benchmark regression-damage deltas: `0/33`
  - degraded corrected token usage higher than clean: `25/33`
  - degraded corrected token usage lower than clean: `8/33`
  - mean degraded-minus-clean corrected token delta: `+98852`
  - median degraded-minus-clean corrected token delta: `+58138`

## Scikit-Learn Deprioritized 2026-04-27

- attempted `scikit-learn__scikit-learn-25232` x `type_hints` x `rep_1`
- stopped the run during clean-side environment preparation before Codex execution and before oracle scoring
- no comparison artifact was emitted and no RQ1/RQ2 export row was added
- removed the unscored partial run directories:
  - `runs/scikit-learn__scikit-learn-25232/codex-cli/clean/rep_1`
  - `runs/scikit-learn__scikit-learn-25232/codex-cli/type_hints/rep_1`
- removed the unscored type-hints run-spec/materialization files for this attempted cell
- decision:
  - keep the existing sklearn cells as valid supporting evidence
  - do not continue sklearn as the immediate third fully complete repo path
  - rationale: even eligible sklearn tasks require very slow editable C-extension builds for each clean/degraded pair, and `scikit-learn__scikit-learn-26194` is not eligible for all four degradations under the current profile
- current repo-completion status for the proper Phase 1 `3 PRs x 4 degradations` tranche:
  - `pytest-dev/pytest`: complete
  - `sphinx-doc/sphinx`: complete
  - third repo: not yet complete; choose a cheaper non-sklearn repo next
- next direction:
  - screen a replacement repo with pure-Python or light-build setup, file-scoped pytest oracle, and all-four-degradation eligibility
  - avoid compiled-extension-heavy repos for the immediate completion checkpoint unless no credible pure-Python option exists

## Replacement Repo Selection 2026-04-27

- screened `pylint-dev/pylint` first because it is pure Python and has pytest-style oracles
- PyLint result:
  - `pylint-dev__pylint-4970` passed gold: `1/1` FAIL_TO_PASS and `17/17` PASS_TO_PASS
  - `pylint-dev__pylint-6903` passed gold: `1/1` FAIL_TO_PASS and `8/8` PASS_TO_PASS
  - `pylint-dev__pylint-7080` failed gold due `3` PASS_TO_PASS misses
  - `pylint-dev__pylint-7277` failed gold due `2` PASS_TO_PASS misses after a legacy editable-install workaround
  - decision: keep PyLint as a future supporting candidate but do not use it for the full `3 PRs x 4 degradations` checkpoint
- fixed a substrate gap discovered during xarray screening:
  - `TaskSnapshot` now preserves optional `environment_setup_commit`, `created_at`, and `difficulty`
  - `to_swebench_instance()` now renders those fields back for SWE-bench `make_test_spec`
  - `run_codex_oracle_cell.py` now has repo-cache entries for `pylint-dev/pylint` and `pydata/xarray`
  - focused tests passed: `PYTHONPATH=. uv run --extra dev pytest tests/test_substrate.py tests/test_materialize.py tests/test_pilot_run.py tests/test_oracle_packet.py` -> `11 passed`
- selected `pydata/xarray` as the replacement third repo:
  - pure-Python editable install using wheels for numerical dependencies
  - file-scoped pytest oracle commands
  - all selected tasks have nonzero type-hint, naming, comments/docstrings, and remove-tests surfaces
- selected xarray tasks:
  - `pydata__xarray-3677`
    - gold preflight passed: `1/1` FAIL_TO_PASS and `21/21` PASS_TO_PASS
    - target surface: `366` annotations, `108` docstrings, `128` comments, `195` naming candidates
  - `pydata__xarray-4629`
    - gold preflight passed: `1/1` FAIL_TO_PASS and `32/32` PASS_TO_PASS
    - target surface: `76` annotations, `19` docstrings, `20` comments, `110` naming candidates
  - `pydata__xarray-4966`
    - gold preflight passed: `4/4` FAIL_TO_PASS and `21/21` PASS_TO_PASS
    - target surface: `11` annotations, `12` docstrings, `20` comments, `51` naming candidates
- rejected xarray reserve:
  - `pydata__xarray-7393` failed gold due `2` PASS_TO_PASS misses
- artifacts:
  - `dev/active/bootstrap-2026-04-22/xarray_signal_screen_2026-04-27.json`
  - `src/profiles/pydata__xarray-3677_eligibility.json`
  - `src/profiles/pydata__xarray-4629_eligibility.json`
  - `src/profiles/pydata__xarray-4966_eligibility.json`
- current full-repo checkpoint status:
  - `pytest-dev/pytest`: complete
  - `sphinx-doc/sphinx`: complete
  - `pydata/xarray`: selected and gold-preflighted, `0/12` Codex cells complete

## Xarray 3677 Naming Rep 0 2026-04-27

- executed `pydata__xarray-3677` x `naming` x `rep_0`
- artifact:
  - `dev/active/bootstrap-2026-04-22/pydata_xarray-3677_naming_rep_0_oracle_comparison.json`
  - `dev/active/bootstrap-2026-04-22/pydata_xarray-3677_naming_rep_0_oracle_comparison.md`
- official oracle outcome:
  - clean passed
  - degraded failed
  - FAIL_TO_PASS failures: `0 -> 0`
  - PASS_TO_PASS failures: `0 -> 8`
- behavior:
  - files opened before first edit: `3 -> 5`
  - exploration efficiency: `0.6667 -> 0.4`
  - corrected total tokens: `413059 -> 684397`
  - changed files: `2 -> 16`
- RQ2 phase note:
  - bootstrap command count moved `10 -> 15`
  - execution command count stayed `7 -> 7`
  - execution test-command count stayed `2 -> 2`
  - degraded had `1` failed execution test command; clean had `0`
- current read:
  - this is the first clean-success to degraded-failure transition in the corrected matrix
  - this is also the first PASS_TO_PASS regression-damage delta
  - naming degradation caused a broad degraded patch across source, tests, and benchmark files, while the clean patch stayed localized to `xarray/core/merge.py` and `xarray/tests/test_merge.py`
  - the failure is not target-loss; the degraded patch still fixed FAIL_TO_PASS but damaged eight existing tests
- refreshed exports:
  - `results/rq1_comparisons_2026-04-26.csv`
  - `results/rq1_comparisons_2026-04-26.json`
  - `results/rq2_phase_metrics_2026-04-26.csv`
  - `results/rq2_phase_metrics_2026-04-26.json`
- refreshed aggregate:
  - `34` scored clean-vs-degraded comparisons
  - `10` unique SWE-bench tasks
  - `5` repositories represented
  - clean-success to degraded-failure transitions: `1/34`
  - benchmark regression-damage deltas: `1/34`
  - degraded corrected token usage higher than clean: `26/34`
  - degraded corrected token usage lower than clean: `8/34`
  - mean degraded-minus-clean corrected token delta: `+103925`
  - median degraded-minus-clean corrected token delta: `+61584`
- next action:
  - continue within the same xarray task to separate a naming-specific effect from broader task sensitivity
  - next queued cell: `pydata__xarray-3677` x `type_hints` x `rep_1`

## Xarray 3677 Type Hints Rep 1 2026-04-27

- executed `pydata__xarray-3677` x `type_hints` x `rep_1`
- artifact:
  - `dev/active/bootstrap-2026-04-22/pydata_xarray-3677_type_hints_rep_1_oracle_comparison.json`
  - `dev/active/bootstrap-2026-04-22/pydata_xarray-3677_type_hints_rep_1_oracle_comparison.md`
- official oracle outcome:
  - clean passed
  - degraded passed
  - FAIL_TO_PASS failures: `0 -> 0`
  - PASS_TO_PASS failures: `0 -> 0`
- behavior:
  - files opened before first edit: `5 -> 4`
  - exploration efficiency: `0.4 -> 0.5`
  - corrected total tokens: `508335 -> 358785`
  - changed files: `2 -> 3`
- RQ2 phase note:
  - bootstrap command count moved `16 -> 12`
  - execution command count moved `5 -> 4`
  - execution test-command count stayed `2 -> 2`
  - neither side had failed execution test commands
- current read:
  - type-hint stripping did not reproduce the xarray naming failure
  - degraded type-hints was cheaper and slightly more direct on early exploration
  - the current xarray signal is therefore condition-specific so far: naming caused outcome and regression damage, type-hints did not
- refreshed exports:
  - `results/rq1_comparisons_2026-04-26.csv`
  - `results/rq1_comparisons_2026-04-26.json`
  - `results/rq2_phase_metrics_2026-04-26.csv`
  - `results/rq2_phase_metrics_2026-04-26.json`
- refreshed aggregate:
  - `35` scored clean-vs-degraded comparisons
  - `10` unique SWE-bench tasks
  - `5` repositories represented
  - clean-success to degraded-failure transitions: `1/35`
  - benchmark regression-damage deltas: `1/35`
  - degraded corrected token usage higher than clean: `26/35`
  - degraded corrected token usage lower than clean: `9/35`
  - mean degraded-minus-clean corrected token delta: `+96683`
  - median degraded-minus-clean corrected token delta: `+58138`
- next action:
  - run `pydata__xarray-3677` x `comments_docstrings` x `rep_2`

## Xarray 3677 Comments/Docstrings Rep 2 2026-04-27

- executed `pydata__xarray-3677` x `comments_docstrings` x `rep_2`
- artifact:
  - `dev/active/bootstrap-2026-04-22/pydata_xarray-3677_comments_docstrings_rep_2_oracle_comparison.json`
  - `dev/active/bootstrap-2026-04-22/pydata_xarray-3677_comments_docstrings_rep_2_oracle_comparison.md`
- official oracle outcome:
  - clean passed
  - degraded passed
  - FAIL_TO_PASS failures: `0 -> 0`
  - PASS_TO_PASS failures: `0 -> 0`
- behavior:
  - files opened before first edit: `3 -> 3`
  - exploration efficiency: `0.6667 -> 0.6667`
  - corrected total tokens: `426628 -> 547441`
  - changed files: `2 -> 3`
- RQ2 phase note:
  - bootstrap command count moved `12 -> 9`
  - execution command count moved `5 -> 6`
  - execution test-command count moved `1 -> 2`
  - neither side had failed execution test commands
- current read:
  - comments/docstrings stripping did not reproduce the xarray naming failure
  - the signal is token and validation-volume cost, not outcome or early-search damage
  - after three xarray cells on `pydata__xarray-3677`, naming remains the only degradation with official outcome damage
- refreshed exports:
  - `results/rq1_comparisons_2026-04-26.csv`
  - `results/rq1_comparisons_2026-04-26.json`
  - `results/rq2_phase_metrics_2026-04-26.csv`
  - `results/rq2_phase_metrics_2026-04-26.json`
- refreshed aggregate:
  - `36` scored clean-vs-degraded comparisons
  - `10` unique SWE-bench tasks
  - `5` repositories represented
  - clean-success to degraded-failure transitions: `1/36`
  - benchmark regression-damage deltas: `1/36`
  - degraded corrected token usage higher than clean: `27/36`
  - degraded corrected token usage lower than clean: `9/36`
  - mean degraded-minus-clean corrected token delta: `+97353`
  - median degraded-minus-clean corrected token delta: `+61584`
- next action:
  - run `pydata__xarray-3677` x `remove_tests` x `rep_3`

## Xarray 3677 Remove Tests Rep 3 2026-04-27

- executed `pydata__xarray-3677` x `remove_tests` x `rep_3`
- artifact:
  - `dev/active/bootstrap-2026-04-22/pydata_xarray-3677_remove_tests_rep_3_oracle_comparison.json`
  - `dev/active/bootstrap-2026-04-22/pydata_xarray-3677_remove_tests_rep_3_oracle_comparison.md`
- official oracle outcome:
  - clean passed
  - degraded passed
  - FAIL_TO_PASS failures: `0 -> 0`
  - PASS_TO_PASS failures: `0 -> 0`
- behavior:
  - files opened before first edit: `4 -> 5`
  - exploration efficiency: `0.5 -> 0.2`
  - corrected total tokens: `327266 -> 435829`
  - changed files: `2 -> 3`
- RQ2 phase note:
  - bootstrap command count moved `11 -> 17`
  - execution command count moved `5 -> 7`
  - execution test-command count stayed `2 -> 2`
  - neither side had failed execution test commands
- current read:
  - remove-tests on this xarray task produced a clear exploration and token-cost penalty but no official outcome damage
  - `pydata__xarray-3677` is now complete across all four degradation families
  - across this completed xarray task, only `naming` caused clean-success to degraded-failure and PASS_TO_PASS damage
- refreshed exports:
  - `results/rq1_comparisons_2026-04-26.csv`
  - `results/rq1_comparisons_2026-04-26.json`
  - `results/rq2_phase_metrics_2026-04-26.csv`
  - `results/rq2_phase_metrics_2026-04-26.json`
- refreshed aggregate:
  - `37` scored clean-vs-degraded comparisons
  - `10` unique SWE-bench tasks
  - `5` repositories represented
  - clean-success to degraded-failure transitions: `1/37`
  - benchmark regression-damage deltas: `1/37`
  - degraded corrected token usage higher than clean: `28/37`
  - degraded corrected token usage lower than clean: `9/37`
  - mean degraded-minus-clean corrected token delta: `+97656`
  - median degraded-minus-clean corrected token delta: `+65029`
- next action:
  - start `pydata__xarray-4629` with `naming` x `rep_0`

## Xarray 4629 Naming Rep 0 2026-04-27

- executed `pydata__xarray-4629` x `naming` x `rep_0`
- artifact:
  - `dev/active/bootstrap-2026-04-22/pydata_xarray-4629_naming_rep_0_oracle_comparison.json`
  - `dev/active/bootstrap-2026-04-22/pydata_xarray-4629_naming_rep_0_oracle_comparison.md`
- official oracle outcome:
  - clean passed
  - degraded failed
  - FAIL_TO_PASS failures: `0 -> 0`
  - PASS_TO_PASS failures: `0 -> 1`
- behavior:
  - files opened before first edit: `2 -> 2`
  - exploration efficiency: `1.0 -> 1.0`
  - corrected total tokens: `204133 -> 398155`
  - changed files: `2 -> 2`
- RQ2 phase note:
  - bootstrap command count stayed `6 -> 6`
  - execution command count moved `3 -> 5`
  - execution test-command count moved `1 -> 2`
  - degraded had one failed bootstrap command but no failed execution test commands
- current read:
  - naming degradation now has repeated xarray outcome damage across two different tasks
  - unlike `pydata__xarray-3677`, this failure did not require broad over-editing; both sides changed the same two files and opened only relevant files before first edit
  - the failure mode is therefore not just search sprawl; naming can preserve apparent locality while still damaging PASS_TO_PASS behavior
- refreshed exports:
  - `results/rq1_comparisons_2026-04-26.csv`
  - `results/rq1_comparisons_2026-04-26.json`
  - `results/rq2_phase_metrics_2026-04-26.csv`
  - `results/rq2_phase_metrics_2026-04-26.json`
- refreshed aggregate:
  - `38` scored clean-vs-degraded comparisons
  - `11` unique SWE-bench tasks
  - `5` repositories represented
  - clean-success to degraded-failure transitions: `2/38`
  - benchmark regression-damage deltas: `2/38`
  - degraded corrected token usage higher than clean: `29/38`
  - degraded corrected token usage lower than clean: `9/38`
  - mean degraded-minus-clean corrected token delta: `+100192`
  - median degraded-minus-clean corrected token delta: `+65665`
- next action:
  - run `pydata__xarray-4629` x `type_hints` x `rep_1`

## Xarray 4629 Type Hints Rep 1 2026-04-27

- executed `pydata__xarray-4629` x `type_hints` x `rep_1`
- artifact:
  - `dev/active/bootstrap-2026-04-22/pydata_xarray-4629_type_hints_rep_1_oracle_comparison.json`
  - `dev/active/bootstrap-2026-04-22/pydata_xarray-4629_type_hints_rep_1_oracle_comparison.md`
- official oracle outcome:
  - clean passed
  - degraded passed
  - FAIL_TO_PASS failures: `0 -> 0`
  - PASS_TO_PASS failures: `0 -> 0`
- behavior:
  - files opened before first edit: `2 -> 2`
  - exploration efficiency: `1.0 -> 1.0`
  - corrected total tokens: `197461 -> 256233`
  - changed files: `2 -> 2`
- RQ2 phase note:
  - bootstrap command count stayed `6 -> 6`
  - execution command count moved `6 -> 5`
  - execution test-command count moved `2 -> 1`
  - neither side had failed execution test commands
- current read:
  - type-hint stripping again did not reproduce xarray naming damage
  - on `pydata__xarray-4629`, naming failed with localized edits, while type-hints preserved outcome and patch scope
- export/process note:
  - added `dev/active/bootstrap-2026-04-22/refresh_exports.py` so future RQ1/RQ2 refreshes are reproducible from a comparison JSON and the saved Codex JSONL logs
- refreshed exports:
  - `results/rq1_comparisons_2026-04-26.csv`
  - `results/rq1_comparisons_2026-04-26.json`
  - `results/rq2_phase_metrics_2026-04-26.csv`
  - `results/rq2_phase_metrics_2026-04-26.json`
- refreshed aggregate:
  - `39` scored clean-vs-degraded comparisons
  - `11` unique SWE-bench tasks
  - `5` repositories represented
  - clean-success to degraded-failure transitions: `2/39`
  - benchmark regression-damage deltas: `2/39`
  - degraded corrected token usage higher than clean: `30/39`
  - degraded corrected token usage lower than clean: `9/39`
  - mean degraded-minus-clean corrected token delta: `+99130`
  - median degraded-minus-clean corrected token delta: `+65029`
- next action:
  - run `pydata__xarray-4629` x `comments_docstrings` x `rep_2`

## Xarray 4629 Comments/Docstrings Rep 2 2026-04-27

- executed `pydata__xarray-4629` x `comments_docstrings` x `rep_2`
- artifact:
  - `dev/active/bootstrap-2026-04-22/pydata_xarray-4629_comments_docstrings_rep_2_oracle_comparison.json`
  - `dev/active/bootstrap-2026-04-22/pydata_xarray-4629_comments_docstrings_rep_2_oracle_comparison.md`
- official oracle outcome:
  - clean passed
  - degraded passed
  - FAIL_TO_PASS failures: `0 -> 0`
  - PASS_TO_PASS failures: `0 -> 0`
- behavior:
  - files opened before first edit: `2 -> 3`
  - exploration efficiency: `1.0 -> 0.6667`
  - corrected total tokens: `172345 -> 390754`
  - changed files: `2 -> 2`
- RQ2 phase note:
  - bootstrap command count moved `5 -> 11`
  - degraded had `1` failed bootstrap test command before first edit
  - execution command count moved `3 -> 6`
  - execution test-command count moved `1 -> 2`
  - neither side had failed execution test commands
- current read:
  - comments/docstrings stripping preserved official outcome but produced a clear bootstrap/process and token-cost penalty on `pydata__xarray-4629`
  - this supports RQ2-style phase sensitivity without changing the RQ1 outcome ranking: naming remains the only xarray degradation causing official failure so far
- refreshed exports:
  - `results/rq1_comparisons_2026-04-26.csv`
  - `results/rq1_comparisons_2026-04-26.json`
  - `results/rq2_phase_metrics_2026-04-26.csv`
  - `results/rq2_phase_metrics_2026-04-26.json`
- refreshed aggregate:
  - `40` scored clean-vs-degraded comparisons
  - `11` unique SWE-bench tasks
  - `5` repositories represented
  - clean-success to degraded-failure transitions: `2/40`
  - benchmark regression-damage deltas: `2/40`
  - degraded corrected token usage higher than clean: `31/40`
  - degraded corrected token usage lower than clean: `9/40`
  - mean degraded-minus-clean corrected token delta: `+102112`
  - median degraded-minus-clean corrected token delta: `+65665`
- next action:
  - run `pydata__xarray-4629` x `remove_tests` x `rep_3`

## Xarray 4629 Remove Tests Rep 3 2026-04-27

- executed `pydata__xarray-4629` x `remove_tests` x `rep_3`
- artifact:
  - `dev/active/bootstrap-2026-04-22/pydata_xarray-4629_remove_tests_rep_3_oracle_comparison.json`
  - `dev/active/bootstrap-2026-04-22/pydata_xarray-4629_remove_tests_rep_3_oracle_comparison.md`
- official oracle outcome:
  - clean passed
  - degraded passed
  - FAIL_TO_PASS failures: `0 -> 0`
  - PASS_TO_PASS failures: `0 -> 0`
- behavior:
  - files opened before first edit: `2 -> 1`
  - exploration efficiency: `1.0 -> 1.0`
  - corrected total tokens: `278069 -> 268874`
  - changed files: `2 -> 2`
- RQ2 phase note:
  - bootstrap command count stayed `6 -> 6`
  - execution test-command count stayed `1 -> 1`
  - no official outcome or regression damage
- current read:
  - `pydata__xarray-4629` is now complete across all four degradation families
  - on this task, only naming caused official PASS_TO_PASS regression damage; type-hints and remove-tests were essentially benign, while comments/docstrings increased bootstrap/process effort
- refreshed exports:
  - `results/rq1_comparisons_2026-04-26.csv`
  - `results/rq1_comparisons_2026-04-26.json`
  - `results/rq2_phase_metrics_2026-04-26.csv`
  - `results/rq2_phase_metrics_2026-04-26.json`
- refreshed aggregate:
  - `41` scored clean-vs-degraded comparisons
  - `11` unique SWE-bench tasks
  - `5` repositories represented
  - clean-success to degraded-failure transitions: `2/41`
  - benchmark regression-damage deltas: `2/41`
  - degraded corrected token usage higher than clean: `31/41`
  - degraded corrected token usage lower than clean: `10/41`
  - mean degraded-minus-clean corrected token delta: `+99397`
  - median degraded-minus-clean corrected token delta: `+65029`
- next action:
  - start `pydata__xarray-4966` with `naming` x `rep_0`

## Xarray 4966 Naming Rep 0 2026-04-27

- executed `pydata__xarray-4966` x `naming` x `rep_0`
- artifact:
  - `dev/active/bootstrap-2026-04-22/pydata_xarray-4966_naming_rep_0_oracle_comparison.json`
  - `dev/active/bootstrap-2026-04-22/pydata_xarray-4966_naming_rep_0_oracle_comparison.md`
- official oracle outcome:
  - clean passed
  - degraded failed
  - FAIL_TO_PASS failures: `0 -> 4`
  - PASS_TO_PASS failures: `0 -> 17`
- behavior:
  - files opened before first edit: `5 -> 5`
  - exploration efficiency: `0.4 -> 0.4`
  - corrected total tokens: `489466 -> 960559`
  - changed files: `2 -> 4`
- current read:
  - naming degradation now repeats as an official failure across all three selected xarray tasks
  - this third case is the strongest xarray naming result: degraded loses all four target tests and damages seventeen PASS_TO_PASS tests
  - the failure again is not captured by early file-open count or exploration-efficiency deltas, which stayed flat; the damage is in semantic interpretation and patch correctness
- refreshed exports:
  - `results/rq1_comparisons_2026-04-26.csv`
  - `results/rq1_comparisons_2026-04-26.json`
  - `results/rq2_phase_metrics_2026-04-26.csv`
  - `results/rq2_phase_metrics_2026-04-26.json`
- refreshed aggregate:
  - `42` scored clean-vs-degraded comparisons
  - `12` unique SWE-bench tasks
  - `5` repositories represented
  - clean-success to degraded-failure transitions: `3/42`
  - benchmark regression-damage deltas: `3/42`
  - degraded corrected token usage higher than clean: `32/42`
  - degraded corrected token usage lower than clean: `10/42`
  - mean degraded-minus-clean corrected token delta: `+108247`
  - median degraded-minus-clean corrected token delta: `+65665`
- next action:
  - run `pydata__xarray-4966` x `type_hints` x `rep_1`

## Xarray 4966 Type Hints Rep 1 2026-04-27

- executed `pydata__xarray-4966` x `type_hints` x `rep_1`
- artifact:
  - `dev/active/bootstrap-2026-04-22/pydata_xarray-4966_type_hints_rep_1_oracle_comparison.json`
  - `dev/active/bootstrap-2026-04-22/pydata_xarray-4966_type_hints_rep_1_oracle_comparison.md`
- official oracle outcome:
  - clean passed
  - degraded passed
  - FAIL_TO_PASS failures: `0 -> 0`
  - PASS_TO_PASS failures: `0 -> 0`
- behavior:
  - files opened before first edit: `4 -> 4`
  - exploration efficiency: `0.5 -> 0.5`
  - corrected total tokens: `454613 -> 614080`
  - changed files: `2 -> 2`
- current read:
  - type-hint stripping again preserved official outcome on xarray
  - after three naming cells and three type-hints cells on xarray, the condition contrast is now strong: naming repeatedly damages correctness, while type-hints mainly changes token cost
- refreshed aggregate:
  - `43` scored clean-vs-degraded comparisons
  - `12` unique SWE-bench tasks
  - `5` repositories represented
  - clean-success to degraded-failure transitions: `3/43`
  - benchmark regression-damage deltas: `3/43`
  - degraded corrected token usage higher than clean: `33/43`
  - degraded corrected token usage lower than clean: `10/43`
  - mean degraded-minus-clean corrected token delta: `+109438`
  - median degraded-minus-clean corrected token delta: `+66301`
- next action:
  - run `pydata__xarray-4966` x `comments_docstrings` x `rep_2`

## Xarray 4966 Comments/Docstrings Rep 2 2026-04-27

- executed `pydata__xarray-4966` x `comments_docstrings` x `rep_2`
- artifact:
  - `dev/active/bootstrap-2026-04-22/pydata_xarray-4966_comments_docstrings_rep_2_oracle_comparison.json`
  - `dev/active/bootstrap-2026-04-22/pydata_xarray-4966_comments_docstrings_rep_2_oracle_comparison.md`
- official oracle outcome:
  - clean passed
  - degraded passed
  - FAIL_TO_PASS failures: `0 -> 0`
  - PASS_TO_PASS failures: `0 -> 0`
- behavior:
  - files opened before first edit: `4 -> 5`
  - exploration efficiency: `0.5 -> 0.4`
  - corrected total tokens: `459782 -> 555215`
  - changed files: `2 -> 2`
- current read:
  - comments/docstrings stripping again preserved official outcome but increased early search and token cost
  - xarray condition pattern remains stable: naming is correctness-damaging; comments/docstrings are process/cost-visible; type-hints are outcome-stable
- refreshed aggregate:
  - `44` scored clean-vs-degraded comparisons
  - `12` unique SWE-bench tasks
  - `5` repositories represented
  - clean-success to degraded-failure transitions: `3/44`
  - benchmark regression-damage deltas: `3/44`
  - degraded corrected token usage higher than clean: `34/44`
  - degraded corrected token usage lower than clean: `10/44`
  - mean degraded-minus-clean corrected token delta: `+109120`
  - median degraded-minus-clean corrected token delta: `+68962`
- next action:
  - run `pydata__xarray-4966` x `remove_tests` x `rep_3`

## Xarray 4966 Remove Tests Rep 3 2026-04-27

- executed `pydata__xarray-4966` x `remove_tests` x `rep_3`
- artifact:
  - `dev/active/bootstrap-2026-04-22/pydata_xarray-4966_remove_tests_rep_3_oracle_comparison.json`
  - `dev/active/bootstrap-2026-04-22/pydata_xarray-4966_remove_tests_rep_3_oracle_comparison.md`
- official oracle outcome:
  - clean passed
  - degraded passed
  - FAIL_TO_PASS failures: `0 -> 0`
  - PASS_TO_PASS failures: `0 -> 0`
- behavior:
  - files opened before first edit: `4 -> 5`
  - exploration efficiency: `0.5 -> 0.2`
  - corrected total tokens: `516662 -> 515154`
  - changed files: `2 -> 3`
- current read:
  - remove-tests preserved official outcome on `pydata__xarray-4966` while worsening early exploration
  - xarray is now complete across the selected `3 PRs x 4 degradations`
  - across the completed xarray repo, all three naming cells caused official clean-success to degraded-failure transitions; no other xarray degradation caused outcome damage
- refreshed aggregate:
  - `45` scored clean-vs-degraded comparisons
  - `12` unique SWE-bench tasks
  - `5` repositories represented
  - clean-success to degraded-failure transitions: `3/45`
  - benchmark regression-damage deltas: `3/45`
  - degraded corrected token usage higher than clean: `34/45`
  - degraded corrected token usage lower than clean: `11/45`
  - mean degraded-minus-clean corrected token delta: `+106661`
  - median degraded-minus-clean corrected token delta: `+66301`
- full-repo checkpoint:
  - `pytest-dev/pytest`: complete
  - `sphinx-doc/sphinx`: complete
  - `pydata/xarray`: complete
  - current fully complete repo count: `3`
- next action:
  - screen the next pure-Python/light-build repo for the fourth fully complete repo

## Sympy Screening and 11618 Completion 2026-04-27

- added two small execution-support helpers:
  - `dev/active/bootstrap-2026-04-22/refresh_exports.py` refreshes RQ1/RQ2 CSV/JSON exports from saved comparison packets and Codex JSONL logs using the corrected token formula
  - `dev/active/bootstrap-2026-04-22/screen_repo_tasks.py` gold-preflights candidate tasks, counts degradation surfaces, and writes eligibility profiles
- fixed `src/harness/oracle_replay.py` so official SWE-bench commands with leading environment assignments run correctly; Sympy uses `PYTHONWARNINGS=... bin/test ...`
- screened Sympy as the next light-build repo:
  - accepted/gold-preflighted: `sympy__sympy-11618`, `sympy__sympy-12096`, `sympy__sympy-12419`, `sympy__sympy-12481`, `sympy__sympy-12489`
  - selected first three for the full-repo checkpoint: `11618`, `12096`, `12419`
  - caveat: these Sympy tasks have `0` annotation nodes in the scoped surfaces, so `type_hints` is retained for matrix shape but is low-signal/no-op relative to naming/comments/remove-tests
- completed `sympy__sympy-11618` across all four degradations:
  - `naming` x `rep_0`: clean passed, degraded failed; FAIL_TO_PASS failures `0 -> 0`; PASS_TO_PASS failures `0 -> 2`; corrected tokens `526554 -> 521011`; changed files `2 -> 5`
  - `comments_docstrings` x `rep_2`: clean and degraded passed; FAIL_TO_PASS failures `0 -> 0`; PASS_TO_PASS failures `0 -> 0`; corrected tokens `651001 -> 644603`; changed files `2 -> 2`
  - `remove_tests` x `rep_3`: clean and degraded passed; FAIL_TO_PASS failures `0 -> 0`; PASS_TO_PASS failures `0 -> 0`; corrected tokens `592535 -> 1081342`; changed files `2 -> 2`
  - `type_hints` x `rep_1`: clean and degraded passed; FAIL_TO_PASS failures `0 -> 0`; PASS_TO_PASS failures `0 -> 0`; corrected tokens `501705 -> 334294`; changed files `2 -> 2`
- current aggregate after `sympy__sympy-11618` completion:
  - `49` scored clean-vs-degraded comparisons
  - `13` unique SWE-bench tasks
  - `6` repositories represented
  - clean-success to degraded-failure transitions: `4/49`
  - benchmark regression-damage deltas: `4/49`
  - degraded corrected token usage higher than clean: `35/49`
  - degraded corrected token usage lower than clean: `14/49`
  - mean degraded-minus-clean corrected token delta: `+104270`
  - median degraded-minus-clean corrected token delta: `+65029`
- current read:
  - Sympy adds a non-xarray naming transition, strengthening the RQ1 signal that naming degradation can damage correctness beyond one repo
  - comments/docstrings and remove-tests remain process/cost-visible on this first Sympy task without official outcome damage
- next action:
  - continue `sympy__sympy-12096` across the four degradation cells

## Sympy 12096 Completion 2026-04-27

- completed `sympy__sympy-12096` across all four degradations:
  - `naming` x `rep_0`: clean and degraded both passed; FAIL_TO_PASS failures `0 -> 0`; PASS_TO_PASS failures `0 -> 0`; corrected tokens `739131 -> 1563817`; changed files `2 -> 8`
  - `comments_docstrings` x `rep_2`: clean and degraded both passed; FAIL_TO_PASS failures `0 -> 0`; PASS_TO_PASS failures `0 -> 0`; corrected tokens `532998 -> 1076892`; changed files `2 -> 3`
  - `remove_tests` x `rep_3`: clean and degraded both passed; FAIL_TO_PASS failures `0 -> 0`; PASS_TO_PASS failures `0 -> 0`; corrected tokens `876074 -> 1015008`; changed files `2 -> 3`
  - `type_hints` x `rep_1`: clean and degraded both passed; FAIL_TO_PASS failures `0 -> 0`; PASS_TO_PASS failures `0 -> 0`; corrected tokens `846266 -> 537162`; changed files `2 -> 2`
- current aggregate after `sympy__sympy-12096` completion:
  - `53` scored clean-vs-degraded comparisons
  - `14` unique SWE-bench tasks
  - `6` repositories represented
  - clean-success to degraded-failure transitions: `4/53`
  - benchmark regression-damage deltas: `4/53`
  - degraded corrected token usage higher than clean: `38/53`
  - degraded corrected token usage lower than clean: `15/53`
  - mean degraded-minus-clean corrected token delta: `+119012`
  - median degraded-minus-clean corrected token delta: `+66301`
- current read:
  - `sympy__sympy-12096` did not add official outcome damage, but naming again produced the broadest degraded patch shape and the largest token increase in the task
  - comments/docstrings and remove-tests also increased degraded token cost and changed one extra test file while preserving official outcome
  - low-signal type-hints remained outcome-stable and cheaper, consistent with the `0` annotation-node caveat
- next action:
  - run `sympy__sympy-12419` across the four degradation cells to complete Sympy as the fourth full repo

## Sympy 12419 Completion 2026-04-27

- completed `sympy__sympy-12419` across all four degradations:
  - `naming` x `rep_0`: clean passed, degraded failed; FAIL_TO_PASS failures `0 -> 1`; PASS_TO_PASS failures `0 -> 7`; corrected tokens `2124867 -> 2327688`; changed files `4 -> 8`
  - `comments_docstrings` x `rep_2`: clean and degraded both passed; FAIL_TO_PASS failures `0 -> 0`; PASS_TO_PASS failures `0 -> 0`; corrected tokens `1116747 -> 2123692`; changed files `3 -> 4`
  - `remove_tests` x `rep_3`: clean and degraded both passed; FAIL_TO_PASS failures `0 -> 0`; PASS_TO_PASS failures `0 -> 0`; corrected tokens `692285 -> 868570`; changed files `2 -> 3`
  - `type_hints` x `rep_1`: clean and degraded both passed; FAIL_TO_PASS failures `0 -> 0`; PASS_TO_PASS failures `0 -> 0`; corrected tokens `1927531 -> 2052480`; changed files `4 -> 4`
- current aggregate after Sympy completion:
  - `57` scored clean-vs-degraded comparisons
  - `15` unique SWE-bench tasks
  - `6` repositories represented
  - clean-success to degraded-failure transitions: `5/57`
  - benchmark regression-damage deltas: `5/57`
  - degraded corrected token usage higher than clean: `42/57`
  - degraded corrected token usage lower than clean: `15/57`
  - mean degraded-minus-clean corrected token delta: `+137169`
  - median degraded-minus-clean corrected token delta: `+79840`
- full-repo checkpoint:
  - `pytest-dev/pytest`: complete
  - `sphinx-doc/sphinx`: complete
  - `pydata/xarray`: complete
  - `sympy/sympy`: complete
  - current fully complete repo count: `4`
- current read:
  - Sympy produced two naming outcome transitions across the three selected tasks, so naming damage now appears in both xarray and Sympy
  - non-naming Sympy conditions were outcome-stable but frequently cost- and patch-shape-visible
  - Sympy type-hints remain interpreted cautiously because selected scoped surfaces had no annotation nodes
- next action:
  - screen and launch the fifth full repo, with Django first because it has many SWE-bench Verified tasks and should avoid sklearn-style C-extension builds

## Django and Requests Completion 2026-04-27

- completed Django as the fifth full Phase 1 repo:
  - selected/gold-preflighted tasks: `django__django-16502`, `django__django-16527`, `django__django-16631`
  - all three selected tasks now have `naming`, `type_hints`, `comments_docstrings`, and `remove_tests` comparison packets
  - `django__django-16502` clean runs failed official oracle across all four cells, so it is retained as a scored process/cost comparison but interpreted cautiously for outcome damage
  - `django__django-16527` and `django__django-16631` were official-outcome-stable across all four degradation families
  - Django type-hints is low-signal in the selected scoped surfaces because the screened tasks had `0` annotation nodes
- screened Requests after Django because Flask only has one Verified task and PyLint had only two clean gold-preflight tasks:
  - accepted/gold-preflighted: `psf__requests-1142`, `psf__requests-1724`, `psf__requests-1921`
  - avoided `psf__requests-2317` after confirming the known official-oracle hang during screening
  - fixed `screen_repo_tasks.py` to sanitize slash-containing repo names in screen-output filenames
  - added `psf/requests` to `run_codex_oracle_cell.py` source-clone cache mapping
- completed Requests as the sixth full Phase 1 repo:
  - `psf__requests-1142`:
    - `naming` x `rep_0`: clean passed, degraded failed; FAIL_TO_PASS failures `0 -> 1`; PASS_TO_PASS failures `0 -> 0`; tokens `384231 -> 549662`
    - `comments_docstrings` x `rep_2`: clean and degraded both failed; FAIL_TO_PASS failures `1 -> 1`; PASS_TO_PASS failures `0 -> 0`; tokens `443793 -> 840743`
    - `remove_tests` x `rep_3`: clean and degraded both passed; FAIL_TO_PASS failures `0 -> 0`; PASS_TO_PASS failures `0 -> 0`; tokens `466700 -> 456428`
    - `type_hints` x `rep_1`: clean and degraded both failed; FAIL_TO_PASS failures `1 -> 1`; PASS_TO_PASS failures `0 -> 0`; tokens `286357 -> 276143`
  - `psf__requests-1724`:
    - `naming` x `rep_0`: clean passed, degraded failed; FAIL_TO_PASS failures `0 -> 0`; PASS_TO_PASS failures `0 -> 1`; tokens `391253 -> 561634`
    - `comments_docstrings` x `rep_2`: clean and degraded both passed; FAIL_TO_PASS failures `0 -> 0`; PASS_TO_PASS failures `0 -> 0`; tokens `321943 -> 619949`
    - `remove_tests` x `rep_3`: clean and degraded both passed; FAIL_TO_PASS failures `0 -> 0`; PASS_TO_PASS failures `0 -> 0`; tokens `452095 -> 242027`
    - `type_hints` x `rep_1`: clean and degraded both passed; FAIL_TO_PASS failures `0 -> 0`; PASS_TO_PASS failures `0 -> 0`; tokens `382645 -> 401869`
  - `psf__requests-1921`:
    - `naming` x `rep_0`: clean passed, degraded failed; FAIL_TO_PASS failures `0 -> 1`; PASS_TO_PASS failures `0 -> 4`; tokens `397218 -> 484799`
    - `comments_docstrings` x `rep_2`: clean and degraded both passed; FAIL_TO_PASS failures `0 -> 0`; PASS_TO_PASS failures `0 -> 0`; tokens `537503 -> 442013`
    - `remove_tests` x `rep_3`: clean and degraded both passed; FAIL_TO_PASS failures `0 -> 0`; PASS_TO_PASS failures `0 -> 0`; tokens `714487 -> 248814`
    - `type_hints` x `rep_1`: clean failed, degraded passed; FAIL_TO_PASS failures `1 -> 0`; PASS_TO_PASS failures `0 -> 0`; tokens `410095 -> 377309`
- refreshed aggregate after reaching six fully complete repos:
  - `81` scored clean-vs-degraded comparisons
  - `21` unique SWE-bench tasks
  - `8` repositories represented in exports
  - `6` fully complete repos: `pytest-dev/pytest`, `sphinx-doc/sphinx`, `pydata/xarray`, `sympy/sympy`, `django/django`, `psf/requests`
  - clean-success to degraded-failure transitions: `8/81`
  - any target-success changes: `9/81` because `psf__requests-1921` x `type_hints` was a clean-failure/degraded-success reversal
  - PASS_TO_PASS regression-damage deltas: `7/81`
  - degraded corrected token usage higher than clean: `55/81`
  - degraded corrected token usage lower than clean: `26/81`
  - mean degraded-minus-clean corrected token delta: `+110566`
  - median degraded-minus-clean corrected token delta: `+79840`
- current RQ1 read:
  - naming is now the strongest outcome-damage signal across multiple repos: xarray, Sympy, and Requests all have naming-induced clean-success to degraded-failure transitions
  - comments/docstrings and remove-tests remain mostly process/cost-visible rather than outcome-damaging in the six-repo tranche
  - type-hints should be interpreted cautiously for Sympy/Django/Requests because many selected scoped surfaces had no annotation nodes
- verification:
  - `PYTHONPATH=. uv run --extra dev pytest tests/test_comments_docstrings.py tests/test_type_hints.py tests/test_naming.py tests/test_materialize.py tests/test_codex_metrics.py tests/test_oracle_replay.py tests/test_pilot_run.py tests/test_oracle_packet.py`
  - result: `19 passed, 1 warning`

## RQ2 Phase Read After Six Complete Repos 2026-04-27

- RQ2 remains supporting/process analysis, but the phase metrics now show a credible multi-dimensional signal.
- by condition, degraded-minus-clean phase deltas from `results/rq2_phase_metrics_2026-04-26.csv`:
  - `naming` (`n=19`):
    - bootstrap commands mean `+1.68`, median `+2`
    - first-edit event index mean `+3.37`, median `+4`
    - execution commands mean `+2.26`, median `+1`
    - total commands mean `+3.95`, median `+5`
    - accounts for all `8` clean-success to degraded-failure transitions and all `7` PASS_TO_PASS damage deltas
  - `comments_docstrings` (`n=22`):
    - bootstrap commands mean `+1.95`, median `+1`
    - first-edit event index mean `+4.23`, median `+2`
    - execution commands mean `+0.55`, median `+1`
    - no clean-success to degraded-failure transitions and no PASS_TO_PASS damage deltas
    - current read: primarily early-orientation/search friction
  - `remove_tests` (`n=22`):
    - bootstrap commands mean `+1.0`, median `+2`
    - execution commands mean `+1.41`, median `+1.5`
    - execution test commands mean `+0.55`, median `0`
    - no clean-success to degraded-failure transitions and no PASS_TO_PASS damage deltas
    - current read: more validation/execution-process effect than outcome effect
  - `type_hints` (`n=18`):
    - bootstrap commands mean `-1.67`, median `-1.5`
    - first-edit event index mean `-3.17`, median `-3`
    - total commands mean `-1.61`, median `-1.5`
    - no clean-success to degraded-failure transitions and no PASS_TO_PASS damage deltas
    - current read: do not over-interpret; many selected Sympy/Django/Requests surfaces had `0` annotation nodes
- outcome-damaging runs show a distinct pre-edit/process pattern:
  - clean-success to degraded-failure transitions (`n=8`) had bootstrap commands mean `+3.0`, first-edit event index mean `+6.25`, and total commands mean `+4.5`
  - all `8/8` transition cells had more total commands than their clean pair
  - non-transition cells (`n=73`) had much smaller deltas: bootstrap commands mean `+0.59`, first-edit event index mean `+1.34`, and total commands mean `+1.62`
- interpretation:
  - agent-readiness appears multi-dimensional: naming damages navigation/API comprehension and correctness; comments/docstrings mainly affects bootstrap orientation; remove-tests affects validation behavior; type-hints needs better annotated-code repos before claims are strong
  - this supports RQ2 as a phase/process companion to the RQ1 outcome/cost story, not yet as the primary result

## Naming Failure Mode Triage 2026-04-27

- clean-success to naming-degraded-failure transitions split as:
  - target fixed but PASS_TO_PASS regressed: `4/8`
    - `pydata__xarray-3677`, `pydata__xarray-4629`, `sympy__sympy-11618`, `psf__requests-1724`
  - target failed only: `1/8`
    - `psf__requests-1142`
  - target failed and PASS_TO_PASS regressed: `3/8`
    - `pydata__xarray-4966`, `sympy__sympy-12419`, `psf__requests-1921`
- failure evidence:
  - xarray naming failures often exposed missing/renamed public APIs such as `Dataset.var1`, `Dataset.reindex`, `xarray.core.merge.broadcast_dimension_size`, and coder classes like `CFMaskCoder` / `UnsignedIntegerCoder`
  - Sympy naming failures exposed missing methods such as `Point3D.are_collinear`, `_eval_transpose`, and `_eval_power`
  - Requests naming failures exposed incomplete target behavior (`HEAD` no-body case in `psf__requests-1142`) and missing API hooks such as `Session.prepare_request`
- current read:
  - naming failures are not simply agents being lazy or skipping validation
  - agents often ran focused tests and reported success, but the renamed surface caused broader API/regression damage or incomplete generalization that focused tests missed
  - this strengthens RQ1 because naming appears to impair codebase navigability/API preservation, not only prompt-following discipline

## Matplotlib 23412 Type-Hints Cell 2026-04-28

- executed `matplotlib__matplotlib-23412` x `type_hints` x `rep_1`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `7 -> 6`
  - exploration efficiency moved `0.2857 -> 0.3333`
  - corrected total tokens moved `793645 -> 786997`
  - changed files moved `2 -> 10`
  - current read: outcome-stable, low-signal type-hints cell as expected for a scoped surface with `0` annotation nodes; degraded still broadened patch shape by touching toolbar SVG assets plus the source/test pair
- refreshed aggregate after this cell:
  - `87` scored clean-vs-degraded comparisons
  - `23` unique SWE-bench tasks
  - `9` repositories represented in exports
  - clean-success to degraded-failure transitions: `9/87`
  - PASS_TO_PASS regression-damage deltas: `9/87`

## Matplotlib 23412 Comments/Docstrings Cell 2026-04-28

- executed `matplotlib__matplotlib-23412` x `comments_docstrings` x `rep_2`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `7 -> 8`
  - exploration efficiency moved `0.2857 -> 0.25`
  - corrected total tokens moved `926710 -> 945449`
  - changed files moved `2 -> 10`
  - current read: comments/docstrings preserved official outcome on this task but added modest bootstrap friction and patch breadth; degraded again edited toolbar SVG assets in addition to `patches.py` and `test_patches.py`
- refreshed aggregate after this cell:
  - `88` scored clean-vs-degraded comparisons
  - `23` unique SWE-bench tasks
  - `9` repositories represented in exports
  - clean-success to degraded-failure transitions: `9/88`
  - PASS_TO_PASS regression-damage deltas: `9/88`

## Matplotlib 23412 Remove-Tests Cell 2026-04-28

- executed `matplotlib__matplotlib-23412` x `remove_tests` x `rep_3`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `3 -> 8`
  - exploration efficiency moved `0.6667 -> 0.125`
  - corrected total tokens moved `964624 -> 1159409`
  - changed files moved `2 -> 10`
  - current read: remove-tests preserved official outcome but produced the strongest `23412` non-naming bootstrap penalty; degraded opened seven dead-end files before first edit and again broadened the patch into toolbar SVG assets
- `matplotlib__matplotlib-23412` is now complete across all four degradation families.
- refreshed aggregate after this cell:
  - `89` scored clean-vs-degraded comparisons
  - `23` unique SWE-bench tasks
  - `9` repositories represented in exports
  - clean-success to degraded-failure transitions: `9/89`
  - PASS_TO_PASS regression-damage deltas: `9/89`

## Matplotlib 26291 Naming Cell 2026-04-28

- executed `matplotlib__matplotlib-26291` x `naming` x `rep_0`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit stayed `2 -> 2`
  - exploration efficiency stayed `1.0 -> 1.0`
  - corrected total tokens moved `541663 -> 831425`
  - changed files moved `2 -> 10`
  - current read: naming did not produce a third matplotlib outcome-damage cell, but it preserved the recurring degraded patch-breadth pattern by adding toolbar SVG assets while official behavior remained intact
- refreshed aggregate after this cell:
  - `90` scored clean-vs-degraded comparisons
  - `24` unique SWE-bench tasks
  - `9` repositories represented in exports
  - clean-success to degraded-failure transitions: `9/90`
  - PASS_TO_PASS regression-damage deltas: `9/90`

## Matplotlib 26291 Type-Hints Cell 2026-04-28

- executed `matplotlib__matplotlib-26291` x `type_hints` x `rep_1`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `3 -> 2`
  - exploration efficiency moved `0.6667 -> 1.0`
  - corrected total tokens moved `402978 -> 387208`
  - changed files moved `2 -> 10`
  - current read: outcome-stable low-signal type-hints cell; degraded was slightly more direct and cheaper despite the same toolbar SVG patch-breadth pattern
- refreshed aggregate after this cell:
  - `91` scored clean-vs-degraded comparisons
  - `24` unique SWE-bench tasks
  - `9` repositories represented in exports
  - clean-success to degraded-failure transitions: `9/91`
  - PASS_TO_PASS regression-damage deltas: `9/91`

## Matplotlib 26291 Comments/Docstrings Cell 2026-04-28

- executed `matplotlib__matplotlib-26291` x `comments_docstrings` x `rep_2`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit stayed `2 -> 2`
  - exploration efficiency stayed `1.0 -> 1.0`
  - corrected total tokens were effectively unchanged: `474112 -> 474110`
  - changed files moved `2 -> 10`
  - current read: comments/docstrings preserved both official outcome and early exploration on this task; the visible degraded signal is patch breadth, not cost or search friction
- refreshed aggregate after this cell:
  - `92` scored clean-vs-degraded comparisons
  - `24` unique SWE-bench tasks
  - `9` repositories represented in exports
  - clean-success to degraded-failure transitions: `9/92`
  - PASS_TO_PASS regression-damage deltas: `9/92`

## Matplotlib 26291 Remove-Tests Cell and Repo Completion 2026-04-28

- executed `matplotlib__matplotlib-26291` x `remove_tests` x `rep_3`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `2 -> 1`
  - exploration efficiency stayed `1.0 -> 1.0`
  - corrected total tokens moved `297176 -> 655803`
  - changed files moved `2 -> 10`
  - current read: remove-tests preserved official outcome and direct early navigation, but raised degraded cost substantially and retained the recurring toolbar SVG patch-breadth pattern
- `matplotlib/matplotlib` is now the seventh fully complete repo:
  - `matplotlib__matplotlib-20676`
  - `matplotlib__matplotlib-23412`
  - `matplotlib__matplotlib-26291`
  - each has `naming`, `type_hints`, `comments_docstrings`, and `remove_tests`
- refreshed aggregate after completing matplotlib:
  - `93` scored clean-vs-degraded comparisons
  - `24` unique SWE-bench tasks
  - `9` repositories represented in exports
  - `7` fully complete repos
  - clean-success to degraded-failure transitions: `9/93`
  - PASS_TO_PASS regression-damage deltas: `9/93`

## PyLint Screening and First Cell 2026-04-28

- resumed PyLint screening after completing matplotlib because PyLint is pure Python and the remaining repo universe is narrow.
- new/fresh accepted PyLint task candidates:
  - `pylint-dev__pylint-4551`: gold replay passed; target surface has `0` annotations, `81` docstrings, `106` comments, `296` naming candidates
  - `pylint-dev__pylint-4604`: gold replay passed; target surface has `3` annotations, `49` docstrings, `311` comments, `419` naming candidates
  - `pylint-dev__pylint-4970`: fresh gold replay now passes after helper compatibility fix; target surface has `118` annotations, `20` docstrings, `70` comments, `303` naming candidates
  - `pylint-dev__pylint-6903`: fresh gold replay now passes after helper compatibility fix; target surface has `19` annotations, `2` docstrings, `28` comments, `42` naming candidates
- helper fixes from PyLint screening:
  - `src/harness/python_env.py` now tolerates unmatched shell quotes in eval scripts when detecting pytest-based official oracles
  - `src/harness/python_env.py` now installs the checkout-local `setup.cfg` astroid constraint before editable installs for historical PyLint tasks whose official requirements pin an incompatible astroid
  - focused verification: `PYTHONPATH=. uv run --extra dev pytest tests/test_python_env.py`
  - result: `16 passed`
- selected PyLint task set for the next full repo:
  - `pylint-dev__pylint-4970`
  - `pylint-dev__pylint-6903`
  - `pylint-dev__pylint-4604`
  - rationale: these three have the best type-hint coverage among the accepted PyLint candidates, while `pylint-dev__pylint-4551` remains a reserve with `0` annotation nodes
- executed `pylint-dev__pylint-4970` x `naming` x `rep_0`
  - clean and degraded both failed official target tests
  - FAIL_TO_PASS failures stayed `1 -> 1`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `4 -> 6`
  - exploration efficiency moved `0.5 -> 0.3333`
  - corrected total tokens moved `596106 -> 1213297`
  - changed files stayed `2 -> 2`
  - current read: not an outcome transition because clean also missed, but naming produced a large cost and bootstrap-friction increase without broadening the final patch
- refreshed aggregate after this cell:
  - `94` scored clean-vs-degraded comparisons
  - `25` unique SWE-bench tasks
  - `10` repositories represented in exports
  - clean-success to degraded-failure transitions: `9/94`
  - PASS_TO_PASS regression-damage deltas: `9/94`

## PyLint 4970 Type-Hints Cell 2026-04-28

- executed `pylint-dev__pylint-4970` x `type_hints` x `rep_1`
  - clean and degraded both failed official target tests
  - FAIL_TO_PASS failures stayed `1 -> 1`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit stayed `4 -> 4`
  - exploration efficiency stayed `0.5 -> 0.5`
  - corrected total tokens moved `1076787 -> 727993`
  - changed files stayed `2 -> 2`
  - current read: baseline-hard task again; type-hints preserved outcome and patch shape while reducing degraded token cost
- refreshed aggregate after this cell:
  - `95` scored clean-vs-degraded comparisons
  - `25` unique SWE-bench tasks
  - `10` repositories represented in exports
  - clean-success to degraded-failure transitions: `9/95`
  - PASS_TO_PASS regression-damage deltas: `9/95`

## PyLint 4970 Comments/Docstrings Cell 2026-04-28

- executed `pylint-dev__pylint-4970` x `comments_docstrings` x `rep_2`
  - clean and degraded both failed official target tests
  - FAIL_TO_PASS failures stayed `1 -> 1`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `5 -> 7`
  - exploration efficiency moved `0.4 -> 0.2857`
  - corrected total tokens moved `726542 -> 1168688`
  - changed files moved `3 -> 2`
  - current read: baseline-hard again; comments/docstrings added cost, dead-end file opens, and failed validation effort while leaving official outcome unchanged
- refreshed aggregate after this cell:
  - `96` scored clean-vs-degraded comparisons
  - `25` unique SWE-bench tasks
  - `10` repositories represented in exports
  - clean-success to degraded-failure transitions: `9/96`
  - PASS_TO_PASS regression-damage deltas: `9/96`

## PyLint 4970 Remove-Tests Cell 2026-04-28

- executed `pylint-dev__pylint-4970` x `remove_tests` x `rep_3`
  - clean and degraded both failed official target tests
  - FAIL_TO_PASS failures stayed `1 -> 1`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `3 -> 2`
  - exploration efficiency moved `0.6667 -> 0.5`
  - corrected total tokens moved `826843 -> 369739`
  - changed files moved `2 -> 3`
  - current read: baseline-hard; remove-tests made degraded cheaper and more direct in command count while adding one changed test file
- `pylint-dev__pylint-4970` is now complete across all four degradation families.
- refreshed aggregate after this cell:
  - `97` scored clean-vs-degraded comparisons
  - `25` unique SWE-bench tasks
  - `10` repositories represented in exports
  - clean-success to degraded-failure transitions: `9/97`
  - PASS_TO_PASS regression-damage deltas: `9/97`

## PyLint 6903 Naming Cell 2026-04-28

- executed `pylint-dev__pylint-6903` x `naming` x `rep_0`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `3 -> 4`
  - exploration efficiency moved `0.6667 -> 0.5`
  - corrected total tokens moved `300170 -> 457137`
  - changed files moved `1 -> 4`
  - current read: naming preserved official outcome here but increased degraded cost, dead-end search, failed validation, and patch breadth
- refreshed aggregate after this cell:
  - `98` scored clean-vs-degraded comparisons
  - `26` unique SWE-bench tasks
  - `10` repositories represented in exports
  - clean-success to degraded-failure transitions: `9/98`
  - PASS_TO_PASS regression-damage deltas: `9/98`

## PyLint 6903 Type-Hints Cell 2026-04-28

- executed `pylint-dev__pylint-6903` x `type_hints` x `rep_1`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit stayed `4 -> 4`
  - exploration efficiency moved `0.25 -> 0.5`
  - corrected total tokens moved `532456 -> 498061`
  - changed files moved `1 -> 4`
  - current read: type-hints preserved official outcome and reduced token cost, but the degraded patch spread into three extra test/support files
- refreshed aggregate after this cell:
  - `99` scored clean-vs-degraded comparisons
  - `26` unique SWE-bench tasks
  - `10` repositories represented in exports
  - clean-success to degraded-failure transitions: `9/99`
  - PASS_TO_PASS regression-damage deltas: `9/99`

## PyLint 6903 Comments/Docstrings Cell 2026-04-28

- executed `pylint-dev__pylint-6903` x `comments_docstrings` x `rep_2`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `5 -> 4`
  - exploration efficiency moved `0.4 -> 0.5`
  - corrected total tokens moved `426574 -> 638537`
  - changed files moved `1 -> 4`
  - current read: comments/docstrings preserved outcome and slightly improved early-file directness, but increased token cost and repeated the broader degraded patch shape seen on `6903` type-hints
- refreshed aggregate after this cell:
  - `100` scored clean-vs-degraded comparisons
  - `26` unique SWE-bench tasks
  - `10` repositories represented in exports
  - clean-success to degraded-failure transitions: `9/100`
  - PASS_TO_PASS regression-damage deltas: `9/100`

## PyLint 6903 Remove-Tests Cell 2026-04-28

- executed `pylint-dev__pylint-6903` x `remove_tests` x `rep_3`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `3 -> 5`
  - exploration efficiency moved `0.6667 -> 0.2`
  - corrected total tokens moved `668400 -> 489210`
  - changed files moved `2 -> 4`
  - current read: remove-tests preserved outcome and reduced degraded token cost, but early exploration degraded sharply and the patch was broader
- `pylint-dev__pylint-6903` is now complete across all four degradation families.
- refreshed aggregate after this cell:
  - `101` scored clean-vs-degraded comparisons
  - `26` unique SWE-bench tasks
  - `10` repositories represented in exports
  - clean-success to degraded-failure transitions: `9/101`
  - PASS_TO_PASS regression-damage deltas: `9/101`

## PyLint 4604 Naming Cell 2026-04-28

- executed `pylint-dev__pylint-4604` x `naming` x `rep_0`
  - clean and degraded both failed official target tests
  - FAIL_TO_PASS failures stayed `21 -> 21`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `4 -> 5`
  - exploration efficiency moved `0.25 -> 0.2`
  - corrected total tokens moved `599032 -> 915659`
  - changed files moved `2 -> 3`
  - current read: baseline-hard in Codex despite gold preflight; naming adds cost, one dead-end open, and one extra changed test file without changing official outcome
- refreshed aggregate after this cell:
  - `102` scored clean-vs-degraded comparisons
  - `27` unique SWE-bench tasks
  - `10` repositories represented in exports
  - clean-success to degraded-failure transitions: `9/102`
  - PASS_TO_PASS regression-damage deltas: `9/102`

## PyLint 4604 Type-Hints Cell 2026-04-28

- executed `pylint-dev__pylint-4604` x `type_hints` x `rep_1`
  - clean and degraded both failed official target tests
  - FAIL_TO_PASS failures stayed `21 -> 21`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `5 -> 3`
  - exploration efficiency moved `0.4 -> 0.3333`
  - corrected total tokens moved `910022 -> 366378`
  - changed files stayed `2 -> 2`
  - current read: baseline-hard again; type-hints made the degraded run much cheaper with identical changed-file set, but did not recover target success
- refreshed aggregate after this cell:
  - `103` scored clean-vs-degraded comparisons
  - `27` unique SWE-bench tasks
  - `10` repositories represented in exports
  - clean-success to degraded-failure transitions: `9/103`
  - PASS_TO_PASS regression-damage deltas: `9/103`

## PyLint 4604 Comments/Docstrings Cell 2026-04-28

- executed `pylint-dev__pylint-4604` x `comments_docstrings` x `rep_2`
  - clean and degraded both failed official target tests
  - FAIL_TO_PASS failures stayed `21 -> 21`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `2 -> 3`
  - exploration efficiency moved `0.5 -> 0.3333`
  - corrected total tokens moved `512551 -> 546094`
  - changed files moved `2 -> 4`
  - current read: baseline-hard; comments/docstrings added small token, search, and patch-breadth cost without changing official outcome
- refreshed aggregate after this cell:
  - `104` scored clean-vs-degraded comparisons
  - `27` unique SWE-bench tasks
  - `10` repositories represented in exports
  - clean-success to degraded-failure transitions: `9/104`
  - PASS_TO_PASS regression-damage deltas: `9/104`

## PyLint 4604 Remove-Tests Cell And 8-Repo Checkpoint 2026-04-28

- executed `pylint-dev__pylint-4604` x `remove_tests` x `rep_3`
  - clean and degraded both failed official target tests
  - FAIL_TO_PASS failures stayed `21 -> 21`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `4 -> 3`
  - exploration efficiency moved `0.25 -> 0.3333`
  - corrected total tokens moved `396669 -> 441524`
  - changed files moved `2 -> 3`
  - current read: baseline-hard; remove-tests slightly improved early-file directness while adding modest token and patch-breadth cost
- `pylint-dev__pylint-4604` is now complete across all four degradation families.
- `pylint-dev/pylint` is now complete across the selected `3 tasks x 4 degradation families`, becoming the eighth fully complete repo.
- refreshed aggregate after this cell:
  - `105` scored clean-vs-degraded comparisons
  - `27` unique SWE-bench tasks
  - `10` repositories represented in exports
  - `8` fully complete repositories
  - clean-success to degraded-failure transitions: `9/105`
  - PASS_TO_PASS regression-damage deltas: `9/105`

## Post-PyLint Repo Selection 2026-04-28

- rechecked Astropy as a potential ninth/tenth full repo with compact candidates:
  - command attempted: `screen_repo_tasks.py astropy/astropy astropy__astropy-14365 astropy__astropy-14182 astropy__astropy-14539 --write-profiles`
  - first candidate `astropy__astropy-14365` still failed during host-local editable install
  - failure path: Astropy `wcs` C-extension build under `/usr/bin/cc`, including incompatible pointer errors in `astropy/wcs/src/wcslib_celprm_wrap.c`
  - current decision: Astropy host blocker is verified still present; do not use Astropy for the next full repo in this lane
- next viable full-repo path is `scikit-learn/scikit-learn` despite slow editable C-extension builds.

## Scikit-Learn 25232 Type-Hints Cell 2026-04-28

- executed `scikit-learn__scikit-learn-25232` x `type_hints` x `rep_1`
  - clean and degraded both passed official target tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `2 -> 3`
  - exploration efficiency moved `1.0 -> 0.6667`
  - corrected total tokens moved `960574 -> 953945`
  - changed files stayed `2 -> 2`
  - changed files overlapped exactly: `sklearn/impute/_iterative.py` and `sklearn/impute/tests/test_impute.py`
  - current read: outcome-stable low-signal type-hints cell; the degraded run added one dead-end pre-edit file open (`sklearn/impute/_base.py`) but did not increase patch breadth or token use
- refreshed aggregate after this cell:
  - `106` scored clean-vs-degraded comparisons
  - `27` unique SWE-bench tasks
  - `10` repositories represented in exports
  - `8` fully complete repositories
  - clean-success to degraded-failure transitions: `9/106`
  - PASS_TO_PASS regression-damage deltas: `9/106`
- strict scikit-learn full-repo path now has:
  - `scikit-learn__scikit-learn-25232`: `2/4` cells complete (`naming`, `type_hints`)
  - `scikit-learn__scikit-learn-25931`: `0/4` cells complete
  - `scikit-learn__scikit-learn-26194`: supporting legacy cells exist, but strict current-family rep indices still need to be filled for full-repo credit
- next strict matrix cell: `scikit-learn__scikit-learn-25232` x `comments_docstrings` x `rep_2`

## Scikit-Learn 25232 Comments/Docstrings Cell 2026-04-28

- executed `scikit-learn__scikit-learn-25232` x `comments_docstrings` x `rep_2`
  - clean and degraded both passed official target tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit stayed `3 -> 3`
  - exploration efficiency stayed `0.6667 -> 0.6667`
  - corrected total tokens moved `840823 -> 882581`
  - changed files stayed `2 -> 2`
  - changed files overlapped exactly: `sklearn/impute/_iterative.py` and `sklearn/impute/tests/test_impute.py`
  - current RQ1 read: outcome-stable, small token-cost increase, no patch-breadth or pre-edit file-search change
  - current RQ2 read: degraded execution had one failed targeted pytest command before recovery; final oracle result still passed
- refreshed aggregate after this cell:
  - `107` scored clean-vs-degraded comparisons
  - `27` unique SWE-bench tasks
  - `10` repositories represented in exports
  - `8` fully complete repositories
  - clean-success to degraded-failure transitions: `9/107`
  - PASS_TO_PASS regression-damage deltas: `9/107`
- strict scikit-learn full-repo path now has:
  - `scikit-learn__scikit-learn-25232`: `3/4` cells complete (`naming`, `type_hints`, `comments_docstrings`)
  - `scikit-learn__scikit-learn-25931`: `0/4` cells complete
  - `scikit-learn__scikit-learn-26194`: supporting legacy cells exist, but strict current-family rep indices still need to be filled for full-repo credit
- next strict matrix cell: `scikit-learn__scikit-learn-25232` x `remove_tests` x `rep_3`

## Scikit-Learn 25232 Remove-Tests Cell 2026-04-28

- executed `scikit-learn__scikit-learn-25232` x `remove_tests` x `rep_3`
  - clean and degraded both passed official target tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `3 -> 5`
  - exploration efficiency moved `0.6667 -> 0.2`
  - corrected total tokens moved `1148003 -> 706913`
  - changed files moved `2 -> 3`
  - degraded-only changed file: `sklearn/impute/tests/test_common.py`
  - current RQ1 read: outcome-stable and cheaper in corrected token use, but with broader patch breadth and weaker early-file targeting
  - current RQ2 read: degraded bootstrap had one failed command and more dead-end pre-edit file opens; execution validation still finished without failed test commands
- refreshed aggregate after this cell:
  - `108` scored clean-vs-degraded comparisons
  - `27` unique SWE-bench tasks
  - `10` repositories represented in exports
  - `8` fully complete repositories
  - clean-success to degraded-failure transitions: `9/108`
  - PASS_TO_PASS regression-damage deltas: `9/108`
- strict scikit-learn full-repo path now has:
  - `scikit-learn__scikit-learn-25232`: `4/4` cells complete (`naming`, `type_hints`, `comments_docstrings`, `remove_tests`)
  - `scikit-learn__scikit-learn-25931`: `0/4` cells complete
  - `scikit-learn__scikit-learn-26194`: supporting legacy cells exist, but strict current-family rep indices still need to be filled for full-repo credit
- next strict matrix cell: `scikit-learn__scikit-learn-25931` x `naming` x `rep_0`

## Scikit-Learn 25931 Naming Cell 2026-04-28

- executed `scikit-learn__scikit-learn-25931` x `naming` x `rep_0`
  - clean passed official target tests; degraded failed official target tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures moved `0 -> 1`
  - files opened before first edit moved `2 -> 3`
  - exploration efficiency moved `1.0 -> 0.6667`
  - corrected total tokens moved `393707 -> 637890`
  - changed files stayed `2 -> 2`
  - changed files overlapped exactly: `sklearn/ensemble/_iforest.py` and `sklearn/ensemble/tests/test_iforest.py`
  - degraded-only pre-edit dead end: `sklearn/tests/test_base.py`
  - current RQ1 read: tenth clean-success to degraded-failure transition overall; naming again produces outcome damage, this time via one PASS_TO_PASS regression without increasing changed-file count
  - current RQ2 read: degraded execution had one failed targeted pytest command before the final full-file run, while clean had no failed test commands
- refreshed aggregate after this cell:
  - `109` scored clean-vs-degraded comparisons
  - `28` unique SWE-bench tasks
  - `10` repositories represented in exports
  - `8` fully complete repositories
  - clean-success to degraded-failure transitions: `10/109`
  - PASS_TO_PASS regression-damage deltas: `10/109`
- strict scikit-learn full-repo path now has:
  - `scikit-learn__scikit-learn-25232`: `4/4` cells complete
  - `scikit-learn__scikit-learn-25931`: `1/4` cells complete (`naming`)
  - `scikit-learn__scikit-learn-26194`: supporting legacy cells exist, but strict current-family rep indices still need to be filled for full-repo credit
- next strict matrix cell: `scikit-learn__scikit-learn-25931` x `type_hints` x `rep_1`

## Scikit-Learn 25931 Type-Hints Cell 2026-04-28

- executed `scikit-learn__scikit-learn-25931` x `type_hints` x `rep_1`
  - clean and degraded both passed official target tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `2 -> 4`
  - exploration efficiency moved `1.0 -> 0.5`
  - corrected total tokens moved `458204 -> 422317`
  - changed files stayed `2 -> 2`
  - changed files overlapped exactly: `sklearn/ensemble/_iforest.py` and `sklearn/ensemble/tests/test_iforest.py`
  - degraded-only pre-edit dead ends: `sklearn/tests/test_base.py` and `sklearn/utils/_testing.py`
  - current RQ1 read: outcome-stable low-signal type-hints cell; degraded run was slightly cheaper in corrected token use and did not broaden the patch
  - current RQ2 read: degraded run needed two targeted pytest executions versus one clean execution, but both validation commands passed and final oracle outcome stayed clean
- refreshed aggregate after this cell:
  - `110` scored clean-vs-degraded comparisons
  - `28` unique SWE-bench tasks
  - `10` repositories represented in exports
  - `8` fully complete repositories
  - clean-success to degraded-failure transitions: `10/110`
  - PASS_TO_PASS regression-damage deltas: `10/110`
- strict scikit-learn full-repo path now has:
  - `scikit-learn__scikit-learn-25232`: `4/4` cells complete
  - `scikit-learn__scikit-learn-25931`: `2/4` cells complete (`naming`, `type_hints`)
  - `scikit-learn__scikit-learn-26194`: supporting legacy cells exist, but strict current-family rep indices still need to be filled for full-repo credit
- next strict matrix cell: `scikit-learn__scikit-learn-25931` x `comments_docstrings` x `rep_2`

## Scikit-Learn 25931 Comments/Docstrings Cell 2026-04-28

- executed `scikit-learn__scikit-learn-25931` x `comments_docstrings` x `rep_2`
  - clean and degraded both passed official target tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit stayed `2 -> 2`
  - exploration efficiency stayed `1.0 -> 1.0`
  - corrected total tokens moved `444694 -> 703306`
  - changed files stayed `2 -> 2`
  - changed files overlapped exactly: `sklearn/ensemble/_iforest.py` and `sklearn/ensemble/tests/test_iforest.py`
  - current RQ1 read: comments/docstrings stripping is outcome-stable here but produces a clear corrected-token cost increase without broader patch or weaker early-file targeting
  - current RQ2 read: degraded execution used more events, commands, and test commands, including one failed non-test command, while targeted pytest validations all passed
- refreshed aggregate after this cell:
  - `111` scored clean-vs-degraded comparisons
  - `28` unique SWE-bench tasks
  - `10` repositories represented in exports
  - `8` fully complete repositories
  - clean-success to degraded-failure transitions: `10/111`
  - PASS_TO_PASS regression-damage deltas: `10/111`
- strict scikit-learn full-repo path now has:
  - `scikit-learn__scikit-learn-25232`: `4/4` cells complete
  - `scikit-learn__scikit-learn-25931`: `3/4` cells complete (`naming`, `type_hints`, `comments_docstrings`)
  - `scikit-learn__scikit-learn-26194`: supporting legacy cells exist, but strict current-family rep indices still need to be filled for full-repo credit
- next strict matrix cell: `scikit-learn__scikit-learn-25931` x `remove_tests` x `rep_3`

## Scikit-Learn 25931 Remove-Tests Cell 2026-04-28

- executed `scikit-learn__scikit-learn-25931` x `remove_tests` x `rep_3`
  - clean and degraded both passed official target tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `2 -> 1`
  - exploration efficiency stayed `1.0 -> 1.0`
  - corrected total tokens moved `455760 -> 567872`
  - changed files stayed `2 -> 2`
  - changed files overlapped exactly: `sklearn/ensemble/_iforest.py` and `sklearn/ensemble/tests/test_iforest.py`
  - clean opened both changed files before first edit; degraded opened only `sklearn/ensemble/_iforest.py`
  - current RQ1 read: remove-tests is outcome-stable here and does not broaden the patch, but increases corrected token use by `112112`
  - current RQ2 read: degraded execution used more commands (`14` vs `8`) and more edit events (`8` vs `6`), while both sides ran three successful test commands and no failed commands
- refreshed aggregate after this cell:
  - `112` scored clean-vs-degraded comparisons
  - `28` unique SWE-bench tasks
  - `10` repositories represented in exports
  - `8` fully complete repositories
  - clean-success to degraded-failure transitions: `10/112`
  - PASS_TO_PASS regression-damage deltas: `10/112`
- strict scikit-learn full-repo path now has:
  - `scikit-learn__scikit-learn-25232`: `4/4` cells complete
  - `scikit-learn__scikit-learn-25931`: `4/4` cells complete
  - `scikit-learn__scikit-learn-26194`: supporting legacy cells exist, but strict current-family rep indices still need to be filled for full-repo credit
- next strict matrix cell: `scikit-learn__scikit-learn-26194` x `naming` x `rep_0`

## Scikit-Learn Third Strict Task Adjustment 2026-04-28

- attempted to launch `scikit-learn__scikit-learn-26194` x `naming` x `rep_0`, but the current helper expected `dev/active/bootstrap-2026-04-22/scikit-learn__scikit-learn-26194_snapshot.json`; only the legacy candidate snapshot exists as `second_task_candidate_scikit-learn__scikit-learn-26194_snapshot.json`
- checked the recorded 26194 eligibility profile before creating any compatibility copy:
  - eligible conditions are only `comments_docstrings` and `remove_tests`
  - this confirms the historical caveat that 26194 is supporting evidence, not a valid all-four strict full-repo task
- screened higher-signal sklearn candidates `scikit-learn__scikit-learn-25973` and `scikit-learn__scikit-learn-26323`
  - `scikit-learn__scikit-learn-25973` passed gold preflight
  - 25973 has all four eligible degradation conditions: `type_hints`, `naming`, `comments_docstrings`, `remove_tests`
  - terminated the unnecessary 26323 preflight during its expensive editable build after 25973 was confirmed sufficient
- strict scikit-learn full-repo path is now:
  - `scikit-learn__scikit-learn-25232`: `4/4` cells complete
  - `scikit-learn__scikit-learn-25931`: `4/4` cells complete
  - `scikit-learn__scikit-learn-25973`: selected as the third strict task

## Scikit-Learn 25973 Naming Cell 2026-04-28

- executed `scikit-learn__scikit-learn-25973` x `naming` x `rep_0`
  - clean and degraded both passed official target tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `6 -> 5`
  - exploration efficiency moved `0.3333 -> 0.4`
  - corrected total tokens moved `347768 -> 549894`
  - changed files stayed `2 -> 2`
  - changed files overlapped exactly: `sklearn/feature_selection/_sequential.py` and `sklearn/feature_selection/tests/test_sequential.py`
  - clean pre-edit dead ends: `sklearn/model_selection/_search.py`, `sklearn/model_selection/_split.py`, `sklearn/utils/_param_validation.py`, `sklearn/utils/tests/test_param_validation.py`
  - degraded pre-edit dead ends: `sklearn/model_selection/_search.py`, `sklearn/model_selection/_split.py`, `sklearn/model_selection/tests/test_split.py`
  - current RQ1 read: naming is outcome-stable on this task but still increases corrected tokens by `202126`; patch breadth remains identical
  - current RQ2 read: degraded bootstrap was slightly shorter, but degraded execution had more commands and one failed targeted pytest command before the final full-file pass
- refreshed aggregate after this cell:
  - `113` scored clean-vs-degraded comparisons
  - `29` unique SWE-bench tasks
  - `10` repositories represented in exports
  - `8` fully complete repositories
  - clean-success to degraded-failure transitions: `10/113`
  - PASS_TO_PASS regression-damage deltas: `10/113`
- next strict matrix cell: `scikit-learn__scikit-learn-25973` x `type_hints` x `rep_1`

## Scikit-Learn 25973 Type-Hints Cell 2026-04-28

- executed `scikit-learn__scikit-learn-25973` x `type_hints` x `rep_1`
  - clean and degraded both passed official target tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `6 -> 7`
  - exploration efficiency moved `0.3333 -> 0.2857`
  - corrected total tokens moved `477202 -> 451756`
  - changed files stayed `2 -> 2`
  - changed files overlapped exactly: `sklearn/feature_selection/_sequential.py` and `sklearn/feature_selection/tests/test_sequential.py`
  - clean pre-edit dead ends: `sklearn/model_selection/_search.py`, `sklearn/model_selection/_split.py`, `sklearn/feature_selection/_rfe.py`, `sklearn/model_selection/tests/test_split.py`
  - degraded pre-edit dead ends: `sklearn/model_selection/_search.py`, `sklearn/model_selection/tests/test_search.py`, `sklearn/model_selection/_split.py`, `sklearn/model_selection/tests/test_split.py`, `sklearn/base.py`
  - current RQ1 read: type-hints stripping is outcome-stable and patch-shape neutral here; it slightly worsens early search diffusion but reduces corrected token use by `25446`
  - current RQ2 read: both sides ran one successful validation command; degraded had fewer total commands (`19` vs `21`) and no failed commands
- refreshed aggregate after this cell:
  - `114` scored clean-vs-degraded comparisons
  - `29` unique SWE-bench tasks
  - `10` repositories represented in exports
  - `8` fully complete repositories
  - clean-success to degraded-failure transitions: `10/114`
  - PASS_TO_PASS regression-damage deltas: `10/114`
- strict scikit-learn full-repo path now has:
  - `scikit-learn__scikit-learn-25232`: `4/4` cells complete
  - `scikit-learn__scikit-learn-25931`: `4/4` cells complete
  - `scikit-learn__scikit-learn-25973`: `2/4` cells complete (`naming`, `type_hints`)
- next strict matrix cell: `scikit-learn__scikit-learn-25973` x `comments_docstrings` x `rep_2`

## Scikit-Learn 25973 Comments/Docstrings Cell 2026-04-28

- executed `scikit-learn__scikit-learn-25973` x `comments_docstrings` x `rep_2`
  - clean and degraded both passed official target tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `7 -> 4`
  - exploration efficiency moved `0.2857 -> 0.5`
  - corrected total tokens moved `467618 -> 521606`
  - changed files stayed `2 -> 2`
  - changed files overlapped exactly: `sklearn/feature_selection/_sequential.py` and `sklearn/feature_selection/tests/test_sequential.py`
  - current RQ1 read: comments/docstrings stripping is outcome-stable and patch-shape neutral here; it improves early targeting but increases corrected token use by `53988`
  - current RQ2 read: degraded used fewer bootstrap and total commands, with one successful validation command versus two clean validation commands
- refreshed aggregate after this cell:
  - `115` scored clean-vs-degraded comparisons
  - `29` unique SWE-bench tasks
  - `10` repositories represented in exports
  - `8` fully complete repositories
  - clean-success to degraded-failure transitions: `10/115`
  - PASS_TO_PASS regression-damage deltas: `10/115`
- strict scikit-learn full-repo path now has:
  - `scikit-learn__scikit-learn-25232`: `4/4` cells complete
  - `scikit-learn__scikit-learn-25931`: `4/4` cells complete
  - `scikit-learn__scikit-learn-25973`: `3/4` cells complete (`naming`, `type_hints`, `comments_docstrings`)
- next strict matrix cell: `scikit-learn__scikit-learn-25973` x `remove_tests` x `rep_3`

## Scikit-Learn 25973 Remove-Tests Cell 2026-04-28

- executed `scikit-learn__scikit-learn-25973` x `remove_tests` x `rep_3`
  - clean and degraded both passed official target tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `4 -> 7`
  - exploration efficiency moved `0.5 -> 0.2857`
  - corrected total tokens moved `608913 -> 980142`
  - changed files stayed `2 -> 2`
  - changed files overlapped exactly: `sklearn/feature_selection/_sequential.py` and `sklearn/feature_selection/tests/test_sequential.py`
  - clean pre-edit dead ends: `sklearn/model_selection/_search.py`, `sklearn/model_selection/_split.py`
  - degraded pre-edit dead ends: `sklearn/model_selection/_split.py`, `sklearn/model_selection/_search.py`, `sklearn/model_selection/tests/test_split.py`, `sklearn/feature_selection/tests/test_feature_select.py`, `sklearn/model_selection/tests/test_search.py`
  - current RQ1 read: remove-tests stripping is outcome-stable and patch-shape neutral here, but increases corrected token use by `371229`
  - current RQ2 read: degraded required more bootstrap commands (`14` vs `12`), had two failed bootstrap commands, and ran more total commands (`30` vs `22`) despite no failed validation commands
- refreshed aggregate after this cell:
  - `116` scored clean-vs-degraded comparisons
  - `29` unique SWE-bench tasks
  - `10` repositories represented in exports
  - `9` fully complete repositories
  - clean-success to degraded-failure transitions: `10/116`
  - PASS_TO_PASS regression-damage deltas: `10/116`
- strict scikit-learn full-repo path is complete:
  - `scikit-learn__scikit-learn-25232`: `4/4` cells complete
  - `scikit-learn__scikit-learn-25931`: `4/4` cells complete
  - `scikit-learn__scikit-learn-25973`: `4/4` cells complete
- `scikit-learn/scikit-learn` is now the ninth fully complete repo.
- next objective: screen and execute one more feasible pure-Python/light-build repo to reach `10` fully complete repos.

## Astropy Reopened for Tenth Repo 2026-04-28

- added a narrow host-local compatibility rule in `src/harness/python_env.py` for historical Astropy editable installs:
  - install Astropy build requirements into the workspace venv before the local editable install: `cython==0.29.30`, `extension-helpers`, `setuptools_scm>=6.2`, and `wheel`
  - run the local editable install with `--no-build-isolation --no-deps`
  - set `CFLAGS="-std=gnu17 -Wno-error=incompatible-pointer-types"` for old bundled C code under the modern host compiler
- focused verification passed:
  - `PYTHONPATH=. uv run --extra dev pytest tests/test_python_env.py`
  - result: `19 passed`
- screened compact Astropy tasks with normal `screen_repo_tasks.py` flow after the env rule:
  - `astropy__astropy-14365`: gold preflight passed; FAIL_TO_PASS/PASS_TO_PASS failures `0/0`; surface `astropy/io/ascii/qdp.py` and `astropy/io/ascii/tests/test_qdp.py`; signals: `0` annotations, `182` name candidates, `12` docstrings, `19` comments
  - `astropy__astropy-14182`: gold preflight passed; FAIL_TO_PASS/PASS_TO_PASS failures `0/0`; surface `astropy/io/ascii/rst.py` and `astropy/io/ascii/tests/test_rst.py`; signals: `0` annotations, `50` name candidates, `11` docstrings, `5` comments
  - `astropy__astropy-14539`: gold preflight passed; FAIL_TO_PASS/PASS_TO_PASS failures `0/0`; surface `astropy/io/fits/diff.py` and `astropy/io/fits/tests/test_diff.py`; signals: `0` annotations, `523` name candidates, `35` docstrings, `149` comments
- all three tasks wrote all-four eligibility profiles:
  - `src/profiles/astropy__astropy-14365_eligibility.json`
  - `src/profiles/astropy__astropy-14182_eligibility.json`
  - `src/profiles/astropy__astropy-14539_eligibility.json`
- caveat: Astropy `type_hints` cells are matrix-completeness/low-signal because all three selected surfaces have `0` annotation nodes.
- selected Astropy as the tenth full-repo path:
  - run order starts with `astropy__astropy-14365` x `naming` x `rep_0`

## Astropy 14365 Naming Cell 2026-04-28

- added one additional harness safeguard before accepting the Astropy comparison:
  - tracked setup-script edits are now committed immediately after setup commands so agent diffs start from setup state
  - focused verification: `PYTHONPATH=. uv run --extra dev pytest tests/test_python_env.py` -> `20 passed`
  - reran `astropy__astropy-14365` x `naming` x `rep_0` after removing the earlier generated Astropy rep-0 workspaces
- executed `astropy__astropy-14365` x `naming` x `rep_0`
  - clean and degraded both failed the official target test
  - FAIL_TO_PASS failures stayed `1 -> 1`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit stayed `2 -> 2`
  - exploration efficiency stayed `1.0 -> 1.0`
  - corrected total tokens moved `424904 -> 182839`
  - changed files stayed `2 -> 2`
  - changed files overlapped exactly: `astropy/io/ascii/qdp.py` and `astropy/io/ascii/tests/test_qdp.py`
  - current RQ1 read: this is a baseline-hard task rather than a degradation-induced failure; naming reduced corrected token use and preserved patch breadth/search targeting
  - current RQ2 read: clean ran two validation commands with one failed test command; degraded ran one successful validation command
- refreshed aggregate after this cell:
  - `117` scored clean-vs-degraded comparisons
  - `30` unique SWE-bench tasks
  - `11` repositories represented in exports
  - `9` fully complete repositories
  - clean-success to degraded-failure transitions: `10/117`
  - PASS_TO_PASS regression-damage deltas: `10/117`
- Astropy tenth-repo path now has:
  - `astropy__astropy-14365`: `1/4` cells complete (`naming`)
  - `astropy__astropy-14182`: `0/4` cells complete
  - `astropy__astropy-14539`: `0/4` cells complete
- next cell completed: `astropy__astropy-14365` x `type_hints` x `rep_1`

## Astropy 14365 Type-Hints Cell 2026-04-28

- executed `astropy__astropy-14365` x `type_hints` x `rep_1`
  - clean and degraded both failed official SWE-bench target tests
  - FAIL_TO_PASS failures stayed `1 -> 1`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit stayed `2 -> 2`
  - exploration efficiency stayed `1.0 -> 1.0`
  - corrected total tokens moved `247115 -> 470352`
  - changed files stayed `2 -> 2`
  - changed files overlapped exactly: `astropy/io/ascii/qdp.py` and `astropy/io/ascii/tests/test_qdp.py`
  - current RQ1 read: low-signal type-hints cell because the selected Astropy surface has `0` annotation nodes; no outcome or patch-breadth damage, but corrected tokens increased by `223237`
  - current RQ2 read: degraded bootstrap was longer (`12` commands vs `7`) and degraded execution had one failed targeted pytest command before the repeated target run; clean ran one successful validation command
- refreshed aggregate after this cell:
  - `118` scored clean-vs-degraded comparisons
  - `30` unique SWE-bench tasks
  - `11` repositories represented in exports
  - `9` fully complete repositories
  - clean-success to degraded-failure transitions: `10/118`
  - PASS_TO_PASS regression-damage deltas: `10/118`
- Astropy tenth-repo path now has:
  - `astropy__astropy-14365`: `2/4` cells complete (`naming`, `type_hints`)
  - `astropy__astropy-14182`: `0/4` cells complete
  - `astropy__astropy-14539`: `0/4` cells complete
- next cell completed: `astropy__astropy-14365` x `comments_docstrings` x `rep_2`

## Astropy 14365 Comments/Docstrings Cell 2026-04-28

- executed `astropy__astropy-14365` x `comments_docstrings` x `rep_2`
  - clean and degraded both failed official SWE-bench target tests
  - FAIL_TO_PASS failures stayed `1 -> 1`
  - PASS_TO_PASS failures moved `0 -> 8`
  - files opened before first edit stayed `2 -> 2`
  - exploration efficiency stayed `1.0 -> 1.0`
  - corrected total tokens moved `310234 -> 436992`
  - changed files stayed `2 -> 2`
  - changed files overlapped exactly: `astropy/io/ascii/qdp.py` and `astropy/io/ascii/tests/test_qdp.py`
  - current RQ1 read: baseline-hard target remains unsolved on both sides, but comments/docstrings caused PASS_TO_PASS regression damage across all `8` passing-preservation tests while preserving patch breadth and early file targeting
  - current RQ2 read: bootstrap command counts stayed equal; degraded execution ran more commands (`10` vs `6`) and its only validation command failed
- refreshed aggregate after this cell:
  - `119` scored clean-vs-degraded comparisons
  - `30` unique SWE-bench tasks
  - `11` repositories represented in exports
  - `9` fully complete repositories
  - clean-success to degraded-failure transitions: `10/119`
  - PASS_TO_PASS regression-damage deltas: `11/119`
- Astropy tenth-repo path now has:
  - `astropy__astropy-14365`: `3/4` cells complete (`naming`, `type_hints`, `comments_docstrings`)
  - `astropy__astropy-14182`: `0/4` cells complete
  - `astropy__astropy-14539`: `0/4` cells complete
- next cell completed: `astropy__astropy-14365` x `remove_tests` x `rep_3`

## Astropy 14365 Remove-Tests Cell 2026-04-28

- executed `astropy__astropy-14365` x `remove_tests` x `rep_3`
  - clean and degraded both failed official SWE-bench target tests
  - FAIL_TO_PASS failures stayed `1 -> 1`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `2 -> 3`
  - exploration efficiency moved `1.0 -> 0.3333`
  - corrected total tokens moved `293926 -> 381447`
  - changed files moved `2 -> 1`
  - clean changed `astropy/io/ascii/qdp.py` and `astropy/io/ascii/tests/test_qdp.py`; degraded changed only `astropy/io/ascii/qdp.py`
  - current RQ1 read: baseline-hard target remains unsolved on both sides with no PASS_TO_PASS damage; removing tests narrowed the patch to source-only but increased corrected tokens and pre-edit search diffusion
  - current RQ2 read: degraded had a longer bootstrap (`12` commands vs `8`) and one failed validation command against `test_write.py -k qdp` after the removed target test was unavailable
- refreshed aggregate after this cell:
  - `120` scored clean-vs-degraded comparisons
  - `30` unique SWE-bench tasks
  - `11` repositories represented in exports
  - `9` fully complete repositories
  - clean-success to degraded-failure transitions: `10/120`
  - PASS_TO_PASS regression-damage deltas: `11/120`
- Astropy tenth-repo path now has:
  - `astropy__astropy-14365`: `4/4` cells complete
  - `astropy__astropy-14182`: `0/4` cells complete
  - `astropy__astropy-14539`: `0/4` cells complete
- next cell completed: `astropy__astropy-14182` x `naming` x `rep_0`

## Astropy 14182 Naming Cell 2026-04-28

- executed `astropy__astropy-14182` x `naming` x `rep_0`
  - clean passed official SWE-bench target tests; degraded failed official target tests
  - FAIL_TO_PASS failures moved `0 -> 1`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `3 -> 4`
  - exploration efficiency moved `0.6667 -> 0.5`
  - corrected total tokens moved `320360 -> 631928`
  - changed files stayed `2 -> 2`
  - changed files overlapped exactly: `astropy/io/ascii/rst.py` and `astropy/io/ascii/tests/test_rst.py`
  - current RQ1 read: eleventh clean-success to degraded-failure transition overall and another naming outcome-damage point; naming roughly doubled corrected tokens, added one dead-end pre-edit file open, and preserved changed-file count
  - current RQ2 read: degraded had a longer bootstrap (`9` commands vs `7`) and one failed targeted validation command before the combined test command; clean had two successful validation commands
- refreshed aggregate after this cell:
  - `121` scored clean-vs-degraded comparisons
  - `31` unique SWE-bench tasks
  - `11` repositories represented in exports
  - `9` fully complete repositories
  - clean-success to degraded-failure transitions: `11/121`
  - PASS_TO_PASS regression-damage deltas: `11/121`
- Astropy tenth-repo path now has:
  - `astropy__astropy-14365`: `4/4` cells complete
  - `astropy__astropy-14182`: `1/4` cells complete (`naming`)
  - `astropy__astropy-14539`: `0/4` cells complete
- next cell completed: `astropy__astropy-14182` x `type_hints` x `rep_1`

## Astropy 14182 Type-Hints Cell 2026-04-28

- executed `astropy__astropy-14182` x `type_hints` x `rep_1`
  - clean and degraded both passed official SWE-bench target tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit stayed `4 -> 4`
  - exploration efficiency stayed `0.5 -> 0.5`
  - corrected total tokens moved `458188 -> 734334`
  - changed files stayed `2 -> 2`
  - changed files overlapped exactly: `astropy/io/ascii/rst.py` and `astropy/io/ascii/tests/test_rst.py`
  - current RQ1 read: low-signal type-hints cell because the selected Astropy surface has `0` annotation nodes; no outcome, patch-breadth, or early-search metric damage, but degraded corrected-token cost increased by `276146`
  - current RQ2 read: degraded had longer bootstrap (`10` commands vs `7`) and more execution commands (`13` vs `10`), while both sides ran two successful validation commands and no failed commands
- refreshed aggregate after this cell:
  - `122` scored clean-vs-degraded comparisons
  - `31` unique SWE-bench tasks
  - `11` repositories represented in exports
  - `9` fully complete repositories
  - clean-success to degraded-failure transitions: `11/122`
  - PASS_TO_PASS regression-damage deltas: `11/122`
- Astropy tenth-repo path now has:
  - `astropy__astropy-14365`: `4/4` cells complete
  - `astropy__astropy-14182`: `2/4` cells complete (`naming`, `type_hints`)
  - `astropy__astropy-14539`: `0/4` cells complete
- next cell completed: `astropy__astropy-14182` x `comments_docstrings` x `rep_2`

## Astropy 14182 Comments/Docstrings Cell 2026-04-28

- executed `astropy__astropy-14182` x `comments_docstrings` x `rep_2`
  - clean and degraded both passed official SWE-bench target tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `4 -> 6`
  - exploration efficiency moved `0.5 -> 0.3333`
  - corrected total tokens moved `449081 -> 548341`
  - changed files stayed `2 -> 2`
  - changed files overlapped exactly: `astropy/io/ascii/rst.py` and `astropy/io/ascii/tests/test_rst.py`
  - current RQ1 read: comments/docstrings stripping preserved outcome and patch breadth here, but increased corrected-token cost and early search diffusion
  - current RQ2 read: bootstrap command counts stayed equal, but degraded execution used more commands (`11` vs `6`) and had one failed targeted pytest command before final success
- refreshed aggregate after this cell:
  - `123` scored clean-vs-degraded comparisons
  - `31` unique SWE-bench tasks
  - `11` repositories represented in exports
  - `9` fully complete repositories
  - clean-success to degraded-failure transitions: `11/123`
  - PASS_TO_PASS regression-damage deltas: `11/123`
- Astropy tenth-repo path now has:
  - `astropy__astropy-14365`: `4/4` cells complete
  - `astropy__astropy-14182`: `3/4` cells complete (`naming`, `type_hints`, `comments_docstrings`)
  - `astropy__astropy-14539`: `0/4` cells complete
- next cell completed: `astropy__astropy-14182` x `remove_tests` x `rep_3`

## Astropy 14182 Remove-Tests Cell 2026-04-28

- executed `astropy__astropy-14182` x `remove_tests` x `rep_3`
  - clean and degraded both passed official SWE-bench target tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `4 -> 5`
  - exploration efficiency moved `0.5 -> 0.2`
  - corrected total tokens moved `320309 -> 507518`
  - changed files stayed `2 -> 2`
  - clean changed `astropy/io/ascii/rst.py` and `astropy/io/ascii/tests/test_rst.py`
  - degraded changed `astropy/io/ascii/rst.py` and `astropy/io/ascii/tests/test_fixedwidth.py`
  - current RQ1 read: remove-tests preserved official outcome, but changed the test-side patch shape because the target `test_rst.py` was removed; degraded also increased token cost and dead-end pre-edit file opens
  - current RQ2 read: degraded had longer bootstrap, six validation commands, and one failed validation command while clean ran one successful validation command
- refreshed aggregate after this cell:
  - `124` scored clean-vs-degraded comparisons
  - `31` unique SWE-bench tasks
  - `11` repositories represented in exports
  - `9` fully complete repositories
  - clean-success to degraded-failure transitions: `11/124`
  - PASS_TO_PASS regression-damage deltas: `11/124`
- `astropy__astropy-14182` is now complete across all four strict degradation families:
  - `naming`
  - `type_hints`
  - `comments_docstrings`
  - `remove_tests`
- Astropy tenth-repo path now has:
  - `astropy__astropy-14365`: `4/4` cells complete
  - `astropy__astropy-14182`: `4/4` cells complete
  - `astropy__astropy-14539`: `0/4` cells complete
- next cell completed: `astropy__astropy-14539` x `naming` x `rep_0`

## Astropy 14539 Naming Cell 2026-04-28

- removed stale generated `runs/astropy__astropy-14539/codex-cli/clean/rep_0` from an incomplete April 22 partial before rerunning this cell; no comparison artifact or agent log existed for the stale run
- executed `astropy__astropy-14539` x `naming` x `rep_0`
  - clean and degraded both passed official SWE-bench target tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `2 -> 3`
  - exploration efficiency moved `1.0 -> 0.6667`
  - corrected total tokens moved `296989 -> 1620500`
  - changed files stayed `2 -> 2`
  - changed files overlapped exactly: `astropy/io/fits/diff.py` and `astropy/io/fits/tests/test_diff.py`
  - current RQ1 read: naming preserved official outcome and patch breadth here, but produced a very large corrected-token increase (`+1323511`) and one extra dead-end pre-edit file open
  - current RQ2 read: degraded execution was much heavier (`22` commands vs `7`), with four validation commands and one failed targeted validation command before final success
- refreshed aggregate after this cell:
  - `125` scored clean-vs-degraded comparisons
  - `32` unique SWE-bench tasks
  - `11` repositories represented in exports
  - `9` fully complete repositories
  - clean-success to degraded-failure transitions: `11/125`
  - PASS_TO_PASS regression-damage deltas: `11/125`
- Astropy tenth-repo path now has:
  - `astropy__astropy-14365`: `4/4` cells complete
  - `astropy__astropy-14182`: `4/4` cells complete
  - `astropy__astropy-14539`: `1/4` cells complete (`naming`)
- next cell completed: `astropy__astropy-14539` x `type_hints` x `rep_1`

## Astropy 14539 Type-Hints Cell 2026-04-28

- executed `astropy__astropy-14539` x `type_hints` x `rep_1`
  - clean and degraded both passed official SWE-bench target tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit stayed `2 -> 2`
  - exploration efficiency stayed `1.0 -> 1.0`
  - corrected total tokens moved `482719 -> 378447`
  - changed files stayed `2 -> 2`
  - changed files overlapped exactly: `astropy/io/fits/diff.py` and `astropy/io/fits/tests/test_diff.py`
  - current RQ1 read: low-signal type-hints matrix-completeness cell because the selected Astropy surface has `0` annotation nodes; outcome, patch breadth, and early search stayed stable while degraded used fewer corrected tokens
  - current RQ2 read: degraded had fewer total commands (`16` vs `21`) and both sides had two successful validation commands, though both had bootstrap command failures unrelated to validation
- refreshed aggregate after this cell:
  - `126` scored clean-vs-degraded comparisons
  - `32` unique SWE-bench tasks
  - `11` repositories represented in exports
  - `9` fully complete repositories
  - clean-success to degraded-failure transitions: `11/126`
  - PASS_TO_PASS regression-damage deltas: `11/126`
- Astropy tenth-repo path now has:
  - `astropy__astropy-14365`: `4/4` cells complete
  - `astropy__astropy-14182`: `4/4` cells complete
  - `astropy__astropy-14539`: `2/4` cells complete (`naming`, `type_hints`)
- next cell completed: `astropy__astropy-14539` x `comments_docstrings` x `rep_2`

## Astropy 14539 Comments/Docstrings Cell 2026-04-28

- executed `astropy__astropy-14539` x `comments_docstrings` x `rep_2`
  - clean and degraded both passed official SWE-bench target tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit stayed `2 -> 2`
  - exploration efficiency stayed `1.0 -> 1.0`
  - corrected total tokens moved `306729 -> 284222`
  - changed files stayed `2 -> 2`
  - changed files overlapped exactly: `astropy/io/fits/diff.py` and `astropy/io/fits/tests/test_diff.py`
  - current RQ1 read: comments/docstrings stripping was outcome-stable, patch-shape neutral, and slightly cheaper on this large FITS diff task
  - current RQ2 read: both sides used two successful validation commands and no failed execution commands
- refreshed aggregate after this cell:
  - `127` scored clean-vs-degraded comparisons
  - `32` unique SWE-bench tasks
  - `11` repositories represented in exports
  - `9` fully complete repositories
  - clean-success to degraded-failure transitions: `11/127`
  - PASS_TO_PASS regression-damage deltas: `11/127`
- Astropy tenth-repo path now has:
  - `astropy__astropy-14365`: `4/4` cells complete
  - `astropy__astropy-14182`: `4/4` cells complete
  - `astropy__astropy-14539`: `3/4` cells complete (`naming`, `type_hints`, `comments_docstrings`)
- next cell completed: `astropy__astropy-14539` x `remove_tests` x `rep_3`

## Astropy 14539 Remove-Tests Cell 2026-04-28

- executed `astropy__astropy-14539` x `remove_tests` x `rep_3`
  - clean and degraded both passed official SWE-bench target tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit stayed `2 -> 2`
  - exploration efficiency moved `1.0 -> 0.5`
  - corrected total tokens moved `345434 -> 291973`
  - changed files stayed `2 -> 2`
  - clean changed `astropy/io/fits/diff.py` and `astropy/io/fits/tests/test_diff.py`
  - degraded changed `astropy/io/fits/diff.py` and `astropy/io/fits/tests/test_fitsdiff.py`
  - current RQ1 read: remove-tests preserved official outcome and reduced corrected-token cost, but shifted the test-side patch to `test_fitsdiff.py` because `test_diff.py` was removed
  - current RQ2 read: degraded execution was shorter and had one successful fallback validation command; degraded had one non-test bootstrap command failure
- refreshed aggregate after this cell:
  - `128` scored clean-vs-degraded comparisons
  - `32` unique SWE-bench tasks
  - `11` repositories represented in exports
  - `10` fully complete repositories
  - clean-success to degraded-failure transitions: `11/128`
  - PASS_TO_PASS regression-damage deltas: `11/128`
- `astropy__astropy-14539` is now complete across all four strict degradation families:
  - `naming`
  - `type_hints`
  - `comments_docstrings`
  - `remove_tests`
- `astropy/astropy` is now the tenth fully complete repo.
- current full-repo checkpoint:
  - `pytest-dev/pytest`
  - `sphinx-doc/sphinx`
  - `pydata/xarray`
  - `sympy/sympy`
  - `django/django`
  - `psf/requests`
  - `matplotlib/matplotlib`
  - `pylint-dev/pylint`
  - `scikit-learn/scikit-learn`
  - `astropy/astropy`
