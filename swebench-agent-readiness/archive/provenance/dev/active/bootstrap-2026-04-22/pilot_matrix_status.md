# Pilot Matrix Status

## Six-Repo Phase 1 Checkpoint 2026-04-27

- fully complete repos: `6`
  - `pytest-dev/pytest`
  - `sphinx-doc/sphinx`
  - `pydata/xarray`
  - `sympy/sympy`
  - `django/django`
  - `psf/requests`
- complete task matrix:
  - `21` unique SWE-bench tasks represented in the flat RQ1 export
  - `81` clean-vs-degraded scored comparisons
  - each fully complete repo has `3` tasks x `4` degradation families
- current aggregate:
  - clean-success to degraded-failure transitions: `8/81`
  - any target-success changes: `9/81`
  - PASS_TO_PASS regression-damage deltas: `7/81`
  - degraded corrected token usage higher than clean: `55/81`
  - degraded corrected token usage lower than clean: `26/81`
  - mean degraded-minus-clean corrected token delta: `+110566`
  - median degraded-minus-clean corrected token delta: `+79840`
- strongest current RQ1 signal:
  - naming degradation is the only family repeatedly producing official outcome damage across multiple repos: xarray, Sympy, and Requests
  - comments/docstrings and remove-tests remain useful for RQ2-style process/cost effects, but are less outcome-damaging in this tranche
  - type-hints is low-signal for several selected tasks with `0` scoped annotation nodes
- current exports:
  - `results/rq1_comparisons_2026-04-26.csv`
  - `results/rq1_comparisons_2026-04-26.json`
  - `results/rq2_phase_metrics_2026-04-26.csv`
  - `results/rq2_phase_metrics_2026-04-26.json`
- RQ2 checkpoint:
  - `naming` is both an outcome-damage and phase-process signal: total commands mean `+3.95`, bootstrap commands mean `+1.68`, execution commands mean `+2.26`
  - outcome-damaging cells (`n=8`) show larger pre-edit friction than non-transition cells: bootstrap commands mean `+3.0` vs `+0.59`, first-edit event index mean `+6.25` vs `+1.34`
  - `comments_docstrings` is mostly bootstrap/orientation friction without outcome damage so far
  - `remove_tests` is more validation/execution-process visible without outcome damage so far
  - `type_hints` remains low-confidence until more annotation-rich repos are selected

## Matplotlib Breadth Start 2026-04-28

- accepted next repo candidate: `matplotlib/matplotlib`
- accepted task set:
  - `matplotlib__matplotlib-20676`: gold preflight passed `2/2` FAIL_TO_PASS and `32/32` PASS_TO_PASS
  - `matplotlib__matplotlib-23412`: gold preflight passed `1/1` FAIL_TO_PASS and `46/46` PASS_TO_PASS
  - `matplotlib__matplotlib-26291`: gold preflight passed `1/1` FAIL_TO_PASS and `49/49` PASS_TO_PASS
- selection caveat:
  - matplotlib env setup is materially slower than Requests/xarray because editable installs build compiled extensions
  - all three accepted task surfaces have `0` annotation nodes, so `type_hints` will be retained for matrix completeness but should remain low-confidence
- first completed matplotlib cell:
  - `matplotlib__matplotlib-20676` x `naming` x `rep_0`
  - clean and degraded both failed target tests: FAIL_TO_PASS failures `2 -> 2`
  - degraded introduced PASS_TO_PASS regression damage: `0 -> 32`
  - corrected tokens `745818 -> 1172686`
  - changed files `2 -> 22`
  - aggregate after refresh: `82` scored comparisons, `22` unique tasks, `9` repos represented in exports, `8` clean-success to degraded-failure transitions, `8` PASS_TO_PASS regression-damage deltas
- second completed matplotlib cell:
  - `matplotlib__matplotlib-20676` x `comments_docstrings` x `rep_2`
  - clean and degraded both failed target tests: FAIL_TO_PASS failures `2 -> 2`
  - PASS_TO_PASS failures `0 -> 0`
  - corrected tokens `681943 -> 1793861`
  - changed files `2 -> 10`
  - aggregate after refresh: `83` scored comparisons, `22` unique tasks, `9` repos represented in exports, `8` clean-success to degraded-failure transitions, `8` PASS_TO_PASS regression-damage deltas
- third completed matplotlib cell:
  - `matplotlib__matplotlib-20676` x `remove_tests` x `rep_3`
  - clean and degraded both failed target tests: FAIL_TO_PASS failures `2 -> 2`
  - PASS_TO_PASS failures `0 -> 0`
  - corrected tokens `891100 -> 577719`
  - changed files `2 -> 10`
  - aggregate after refresh: `84` scored comparisons, `22` unique tasks, `9` repos represented in exports, `8` clean-success to degraded-failure transitions, `8` PASS_TO_PASS regression-damage deltas
- fourth completed matplotlib cell:
  - `matplotlib__matplotlib-20676` x `type_hints` x `rep_1`
  - clean and degraded both failed target tests: FAIL_TO_PASS failures `2 -> 2`
  - PASS_TO_PASS failures `0 -> 0`
  - corrected tokens `778935 -> 632267`
  - changed files `2 -> 10`
  - first matplotlib task is now complete across all four degradation families
  - aggregate after refresh: `85` scored comparisons, `22` unique tasks, `9` repos represented in exports, `8` clean-success to degraded-failure transitions, `8` PASS_TO_PASS regression-damage deltas
- fifth completed matplotlib cell:
  - `matplotlib__matplotlib-23412` x `naming` x `rep_0`
  - clean passed and degraded failed official SWE-bench tests
  - FAIL_TO_PASS failures `0 -> 1`
  - PASS_TO_PASS failures `0 -> 21`
  - corrected tokens `858611 -> 2160998`
  - changed files `2 -> 36`
  - aggregate after refresh: `86` scored comparisons, `23` unique tasks, `9` repos represented in exports, `9` clean-success to degraded-failure transitions, `9` PASS_TO_PASS regression-damage deltas
- sixth completed matplotlib cell:
  - `matplotlib__matplotlib-23412` x `type_hints` x `rep_1`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures `0 -> 0`
  - PASS_TO_PASS failures `0 -> 0`
  - files opened before first edit `7 -> 6`
  - exploration efficiency `0.2857 -> 0.3333`
  - corrected tokens `793645 -> 786997`
  - changed files `2 -> 10`
  - aggregate after refresh: `87` scored comparisons, `23` unique tasks, `9` repos represented in exports, `9` clean-success to degraded-failure transitions, `9` PASS_TO_PASS regression-damage deltas
- seventh completed matplotlib cell:
  - `matplotlib__matplotlib-23412` x `comments_docstrings` x `rep_2`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures `0 -> 0`
  - PASS_TO_PASS failures `0 -> 0`
  - files opened before first edit `7 -> 8`
  - exploration efficiency `0.2857 -> 0.25`
  - corrected tokens `926710 -> 945449`
  - changed files `2 -> 10`
  - aggregate after refresh: `88` scored comparisons, `23` unique tasks, `9` repos represented in exports, `9` clean-success to degraded-failure transitions, `9` PASS_TO_PASS regression-damage deltas
- eighth completed matplotlib cell:
  - `matplotlib__matplotlib-23412` x `remove_tests` x `rep_3`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures `0 -> 0`
  - PASS_TO_PASS failures `0 -> 0`
  - files opened before first edit `3 -> 8`
  - exploration efficiency `0.6667 -> 0.125`
  - corrected tokens `964624 -> 1159409`
  - changed files `2 -> 10`
  - second matplotlib task is now complete across all four degradation families
  - aggregate after refresh: `89` scored comparisons, `23` unique tasks, `9` repos represented in exports, `9` clean-success to degraded-failure transitions, `9` PASS_TO_PASS regression-damage deltas
- ninth completed matplotlib cell:
  - `matplotlib__matplotlib-26291` x `naming` x `rep_0`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures `0 -> 0`
  - PASS_TO_PASS failures `0 -> 0`
  - files opened before first edit `2 -> 2`
  - exploration efficiency `1.0 -> 1.0`
  - corrected tokens `541663 -> 831425`
  - changed files `2 -> 10`
  - aggregate after refresh: `90` scored comparisons, `24` unique tasks, `9` repos represented in exports, `9` clean-success to degraded-failure transitions, `9` PASS_TO_PASS regression-damage deltas
- tenth completed matplotlib cell:
  - `matplotlib__matplotlib-26291` x `type_hints` x `rep_1`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures `0 -> 0`
  - PASS_TO_PASS failures `0 -> 0`
  - files opened before first edit `3 -> 2`
  - exploration efficiency `0.6667 -> 1.0`
  - corrected tokens `402978 -> 387208`
  - changed files `2 -> 10`
  - aggregate after refresh: `91` scored comparisons, `24` unique tasks, `9` repos represented in exports, `9` clean-success to degraded-failure transitions, `9` PASS_TO_PASS regression-damage deltas
- eleventh completed matplotlib cell:
  - `matplotlib__matplotlib-26291` x `comments_docstrings` x `rep_2`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures `0 -> 0`
  - PASS_TO_PASS failures `0 -> 0`
  - files opened before first edit `2 -> 2`
  - exploration efficiency `1.0 -> 1.0`
  - corrected tokens `474112 -> 474110`
  - changed files `2 -> 10`
  - aggregate after refresh: `92` scored comparisons, `24` unique tasks, `9` repos represented in exports, `9` clean-success to degraded-failure transitions, `9` PASS_TO_PASS regression-damage deltas
- twelfth completed matplotlib cell:
  - `matplotlib__matplotlib-26291` x `remove_tests` x `rep_3`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures `0 -> 0`
  - PASS_TO_PASS failures `0 -> 0`
  - files opened before first edit `2 -> 1`
  - exploration efficiency `1.0 -> 1.0`
  - corrected tokens `297176 -> 655803`
  - changed files `2 -> 10`
  - `matplotlib/matplotlib` is now the seventh fully complete repo
  - aggregate after refresh: `93` scored comparisons, `24` unique tasks, `9` repos represented in exports, `9` clean-success to degraded-failure transitions, `9` PASS_TO_PASS regression-damage deltas

## Seven-Repo Checkpoint 2026-04-28

- fully complete repos: `7`
  - `pytest-dev/pytest`
  - `sphinx-doc/sphinx`
  - `pydata/xarray`
  - `sympy/sympy`
  - `django/django`
  - `psf/requests`
  - `matplotlib/matplotlib`
- remaining target: `3` more fully complete repos to reach the `10` repo RQ1 target
- current aggregate:
  - `93` scored clean-vs-degraded comparisons
  - `24` unique SWE-bench tasks
  - clean-success to degraded-failure transitions: `9/93`
  - PASS_TO_PASS regression-damage deltas: `9/93`
  - degraded corrected token usage higher than clean: `62/93`
  - degraded corrected token usage lower than clean: `31/93`
  - mean degraded-minus-clean corrected token delta: `+130930`
  - median degraded-minus-clean corrected token delta: `+79840`

## PyLint Start 2026-04-28

- selected next full-repo candidate: `pylint-dev/pylint`
- selected task set:
  - `pylint-dev__pylint-4970`: gold preflight passed `1/1` FAIL_TO_PASS and `17/17` PASS_TO_PASS; target surface has `118` annotations, `20` docstrings, `70` comments, `303` naming candidates
  - `pylint-dev__pylint-6903`: gold preflight passed `1/1` FAIL_TO_PASS and `8/8` PASS_TO_PASS; target surface has `19` annotations, `2` docstrings, `28` comments, `42` naming candidates
  - `pylint-dev__pylint-4604`: gold preflight passed `21/21` FAIL_TO_PASS and `0/0` PASS_TO_PASS; target surface has `3` annotations, `49` docstrings, `311` comments, `419` naming candidates
- reserve accepted task:
  - `pylint-dev__pylint-4551`: gold preflight passed, but target surface has `0` annotations
- helper updates needed by fresh PyLint screening:
  - tolerate unmatched eval-script shell quotes during pytest oracle detection
  - install checkout-local astroid constraints before historical PyLint editable installs
  - focused verification: `tests/test_python_env.py` passed with `16 passed`
- first completed PyLint cell:
  - `pylint-dev__pylint-4970` x `naming` x `rep_0`
  - clean and degraded both failed target tests: FAIL_TO_PASS failures `1 -> 1`
  - PASS_TO_PASS failures `0 -> 0`
  - files opened before first edit `4 -> 6`
  - exploration efficiency `0.5 -> 0.3333`
  - corrected tokens `596106 -> 1213297`
  - changed files `2 -> 2`
  - aggregate after refresh: `94` scored comparisons, `25` unique tasks, `10` repos represented in exports, `9` clean-success to degraded-failure transitions, `9` PASS_TO_PASS regression-damage deltas
- second completed PyLint cell:
  - `pylint-dev__pylint-4970` x `type_hints` x `rep_1`
  - clean and degraded both failed target tests: FAIL_TO_PASS failures `1 -> 1`
  - PASS_TO_PASS failures `0 -> 0`
  - files opened before first edit `4 -> 4`
  - exploration efficiency `0.5 -> 0.5`
  - corrected tokens `1076787 -> 727993`
  - changed files `2 -> 2`
  - aggregate after refresh: `95` scored comparisons, `25` unique tasks, `10` repos represented in exports, `9` clean-success to degraded-failure transitions, `9` PASS_TO_PASS regression-damage deltas
- third completed PyLint cell:
  - `pylint-dev__pylint-4970` x `comments_docstrings` x `rep_2`
  - clean and degraded both failed target tests: FAIL_TO_PASS failures `1 -> 1`
  - PASS_TO_PASS failures `0 -> 0`
  - files opened before first edit `5 -> 7`
  - exploration efficiency `0.4 -> 0.2857`
  - corrected tokens `726542 -> 1168688`
  - changed files `3 -> 2`
  - aggregate after refresh: `96` scored comparisons, `25` unique tasks, `10` repos represented in exports, `9` clean-success to degraded-failure transitions, `9` PASS_TO_PASS regression-damage deltas
- fourth completed PyLint cell:
  - `pylint-dev__pylint-4970` x `remove_tests` x `rep_3`
  - clean and degraded both failed target tests: FAIL_TO_PASS failures `1 -> 1`
  - PASS_TO_PASS failures `0 -> 0`
  - files opened before first edit `3 -> 2`
  - exploration efficiency `0.6667 -> 0.5`
  - corrected tokens `826843 -> 369739`
  - changed files `2 -> 3`
  - first PyLint task is now complete across all four degradation families
  - aggregate after refresh: `97` scored comparisons, `25` unique tasks, `10` repos represented in exports, `9` clean-success to degraded-failure transitions, `9` PASS_TO_PASS regression-damage deltas
- fifth completed PyLint cell:
  - `pylint-dev__pylint-6903` x `naming` x `rep_0`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures `0 -> 0`
  - PASS_TO_PASS failures `0 -> 0`
  - files opened before first edit `3 -> 4`
  - exploration efficiency `0.6667 -> 0.5`
  - corrected tokens `300170 -> 457137`
  - changed files `1 -> 4`
  - aggregate after refresh: `98` scored comparisons, `26` unique tasks, `10` repos represented in exports, `9` clean-success to degraded-failure transitions, `9` PASS_TO_PASS regression-damage deltas
- sixth completed PyLint cell:
  - `pylint-dev__pylint-6903` x `type_hints` x `rep_1`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures `0 -> 0`
  - PASS_TO_PASS failures `0 -> 0`
  - files opened before first edit `4 -> 4`
  - exploration efficiency `0.25 -> 0.5`
  - corrected tokens `532456 -> 498061`
  - changed files `1 -> 4`
  - aggregate after refresh: `99` scored comparisons, `26` unique tasks, `10` repos represented in exports, `9` clean-success to degraded-failure transitions, `9` PASS_TO_PASS regression-damage deltas
- seventh completed PyLint cell:
  - `pylint-dev__pylint-6903` x `comments_docstrings` x `rep_2`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures `0 -> 0`
  - PASS_TO_PASS failures `0 -> 0`
  - files opened before first edit `5 -> 4`
  - exploration efficiency `0.4 -> 0.5`
  - corrected tokens `426574 -> 638537`
  - changed files `1 -> 4`
  - aggregate after refresh: `100` scored comparisons, `26` unique tasks, `10` repos represented in exports, `9` clean-success to degraded-failure transitions, `9` PASS_TO_PASS regression-damage deltas
- eighth completed PyLint cell:
  - `pylint-dev__pylint-6903` x `remove_tests` x `rep_3`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures `0 -> 0`
  - PASS_TO_PASS failures `0 -> 0`
  - files opened before first edit `3 -> 5`
  - exploration efficiency `0.6667 -> 0.2`
  - corrected tokens `668400 -> 489210`
  - changed files `2 -> 4`
  - second PyLint task is now complete across all four degradation families
  - aggregate after refresh: `101` scored comparisons, `26` unique tasks, `10` repos represented in exports, `9` clean-success to degraded-failure transitions, `9` PASS_TO_PASS regression-damage deltas
- ninth completed PyLint cell:
  - `pylint-dev__pylint-4604` x `naming` x `rep_0`
  - clean and degraded both failed target tests: FAIL_TO_PASS failures `21 -> 21`
  - PASS_TO_PASS failures `0 -> 0`
  - files opened before first edit `4 -> 5`
  - exploration efficiency `0.25 -> 0.2`
  - corrected tokens `599032 -> 915659`
  - changed files `2 -> 3`
  - aggregate after refresh: `102` scored comparisons, `27` unique tasks, `10` repos represented in exports, `9` clean-success to degraded-failure transitions, `9` PASS_TO_PASS regression-damage deltas
- tenth completed PyLint cell:
  - `pylint-dev__pylint-4604` x `type_hints` x `rep_1`
  - clean and degraded both failed target tests: FAIL_TO_PASS failures `21 -> 21`
  - PASS_TO_PASS failures `0 -> 0`
  - files opened before first edit `5 -> 3`
  - exploration efficiency `0.4 -> 0.3333`
  - corrected tokens `910022 -> 366378`
  - changed files `2 -> 2`
  - aggregate after refresh: `103` scored comparisons, `27` unique tasks, `10` repos represented in exports, `9` clean-success to degraded-failure transitions, `9` PASS_TO_PASS regression-damage deltas
- eleventh completed PyLint cell:
  - `pylint-dev__pylint-4604` x `comments_docstrings` x `rep_2`
  - clean and degraded both failed target tests: FAIL_TO_PASS failures `21 -> 21`
  - PASS_TO_PASS failures `0 -> 0`
  - files opened before first edit `2 -> 3`
  - exploration efficiency `0.5 -> 0.3333`
  - corrected tokens `512551 -> 546094`
  - changed files `2 -> 4`
  - aggregate after refresh: `104` scored comparisons, `27` unique tasks, `10` repos represented in exports, `9` clean-success to degraded-failure transitions, `9` PASS_TO_PASS regression-damage deltas
- twelfth completed PyLint cell:
  - `pylint-dev__pylint-4604` x `remove_tests` x `rep_3`
  - clean and degraded both failed target tests: FAIL_TO_PASS failures `21 -> 21`
  - PASS_TO_PASS failures `0 -> 0`
  - files opened before first edit `4 -> 3`
  - exploration efficiency `0.25 -> 0.3333`
  - corrected tokens `396669 -> 441524`
  - changed files `2 -> 3`
  - third PyLint task is now complete across all four degradation families
  - `pylint-dev/pylint` is now complete across the selected `3 tasks x 4 degradations`; full-repo count is `8/10`
  - aggregate after refresh: `105` scored comparisons, `27` unique tasks, `10` repos represented in exports, `9` clean-success to degraded-failure transitions, `9` PASS_TO_PASS regression-damage deltas

## Astropy Recheck 2026-04-28

- attempted compact Astropy screen after PyLint:
  - `astropy__astropy-14365`
  - `astropy__astropy-14182`
  - `astropy__astropy-14539`
- `astropy__astropy-14365` failed during host-local editable install before gold preflight:
  - build reached the `astropy/wcs` C-extension stack
  - `/usr/bin/cc` failed in `astropy/wcs/src/wcslib_celprm_wrap.c`
- decision: Astropy remains blocked for this host-local lane; continue with scikit-learn as the next full-repo candidate despite known build cost.

## Scikit-Learn Strict Matrix Restart 2026-04-28

- completed `scikit-learn__scikit-learn-25232` x `type_hints` x `rep_1`
  - clean and degraded both passed
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - corrected total tokens moved `960574 -> 953945`
  - changed files stayed `2 -> 2`
  - exploration efficiency moved `1.0 -> 0.6667`
  - aggregate after refresh: `106` scored comparisons, `27` unique tasks, `10` repos represented in exports, `9` clean-success to degraded-failure transitions, `9` PASS_TO_PASS regression-damage deltas
- strict sklearn full-repo progress:
  - `scikit-learn__scikit-learn-25232`: `2/4` cells complete
  - `scikit-learn__scikit-learn-25931`: `0/4` cells complete
  - `scikit-learn__scikit-learn-26194`: supporting legacy cells exist, strict current-family cells still pending
- full-repo count remains `8/10`.
- next cell: `scikit-learn__scikit-learn-25232` x `comments_docstrings` x `rep_2`

## Scikit-Learn 25232 Comments/Docstrings 2026-04-28

- completed `scikit-learn__scikit-learn-25232` x `comments_docstrings` x `rep_2`
  - clean and degraded both passed
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - corrected total tokens moved `840823 -> 882581`
  - changed files stayed `2 -> 2`
  - exploration efficiency stayed `0.6667 -> 0.6667`
  - degraded execution had one failed targeted pytest command before recovering with a broader passing test run
  - aggregate after refresh: `107` scored comparisons, `27` unique tasks, `10` repos represented in exports, `9` clean-success to degraded-failure transitions, `9` PASS_TO_PASS regression-damage deltas
- strict sklearn full-repo progress:
  - `scikit-learn__scikit-learn-25232`: `3/4` cells complete
  - `scikit-learn__scikit-learn-25931`: `0/4` cells complete
  - `scikit-learn__scikit-learn-26194`: supporting legacy cells exist, strict current-family cells still pending
- full-repo count remains `8/10`.
- next cell: `scikit-learn__scikit-learn-25232` x `remove_tests` x `rep_3`

## Why `pytest-dev__pytest-7432` Was Eligible

- Verified SWE-bench task with a compact Python surface:
  - source file: `src/_pytest/skipping.py`
  - changed test file: `testing/test_skipping.py`
- official oracle surface is strong enough for pilot scoring:
  - `1` FAIL_TO_PASS target
  - `77` PASS_TO_PASS tests
- the task supports at least two degradation types without custom mining:
  - `comments_docstrings`
  - `remove_tests`
- the bug is localized enough that changed-file and exploration metrics are interpretable.

## Efficiency Metrics

- `files_opened_before_first_edit`
  - count of unique repo files Codex opened before the first detected edit event in the JSONL log
- `opened_files_before_first_edit`
  - the concrete ordered file list behind that count
- `relevant_files_opened`
  - opened files that ended up in the final changed-file set for that run
- `dead_end_file_opens`
  - opened files before first edit that were not in the final changed-file set
- `exploration_efficiency`
  - `relevant_files_opened / files_opened_before_first_edit`
- token totals
  - corrected on 2026-04-26 to `input_tokens + output_tokens` from the terminal `turn.completed` event
  - `cached_input_tokens` is retained as a diagnostic field but is not added because it is a subset of input usage
  - older narrative sections below may mention pre-correction token totals; use the JSON artifacts or `docs/rq1_token_metric_correction_2026-04-26.md` for current token numbers

## Numeric Deltas

### `comments_docstrings` on `pytest-dev__pytest-7432`

- rep_1
  - clean: `files_opened=3`, `exploration_efficiency=1.0`, `total_tokens=1161445`
  - degraded: `files_opened=3`, `exploration_efficiency=0.6667`, `total_tokens=1316933`
  - delta: `files_opened=0`, `exploration_efficiency=-0.3333`, `total_tokens=+155488`
- rep_2
  - clean: `files_opened=3`, `exploration_efficiency=1.0`, `total_tokens=756447`
  - degraded: `files_opened=3`, `exploration_efficiency=0.6667`, `total_tokens=825095`
  - delta: `files_opened=0`, `exploration_efficiency=-0.3333`, `total_tokens=+68648`
- oracle outcome across both reps
  - clean and degraded both achieved `1/1` FAIL_TO_PASS and `77/77` PASS_TO_PASS
- practical interpretation
  - no task-success drop yet
  - consistent degradation in early exploration quality

### `comments_docstrings` on `scikit-learn__scikit-learn-26194`

- rep_0
  - clean: `files_opened=3`, `exploration_efficiency=0.6667`
  - degraded: `files_opened=2`, `exploration_efficiency=1.0`
  - delta: `files_opened=-1`, `exploration_efficiency=+0.3333`
- rep_1
  - clean: `files_opened=2`, `exploration_efficiency=1.0`, `total_tokens=884896`
  - degraded: `files_opened=2`, `exploration_efficiency=1.0`, `total_tokens=999973`
  - delta: `files_opened=0`, `exploration_efficiency=0.0`, `total_tokens=+115077`
- oracle outcome
  - clean and degraded both achieved `2/2` FAIL_TO_PASS and `186/186` PASS_TO_PASS in `rep_0` and `rep_1`
- practical interpretation
  - the second task is now oracle-backed and runnable end to end
  - neither sklearn replication reduced task success
  - the first sklearn replication favored degraded exploration, but the second converged to parity
  - the degraded run changed one extra nearby docs file only in `rep_0`; in `rep_1` both sides changed the same two files

### `remove_tests` on `pytest-dev__pytest-7432`

- rep_3
  - clean: `files_opened=3`, `exploration_efficiency=0.6667`, `total_tokens=860647`
  - degraded: `files_opened=2`, `exploration_efficiency=1.0`, `total_tokens=434730`
  - delta: `files_opened=-1`, `exploration_efficiency=+0.3333`, `total_tokens=-425917`
- rep_4
  - clean: `files_opened=3`, `exploration_efficiency=0.6667`, `total_tokens=537137`
  - degraded: `files_opened=3`, `exploration_efficiency=0.6667`, `total_tokens=572143`
  - delta: `files_opened=0`, `exploration_efficiency=0.0`, `total_tokens=+35006`
- oracle outcome
  - clean and degraded both achieved `1/1` FAIL_TO_PASS and `77/77` PASS_TO_PASS in `rep_3` and `rep_4`
- practical interpretation
  - deleting `testing/test_skipping.py` did not break task success across two replications
  - the degraded run consistently pivoted its regression toward `testing/test_terminal.py`
  - the efficiency direction was not stable across replications, so the current signal is a stable strategy shift rather than a stable efficiency change

### `comments_docstrings` on `pallets__flask-5014`

- rep_0
  - clean: `files_opened=4`, `exploration_efficiency=0.5`
  - degraded: `files_opened=2`, `exploration_efficiency=1.0`
  - delta: `files_opened=-2`, `exploration_efficiency=+0.5`
- oracle outcome
  - clean and degraded both achieved `1/1` FAIL_TO_PASS and `59/59` PASS_TO_PASS
- practical interpretation
  - Flask is now a real third oracle-backed repo, not just a selection note
  - this first Flask replication again showed no task-success drop
  - like sklearn and unlike pytest, the degraded run was more efficient before the first edit
  - the degraded run also implemented a narrower fix than clean while still passing the oracle

### `remove_tests` on `pallets__flask-5014`

- rep_1
  - clean: `files_opened=2`, `exploration_efficiency=1.0`
  - degraded: `files_opened=4`, `exploration_efficiency=0.25`
  - delta: `files_opened=+2`, `exploration_efficiency=-0.75`
- rep_2
  - clean: `files_opened=2`, `exploration_efficiency=1.0`, `total_tokens=536631`
  - degraded: `files_opened=3`, `exploration_efficiency=0.6667`, `total_tokens=564830`
  - delta: `files_opened=+1`, `exploration_efficiency=-0.3333`, `total_tokens=+28199`
- oracle outcome
  - clean and degraded both achieved `1/1` FAIL_TO_PASS and `59/59` PASS_TO_PASS in `rep_1` and `rep_2`
- practical interpretation
  - deleting `tests/test_blueprints.py` did not break task success
  - the degraded run relocated visible regression coverage to `tests/test_basic.py` in both replications
  - the exploration penalty replicated directionally, but with a smaller magnitude in `rep_2`
  - the stable signal is redirected test strategy and degraded exploration cost, not oracle failure

### `remove_tests` on `scikit-learn__scikit-learn-26194`

- rep_2
  - clean: `files_opened=4`, `exploration_efficiency=0.5`, `total_tokens=1861426`
  - degraded: `files_opened=4`, `exploration_efficiency=0.5`, `total_tokens=3729619`
  - delta: `files_opened=0`, `exploration_efficiency=0.0`, `total_tokens=+1868193`
- oracle outcome
  - clean and degraded both achieved `2/2` FAIL_TO_PASS and `186/186` PASS_TO_PASS
- practical interpretation
  - deleting `sklearn/metrics/tests/test_ranking.py` did not break oracle task success
  - the degraded run relocated visible regression coverage to `sklearn/metrics/tests/test_common.py`
  - unlike Flask remove-tests, the exploration signal landed at parity rather than a penalty, but degraded used substantially more tokens
  - clean visible validation of the full ranking file still had two stale failures, so the official oracle is the authoritative score for this cell

### `type_hints` on `pytest-dev__pytest-7432`

- rep_5
  - clean: `files_opened=3`, `exploration_efficiency=0.6667`, `total_tokens=670835`
  - degraded: `files_opened=2`, `exploration_efficiency=1.0`, `total_tokens=583152`
  - delta: `files_opened=-1`, `exploration_efficiency=+0.3333`, `total_tokens=-87683`
- oracle outcome
  - clean and degraded both achieved `1/1` FAIL_TO_PASS and `77/77` PASS_TO_PASS
- practical interpretation
  - stripping annotations did not reduce task success on this pytest task
  - unlike the original `comments_docstrings` pytest signal, the annotation-stripped run was more direct and cheaper

### `naming` on `pytest-dev__pytest-7432`

- rep_6
  - clean: `files_opened=4`, `exploration_efficiency=0.5`, `total_tokens=756952`
  - degraded: `files_opened=2`, `exploration_efficiency=1.0`, `total_tokens=854236`
  - delta: `files_opened=-2`, `exploration_efficiency=+0.5`, `total_tokens=+97284`
- oracle outcome
  - clean and degraded both achieved `1/1` FAIL_TO_PASS and `77/77` PASS_TO_PASS
- practical interpretation
  - identifier obfuscation increased token cost but did not damage official oracle success
  - on this task, naming was a compensation-cost signal rather than a solve-rate signal

## Current Matrix Readout

- completed cells:
  - task `pytest-dev__pytest-7432` x `comments_docstrings` x `rep_1`
  - task `pytest-dev__pytest-7432` x `comments_docstrings` x `rep_2`
  - task `scikit-learn__scikit-learn-26194` x `comments_docstrings` x `rep_0`
  - task `scikit-learn__scikit-learn-26194` x `comments_docstrings` x `rep_1`
  - task `scikit-learn__scikit-learn-26194` x `remove_tests` x `rep_2`
  - task `pallets__flask-5014` x `comments_docstrings` x `rep_0`
  - task `pytest-dev__pytest-7432` x `remove_tests` x `rep_3`
  - task `pytest-dev__pytest-7432` x `remove_tests` x `rep_4`
  - task `pytest-dev__pytest-7432` x `type_hints` x `rep_5`
  - task `pytest-dev__pytest-7432` x `naming` x `rep_6`
  - task `pallets__flask-5014` x `remove_tests` x `rep_1`
  - task `pallets__flask-5014` x `remove_tests` x `rep_2`
- current recommendation
  - the current pilot evidence base has `12` oracle-backed paired replications across `3` repos, `3` tasks, and all `4` degradation families
  - the first pytest PR now has every current degradation represented
  - Flask `remove_tests` now has a directionally replicated exploration penalty
  - a reasonable next proper-snapshot target is selecting two more pytest tasks and two more scikit-learn tasks with nonzero type-hint signal, while using Sphinx as the third proper-matrix repo
  - keep the in-place oracle replay path unless it causes a concrete validity issue
# Latest RQ1 Snapshot Note

For teammate-facing current counts and conclusions, use:

- `docs/rq1_initial_findings_for_teammate_2026-04-23.md`

Current completed evidence base:

- `57` oracle-backed paired clean-vs-degraded cells
- `6` repos with completed Codex cells
- `15` unique SWE-bench Verified PRs
- all `4` degradation families represented
- `5/57` clean-success to degraded-failure transitions
- `5/57` PASS_TO_PASS regression-damage deltas

Phase 1 full-repo checkpoint:

- `pytest-dev/pytest`: complete across selected `3 PRs x 4 degradations`
- `sphinx-doc/sphinx`: complete across selected `3 PRs x 4 degradations`
- `scikit-learn/scikit-learn`: valid supporting cells exist, but the repo is now deprioritized for the immediate full-repo checkpoint because each cell requires slow clean/degraded editable C-extension builds and `scikit-learn__scikit-learn-26194` is not eligible for all four degradations
- `pydata/xarray`: complete across selected `3 PRs x 4 degradations`; all three xarray naming cells caused official degraded failures
- `sympy/sympy`: complete across selected `3 PRs x 4 degradations`; two of three Sympy naming cells caused official degraded failures
- current count: `4` fully complete repos
- next action: screen and run a fifth full repo; Django is the first candidate because it has a large Verified task pool and no sklearn-style C-extension build path

Newest completed cell:

- `sympy__sympy-12419` x `type_hints` x `rep_1`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit stayed `2 -> 2`
  - exploration efficiency stayed `1.0 -> 1.0`
  - corrected total tokens moved `1927531 -> 2052480`
  - changed files stayed `4 -> 4`
  - current read: outcome-stable low-signal type-hints cell; retained for matrix completeness
- `sympy__sympy-12419` x `remove_tests` x `rep_3`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `2 -> 3`
  - exploration efficiency moved `1.0 -> 0.3333`
  - corrected total tokens moved `692285 -> 868570`
  - changed files moved `2 -> 3`
  - current read: remove-tests preserved official outcome but degraded early orientation and added patch breadth
- `sympy__sympy-12419` x `comments_docstrings` x `rep_2`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `2 -> 3`
  - exploration efficiency moved `0.5 -> 0.6667`
  - corrected total tokens moved `1116747 -> 2123692`
  - changed files moved `3 -> 4`
  - current read: comments/docstrings preserved outcome but substantially increased degraded cost and validation work
- `sympy__sympy-12419` x `naming` x `rep_0`
  - clean passed official SWE-bench tests; degraded failed official SWE-bench tests
  - FAIL_TO_PASS failures moved `0 -> 1`
  - PASS_TO_PASS failures moved `0 -> 7`
  - files opened before first edit moved `3 -> 4`
  - exploration efficiency moved `0.6667 -> 0.5`
  - corrected total tokens moved `2124867 -> 2327688`
  - changed files moved `4 -> 8`
  - current read: fifth transition overall and second Sympy naming transition; naming damage now clearly crosses repos
- `sympy__sympy-12096` x `type_hints` x `rep_1`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `2 -> 5`
  - exploration efficiency moved `0.5 -> 0.2`
  - corrected total tokens moved `846266 -> 537162`
  - changed files stayed `2 -> 2`
  - current read: outcome-stable low-signal type-hints cell; degraded did more early wandering but used fewer total tokens
- `sympy__sympy-12096` x `remove_tests` x `rep_3`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `7 -> 5`
  - exploration efficiency moved `0.2857 -> 0.2`
  - corrected total tokens moved `876074 -> 1015008`
  - changed files moved `2 -> 3`
  - current read: remove-tests preserved official outcome but added one degraded changed file and token cost
- `sympy__sympy-12096` x `comments_docstrings` x `rep_2`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `5 -> 3`
  - exploration efficiency moved `0.2 -> 0.3333`
  - corrected total tokens moved `532998 -> 1076892`
  - changed files moved `2 -> 3`
  - current read: comments/docstrings was outcome-stable but cost-heavy on this task
- `sympy__sympy-12096` x `naming` x `rep_0`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `4 -> 7`
  - exploration efficiency moved `0.25 -> 0.2857`
  - corrected total tokens moved `739131 -> 1563817`
  - changed files moved `2 -> 8`
  - current read: naming did not break official outcome here, but it produced the broadest degraded patch shape and largest token cost in this Sympy task
- `sympy__sympy-11618` x `type_hints` x `rep_1`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit stayed `2 -> 2`
  - exploration efficiency stayed `1.0 -> 1.0`
  - corrected total tokens moved `501705 -> 334294`
  - changed files stayed `2 -> 2`
  - current read: outcome-stable low-signal Sympy type-hints cell, included for matrix completeness
- `sympy__sympy-11618` x `remove_tests` x `rep_3`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `2 -> 1`
  - exploration efficiency stayed `1.0 -> 1.0`
  - corrected total tokens moved `592535 -> 1081342`
  - changed files stayed `2 -> 2`
  - current read: remove-tests did not damage official outcome but materially increased degraded token cost
- `sympy__sympy-11618` x `comments_docstrings` x `rep_2`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit stayed `3 -> 3`
  - exploration efficiency stayed `0.6667 -> 0.6667`
  - corrected total tokens moved `651001 -> 644603`
  - changed files stayed `2 -> 2`
  - current read: comments/docstrings preserved official outcome and patch shape on this Sympy task
- `sympy__sympy-11618` x `naming` x `rep_0`
  - clean passed official SWE-bench tests; degraded failed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures moved `0 -> 2`
  - files opened before first edit stayed `3 -> 3`
  - exploration efficiency stayed `0.6667 -> 0.6667`
  - corrected total tokens moved `526554 -> 521011`
  - changed files moved `2 -> 5`
  - current read: fourth transition overall and first non-xarray naming transition; naming damage now replicates across repos
- `pydata__xarray-4966` x `remove_tests` x `rep_3`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `4 -> 5`
  - exploration efficiency moved `0.5 -> 0.2`
  - corrected total tokens moved `516662 -> 515154`
  - changed files moved `2 -> 3`
  - current read: xarray is now complete across all selected `3 PRs x 4 degradations`; naming is the only xarray degradation with outcome damage
- `pydata__xarray-4966` x `comments_docstrings` x `rep_2`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `4 -> 5`
  - exploration efficiency moved `0.5 -> 0.4`
  - corrected total tokens moved `459782 -> 555215`
  - changed files stayed `2 -> 2`
  - current read: comments/docstrings remains process/cost-visible but not outcome-visible on xarray
- `pydata__xarray-4966` x `type_hints` x `rep_1`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit stayed `4 -> 4`
  - exploration efficiency stayed `0.5 -> 0.5`
  - corrected total tokens moved `454613 -> 614080`
  - changed files stayed `2 -> 2`
  - current read: type-hints remains outcome-stable on xarray, contrasting with repeated naming failures
- `pydata__xarray-4966` x `naming` x `rep_0`
  - clean passed official SWE-bench tests; degraded failed official SWE-bench tests
  - FAIL_TO_PASS failures moved `0 -> 4`
  - PASS_TO_PASS failures moved `0 -> 17`
  - files opened before first edit stayed `5 -> 5`
  - exploration efficiency stayed `0.4 -> 0.4`
  - corrected total tokens moved `489466 -> 960559`
  - changed files moved `2 -> 4`
  - current read: third repeated xarray naming transition; strongest xarray failure so far because degraded lost the target tests and damaged seventeen PASS_TO_PASS tests
- `pydata__xarray-4629` x `remove_tests` x `rep_3`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `2 -> 1`
  - exploration efficiency stayed `1.0 -> 1.0`
  - corrected total tokens moved `278069 -> 268874`
  - changed files stayed `2 -> 2`
  - current read: `pydata__xarray-4629` is complete across all four degradations; only naming caused official regression damage on this task
- `pydata__xarray-4629` x `comments_docstrings` x `rep_2`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `2 -> 3`
  - exploration efficiency moved `1.0 -> 0.6667`
  - corrected total tokens moved `172345 -> 390754`
  - changed files stayed `2 -> 2`
  - RQ2 phase note: degraded bootstrap commands moved `5 -> 11`, including one failed bootstrap test command before first edit
  - current read: comments/docstrings stripping is process- and cost-visible here, but not outcome-visible
- `pydata__xarray-4629` x `type_hints` x `rep_1`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit stayed `2 -> 2`
  - exploration efficiency stayed `1.0 -> 1.0`
  - corrected total tokens moved `197461 -> 256233`
  - changed files stayed `2 -> 2`
  - RQ2 phase note: degraded execution commands moved `6 -> 5`; execution test commands moved `2 -> 1`, with no failed execution test commands
  - current read: type-hint stripping again preserved outcome while xarray naming remains damaging
- `pydata__xarray-4629` x `naming` x `rep_0`
  - clean passed official SWE-bench tests; degraded failed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures moved `0 -> 1`
  - files opened before first edit stayed `2 -> 2`
  - exploration efficiency stayed `1.0 -> 1.0`
  - corrected total tokens moved `204133 -> 398155`
  - changed files stayed `2 -> 2`
  - RQ2 phase note: degraded execution commands moved `3 -> 5`; execution test commands moved `1 -> 2`, with no failed execution test commands
  - current read: repeated xarray naming damage; this case is semantic/local rather than broad over-editing
- `pydata__xarray-3677` x `remove_tests` x `rep_3`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `4 -> 5`
  - exploration efficiency moved `0.5 -> 0.2`
  - corrected total tokens moved `327266 -> 435829`
  - changed files moved `2 -> 3`
  - RQ2 phase note: degraded bootstrap commands moved `11 -> 17`; execution test commands stayed `2 -> 2`, with no failed execution test commands on either side
  - current read: `pydata__xarray-3677` is complete across all four degradations; only naming caused official outcome and PASS_TO_PASS damage on this task
- `pydata__xarray-3677` x `comments_docstrings` x `rep_2`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit stayed `3 -> 3`
  - exploration efficiency stayed `0.6667 -> 0.6667`
  - corrected total tokens moved `426628 -> 547441`
  - changed files moved `2 -> 3`
  - RQ2 phase note: degraded bootstrap commands moved `12 -> 9`; degraded execution test commands moved `1 -> 2`, with no failed execution test commands on either side
  - current read: comments/docstrings stripping on xarray is cost-visible but not outcome-visible
- `pydata__xarray-3677` x `type_hints` x `rep_1`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `5 -> 4`
  - exploration efficiency moved `0.4 -> 0.5`
  - corrected total tokens moved `508335 -> 358785`
  - changed files moved `2 -> 3`
  - RQ2 phase note: degraded bootstrap commands moved `16 -> 12`; execution test commands stayed `2 -> 2`, with no failed execution test commands on either side
  - current read: type-hint stripping did not reproduce the xarray naming failure and was cheaper on this cell
- `pydata__xarray-3677` x `naming` x `rep_0`
  - clean passed official SWE-bench tests; degraded failed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures moved `0 -> 8`
  - files opened before first edit moved `3 -> 5`
  - exploration efficiency moved `0.6667 -> 0.4`
  - corrected total tokens moved `413059 -> 684397`
  - changed files moved `2 -> 16`
  - RQ2 phase note: degraded bootstrap commands moved `10 -> 15`; degraded execution had one failed full-file pytest command while clean had none
  - current read: first outcome transition and first regression-damage delta; naming degradation preserved the target fix but induced broad over-editing and PASS_TO_PASS damage
- `scikit-learn__scikit-learn-25232` x `naming` x `rep_0`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit stayed `3 -> 3`
  - exploration efficiency stayed `0.6667 -> 0.6667`
  - corrected total tokens moved `827002 -> 977987`
  - RQ2 phase note: degraded bootstrap command count moved `16 -> 20`; degraded execution had two failed validation commands before official oracle replay passed
  - current read: sklearn naming degradation is not an outcome or early-search penalty on this cell, but it is a token and validation-noise penalty
- `sphinx-doc__sphinx-9673` x `remove_tests` x `rep_3`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `4 -> 9`
  - exploration efficiency moved `0.5 -> 0.1111`
  - corrected total tokens moved `403192 -> 447693`
  - RQ2 phase note: degraded bootstrap commands moved `9 -> 12`; degraded execution had one failed test command before the successful `HOME=/tmp` rerun
  - current read: Sphinx is now fully complete across the selected `3 PRs x 4 degradations`, making it the second complete Phase 1 repo after pytest
- `sphinx-doc__sphinx-9673` x `comments_docstrings` x `rep_2`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `3 -> 6`
  - exploration efficiency moved `0.6667 -> 0.3333`
  - corrected total tokens moved `260101 -> 326402`
  - RQ2 phase note: degraded bootstrap command count moved `6 -> 12` while execution command and test counts stayed even
  - current read: comments/docstrings stripping on `sphinx-9673` is a clear bootstrap-search and token-cost signal without official outcome damage
- `sphinx-doc__sphinx-9673` x `type_hints` x `rep_1`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `4 -> 5`
  - exploration efficiency moved `0.5 -> 0.4`
  - corrected total tokens moved `718661 -> 377250`
  - RQ2 phase note: degraded execution test commands moved `7 -> 2`, with failed execution test commands moving `3 -> 0`
  - current read: type-hint stripping on `sphinx-9673` worsens early exploration but reduces execution validation effort and total token use
- `sphinx-doc__sphinx-9673` x `naming` x `rep_0`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `6 -> 3`
  - exploration efficiency moved `0.3333 -> 0.6667`
  - corrected total tokens moved `392263 -> 371918`
  - current read: first `sphinx-9673` cell preserves official outcome while the naming-degraded run is more direct and slightly cheaper
- `sphinx-doc__sphinx-10449` x `type_hints` x `rep_1`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit stayed `4 -> 4`
  - exploration efficiency stayed `0.5 -> 0.5`
  - corrected total tokens moved `554643 -> 864539`
  - RQ2 phase note: degraded execution test commands moved `2 -> 4`, with one failed validation command before final success
  - current read: type-hint stripping on the second Sphinx PR is mostly a token/validation-effort signal rather than a bootstrap-search or outcome signal
- `sphinx-doc__sphinx-10449` x `comments_docstrings` x `rep_2`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - degraded files opened before first edit moved `5 -> 6`
  - degraded exploration efficiency moved `0.4 -> 0.3333`
  - corrected total tokens moved `387291 -> 558719`
  - current read: comments/docstrings stripping on the second Sphinx PR is process-visible but not outcome-visible
- `sphinx-doc__sphinx-10449` x `remove_tests` x `rep_3`
  - clean and degraded both passed official SWE-bench tests
  - degraded exploration efficiency moved `0.5 -> 0.1667`
  - degraded token use moved `374935 -> 762784`
  - current read: remove-tests on the second Sphinx PR preserves outcome while increasing search and token cost
- `sphinx-doc__sphinx-10449` x `naming` x `rep_0`
  - clean and degraded both passed official SWE-bench tests
  - degraded exploration efficiency moved `0.4 -> 0.5`
  - degraded token use moved `781838 -> 1814093`
  - current read: second Sphinx naming cell again shows outcome preservation with substantial token-cost increase
- `sphinx-doc__sphinx-9367` x `comments_docstrings` x `rep_2`
  - clean and degraded both passed official SWE-bench tests
  - exploration efficiency stayed at `1.0`
  - degraded token use moved `466373 -> 571487`
  - current read: comments/docstrings stripping on this Sphinx task is cost-visible but not outcome-visible
- `sphinx-doc__sphinx-9367` is now complete across all four degradation families:
  - `naming`
  - `type_hints`
  - `comments_docstrings`
  - `remove_tests`
  - all four clean/degraded pairs passed official SWE-bench tests

Integrity check:

- comparison artifacts checked: `25`
- schema/delta/metric consistency errors: `0`
- focused harness tests: `17 passed, 1 warning`
- `sphinx-doc__sphinx-9367` x `type_hints` x `rep_1`
  - clean and degraded both passed official SWE-bench tests
  - exploration efficiency stayed at `1.0`
  - degraded token use moved `318475 -> 606918`
  - current read: type-hint stripping on this Sphinx task is a cost signal, not a success or search-quality failure
- `sphinx-doc__sphinx-9367` x `remove_tests` x `rep_3`
  - clean and degraded both passed official SWE-bench tests
  - degraded exploration efficiency stayed at `1.0`
  - degraded files opened before first edit moved `2 -> 1`
  - degraded token use moved `404904 -> 498416`
  - current read: first Sphinx remove-tests cell did not harm solve rate or exploration efficiency, but did increase token cost
- `sphinx-doc__sphinx-9367` x `naming` x `rep_0`
  - clean and degraded both passed official SWE-bench tests
  - degraded exploration efficiency moved `1.0 -> 0.6667`
  - degraded token use moved `320633 -> 586173`
  - current read: first Sphinx naming cell matches the behavioral-sensitivity pattern without solve-rate damage

This file still contains the historical running matrix notes below.

## Scikit-Learn 25232 Remove-Tests 2026-04-28

- `scikit-learn__scikit-learn-25232` x `remove_tests` x `rep_3`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `3 -> 5`
  - exploration efficiency moved `0.6667 -> 0.2`
  - corrected total tokens moved `1148003 -> 706913`
  - changed files moved `2 -> 3`
  - RQ2 phase note: degraded bootstrap had one failed command and more dead-end pre-edit file opens; execution test commands stayed successful
  - current read: remove-tests preserved official outcome and reduced corrected token use on this task, but it increased search diffusion and patch breadth
- `scikit-learn__scikit-learn-25232` is now complete across all four strict degradation families:
  - `naming`
  - `type_hints`
  - `comments_docstrings`
  - `remove_tests`
- aggregate after refresh: `108` scored comparisons, `27` tasks, `10` represented repos, `9` clean-success to degraded-failure transitions, `9` PASS_TO_PASS regression-damage deltas

## Scikit-Learn 25931 Naming 2026-04-28

- `scikit-learn__scikit-learn-25931` x `naming` x `rep_0`
  - clean passed official SWE-bench tests; degraded failed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures moved `0 -> 1`
  - files opened before first edit moved `2 -> 3`
  - exploration efficiency moved `1.0 -> 0.6667`
  - corrected total tokens moved `393707 -> 637890`
  - changed files stayed `2 -> 2`
  - RQ2 phase note: degraded execution had one failed targeted pytest command; clean had none
  - current read: tenth naming clean-success to degraded-failure transition overall, with outcome damage despite identical changed-file count
- aggregate after refresh: `109` scored comparisons, `28` tasks, `10` represented repos, `10` clean-success to degraded-failure transitions, `10` PASS_TO_PASS regression-damage deltas

## Scikit-Learn 25931 Type-Hints 2026-04-28

- `scikit-learn__scikit-learn-25931` x `type_hints` x `rep_1`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `2 -> 4`
  - exploration efficiency moved `1.0 -> 0.5`
  - corrected total tokens moved `458204 -> 422317`
  - changed files stayed `2 -> 2`
  - RQ2 phase note: degraded execution ran two successful targeted pytest commands versus one clean command, with no failed commands
  - current read: type-hints stripping preserved official outcome and patch breadth while adding two dead-end pre-edit file opens but slightly reducing corrected token use
- aggregate after refresh: `110` scored comparisons, `28` tasks, `10` represented repos, `10` clean-success to degraded-failure transitions, `10` PASS_TO_PASS regression-damage deltas

## Scikit-Learn 25931 Comments/Docstrings 2026-04-28

- `scikit-learn__scikit-learn-25931` x `comments_docstrings` x `rep_2`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit stayed `2 -> 2`
  - exploration efficiency stayed `1.0 -> 1.0`
  - corrected total tokens moved `444694 -> 703306`
  - changed files stayed `2 -> 2`
  - RQ2 phase note: degraded execution used `15` commands and `4` test commands versus clean `6` commands and `2` test commands; targeted test commands did not fail
  - current read: comments/docstrings stripping preserved official outcome and early targeting but increased corrected token use by `258612`
- aggregate after refresh: `111` scored comparisons, `28` tasks, `10` represented repos, `10` clean-success to degraded-failure transitions, `10` PASS_TO_PASS regression-damage deltas

## Scikit-Learn 25931 Remove-Tests 2026-04-28

- `scikit-learn__scikit-learn-25931` x `remove_tests` x `rep_3`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `2 -> 1`
  - exploration efficiency stayed `1.0 -> 1.0`
  - corrected total tokens moved `455760 -> 567872`
  - changed files stayed `2 -> 2`
  - RQ2 phase note: degraded execution ran more commands and edit events, but both sides had three successful test commands and no failed commands
  - current read: remove-tests preserved official outcome and patch breadth while increasing corrected token use
- `scikit-learn__scikit-learn-25931` is now complete across all four strict degradation families:
  - `naming`
  - `type_hints`
  - `comments_docstrings`
  - `remove_tests`
- aggregate after refresh: `112` scored comparisons, `28` tasks, `10` represented repos, `10` clean-success to degraded-failure transitions, `10` PASS_TO_PASS regression-damage deltas

## Scikit-Learn Third Strict Task Adjustment 2026-04-28

- `scikit-learn__scikit-learn-26194` remains supporting evidence only:
  - current profile is eligible for `comments_docstrings` and `remove_tests`, not all four degradation families
  - strict full-repo credit therefore requires a different third sklearn task
- `scikit-learn__scikit-learn-25973` was screened and selected:
  - gold preflight passed
  - all four degradation families are eligible
  - source/test surface: `sklearn/feature_selection/_sequential.py` and `sklearn/feature_selection/tests/test_sequential.py`

## Scikit-Learn 25973 Naming 2026-04-28

- `scikit-learn__scikit-learn-25973` x `naming` x `rep_0`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `6 -> 5`
  - exploration efficiency moved `0.3333 -> 0.4`
  - corrected total tokens moved `347768 -> 549894`
  - changed files stayed `2 -> 2`
  - RQ2 phase note: degraded execution had one failed targeted pytest command before the final successful full-file run
  - current read: naming preserved official outcome and patch breadth, but increased corrected token use and validation friction
- aggregate after refresh: `113` scored comparisons, `29` tasks, `10` represented repos, `10` clean-success to degraded-failure transitions, `10` PASS_TO_PASS regression-damage deltas

## Scikit-Learn 25973 Type-Hints 2026-04-28

- `scikit-learn__scikit-learn-25973` x `type_hints` x `rep_1`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `6 -> 7`
  - exploration efficiency moved `0.3333 -> 0.2857`
  - corrected total tokens moved `477202 -> 451756`
  - changed files stayed `2 -> 2`
  - RQ2 phase note: both sides had one successful validation command; degraded used fewer total commands and no failed commands
  - current read: type-hints preserved outcome and patch breadth while slightly diffusing early search but reducing corrected token use
- aggregate after refresh: `114` scored comparisons, `29` tasks, `10` represented repos, `10` clean-success to degraded-failure transitions, `10` PASS_TO_PASS regression-damage deltas

## Scikit-Learn 25973 Comments/Docstrings 2026-04-28

- `scikit-learn__scikit-learn-25973` x `comments_docstrings` x `rep_2`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `7 -> 4`
  - exploration efficiency moved `0.2857 -> 0.5`
  - corrected total tokens moved `467618 -> 521606`
  - changed files stayed `2 -> 2`
  - RQ2 phase note: degraded used fewer bootstrap/total commands and one successful validation command versus two clean validation commands
  - current read: comments/docstrings preserved outcome and patch breadth while improving early targeting but increasing corrected token use
- aggregate after refresh: `115` scored comparisons, `29` tasks, `10` represented repos, `10` clean-success to degraded-failure transitions, `10` PASS_TO_PASS regression-damage deltas

## Scikit-Learn 25973 Remove-Tests 2026-04-28

- `scikit-learn__scikit-learn-25973` x `remove_tests` x `rep_3`
  - clean and degraded both passed official SWE-bench tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `4 -> 7`
  - exploration efficiency moved `0.5 -> 0.2857`
  - corrected total tokens moved `608913 -> 980142`
  - changed files stayed `2 -> 2`
  - RQ2 phase note: degraded had more bootstrap commands, two failed bootstrap commands, and more total commands, but no failed validation commands
  - current read: remove-tests preserved outcome and patch breadth while increasing early search diffusion and corrected token use
- `scikit-learn__scikit-learn-25973` is now complete across all four strict degradation families:
  - `naming`
  - `type_hints`
  - `comments_docstrings`
  - `remove_tests`
- `scikit-learn/scikit-learn` is now the ninth fully complete repo.
- aggregate after refresh: `116` scored comparisons, `29` tasks, `10` represented repos, `9` fully complete repos, `10` clean-success to degraded-failure transitions, `10` PASS_TO_PASS regression-damage deltas

## Astropy Screening Reopened 2026-04-28

- Astropy host-local editable install blocker is now worked around by a narrow env-prep rule:
  - preinstall checkout build requirements
  - use `--no-build-isolation --no-deps` for the local editable install
  - compile historical C sources with `-std=gnu17 -Wno-error=incompatible-pointer-types`
- verification: `PYTHONPATH=. uv run --extra dev pytest tests/test_python_env.py` -> `19 passed`
- accepted Astropy task set for the tenth full repo:
  - `astropy__astropy-14365`
  - `astropy__astropy-14182`
  - `astropy__astropy-14539`
- gold preflight status:
  - `astropy__astropy-14365`: passed; `1` FAIL_TO_PASS and `8` PASS_TO_PASS targets
  - `astropy__astropy-14182`: passed; `1` FAIL_TO_PASS and `9` PASS_TO_PASS targets
  - `astropy__astropy-14539`: passed; `2` FAIL_TO_PASS and `46` PASS_TO_PASS targets
- eligibility:
  - all three tasks are eligible for `naming`, `type_hints`, `comments_docstrings`, and `remove_tests`
  - `type_hints` is low-signal for all three tasks because target surfaces have `0` annotation nodes
- next cell: `astropy__astropy-14365` x `naming` x `rep_0`

## Astropy 14365 Naming 2026-04-28

- `astropy__astropy-14365` x `naming` x `rep_0`
  - clean and degraded both failed official SWE-bench target tests
  - FAIL_TO_PASS failures stayed `1 -> 1`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit stayed `2 -> 2`
  - exploration efficiency stayed `1.0 -> 1.0`
  - corrected total tokens moved `424904 -> 182839`
  - changed files stayed `2 -> 2`
  - RQ2 phase note: clean ran one failed and one successful validation command; degraded ran one successful validation command
  - current read: baseline-hard task, not a clean-success/degraded-failure transition; naming reduced corrected token use without changing patch breadth
- aggregate after refresh: `117` scored comparisons, `30` tasks, `11` represented repos, `9` fully complete repos, `10` clean-success to degraded-failure transitions, `10` PASS_TO_PASS regression-damage deltas
- next cell completed: `astropy__astropy-14365` x `type_hints` x `rep_1`

## Astropy 14365 Type-Hints 2026-04-28

- `astropy__astropy-14365` x `type_hints` x `rep_1`
  - clean and degraded both failed official SWE-bench target tests
  - FAIL_TO_PASS failures stayed `1 -> 1`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit stayed `2 -> 2`
  - exploration efficiency stayed `1.0 -> 1.0`
  - corrected total tokens moved `247115 -> 470352`
  - changed files stayed `2 -> 2`
  - RQ2 phase note: degraded had a longer bootstrap and one failed targeted pytest command during execution; clean had one successful validation command
  - current read: low-signal type-hints matrix-completeness cell with no outcome or patch-breadth damage, but higher degraded corrected-token cost
- aggregate after refresh: `118` scored comparisons, `30` tasks, `11` represented repos, `9` fully complete repos, `10` clean-success to degraded-failure transitions, `10` PASS_TO_PASS regression-damage deltas
- Astropy tenth-repo path now has:
  - `astropy__astropy-14365`: `2/4` cells complete (`naming`, `type_hints`)
  - `astropy__astropy-14182`: `0/4` cells complete
  - `astropy__astropy-14539`: `0/4` cells complete
- next cell completed: `astropy__astropy-14365` x `comments_docstrings` x `rep_2`

## Astropy 14365 Comments/Docstrings 2026-04-28

- `astropy__astropy-14365` x `comments_docstrings` x `rep_2`
  - clean and degraded both failed official SWE-bench target tests
  - FAIL_TO_PASS failures stayed `1 -> 1`
  - PASS_TO_PASS failures moved `0 -> 8`
  - files opened before first edit stayed `2 -> 2`
  - exploration efficiency stayed `1.0 -> 1.0`
  - corrected total tokens moved `310234 -> 436992`
  - changed files stayed `2 -> 2`
  - RQ2 phase note: degraded execution ran more commands and its only targeted validation command failed
  - current read: baseline-hard target, but comments/docstrings introduced PASS_TO_PASS regression damage despite stable patch breadth and search targeting
- aggregate after refresh: `119` scored comparisons, `30` tasks, `11` represented repos, `9` fully complete repos, `10` clean-success to degraded-failure transitions, `11` PASS_TO_PASS regression-damage deltas
- Astropy tenth-repo path now has:
  - `astropy__astropy-14365`: `3/4` cells complete (`naming`, `type_hints`, `comments_docstrings`)
  - `astropy__astropy-14182`: `0/4` cells complete
  - `astropy__astropy-14539`: `0/4` cells complete
- next cell completed: `astropy__astropy-14365` x `remove_tests` x `rep_3`

## Astropy 14365 Remove-Tests 2026-04-28

- `astropy__astropy-14365` x `remove_tests` x `rep_3`
  - clean and degraded both failed official SWE-bench target tests
  - FAIL_TO_PASS failures stayed `1 -> 1`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `2 -> 3`
  - exploration efficiency moved `1.0 -> 0.3333`
  - corrected total tokens moved `293926 -> 381447`
  - changed files moved `2 -> 1`
  - RQ2 phase note: degraded had longer bootstrap and one failed fallback validation command after the target test file had been removed
  - current read: baseline-hard target; remove-tests narrowed the patch to source-only but increased token cost and dead-end pre-edit test-file opens
- `astropy__astropy-14365` is now complete across all four strict degradation families:
  - `naming`
  - `type_hints`
  - `comments_docstrings`
  - `remove_tests`
- aggregate after refresh: `120` scored comparisons, `30` tasks, `11` represented repos, `9` fully complete repos, `10` clean-success to degraded-failure transitions, `11` PASS_TO_PASS regression-damage deltas
- Astropy tenth-repo path now has:
  - `astropy__astropy-14365`: `4/4` cells complete
  - `astropy__astropy-14182`: `0/4` cells complete
  - `astropy__astropy-14539`: `0/4` cells complete
- next cell completed: `astropy__astropy-14182` x `naming` x `rep_0`

## Astropy 14182 Naming 2026-04-28

- `astropy__astropy-14182` x `naming` x `rep_0`
  - clean passed official SWE-bench target tests; degraded failed official target tests
  - FAIL_TO_PASS failures moved `0 -> 1`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `3 -> 4`
  - exploration efficiency moved `0.6667 -> 0.5`
  - corrected total tokens moved `320360 -> 631928`
  - changed files stayed `2 -> 2`
  - RQ2 phase note: degraded had longer bootstrap and one failed targeted validation command; clean validation commands both passed
  - current read: eleventh clean-success to degraded-failure transition overall and another naming outcome-damage point, with higher token cost and slightly more search diffusion
- aggregate after refresh: `121` scored comparisons, `31` tasks, `11` represented repos, `9` fully complete repos, `11` clean-success to degraded-failure transitions, `11` PASS_TO_PASS regression-damage deltas
- Astropy tenth-repo path now has:
  - `astropy__astropy-14365`: `4/4` cells complete
  - `astropy__astropy-14182`: `1/4` cells complete (`naming`)
  - `astropy__astropy-14539`: `0/4` cells complete
- next cell completed: `astropy__astropy-14182` x `type_hints` x `rep_1`

## Astropy 14182 Type-Hints 2026-04-28

- `astropy__astropy-14182` x `type_hints` x `rep_1`
  - clean and degraded both passed official SWE-bench target tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit stayed `4 -> 4`
  - exploration efficiency stayed `0.5 -> 0.5`
  - corrected total tokens moved `458188 -> 734334`
  - changed files stayed `2 -> 2`
  - RQ2 phase note: degraded used more bootstrap and execution commands, but both sides had two successful validation commands and no failed commands
  - current read: low-signal type-hints matrix-completeness cell; outcome and patch shape stayed stable, but degraded token cost increased
- aggregate after refresh: `122` scored comparisons, `31` tasks, `11` represented repos, `9` fully complete repos, `11` clean-success to degraded-failure transitions, `11` PASS_TO_PASS regression-damage deltas
- Astropy tenth-repo path now has:
  - `astropy__astropy-14365`: `4/4` cells complete
  - `astropy__astropy-14182`: `2/4` cells complete (`naming`, `type_hints`)
  - `astropy__astropy-14539`: `0/4` cells complete
- next cell completed: `astropy__astropy-14182` x `comments_docstrings` x `rep_2`

## Astropy 14182 Comments/Docstrings 2026-04-28

- `astropy__astropy-14182` x `comments_docstrings` x `rep_2`
  - clean and degraded both passed official SWE-bench target tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `4 -> 6`
  - exploration efficiency moved `0.5 -> 0.3333`
  - corrected total tokens moved `449081 -> 548341`
  - changed files stayed `2 -> 2`
  - RQ2 phase note: degraded execution used more commands and had one failed targeted pytest command before final success
  - current read: outcome-stable process/cost result; comments/docstrings increased token cost and dead-end pre-edit file opens without changing patch breadth
- aggregate after refresh: `123` scored comparisons, `31` tasks, `11` represented repos, `9` fully complete repos, `11` clean-success to degraded-failure transitions, `11` PASS_TO_PASS regression-damage deltas
- Astropy tenth-repo path now has:
  - `astropy__astropy-14365`: `4/4` cells complete
  - `astropy__astropy-14182`: `3/4` cells complete (`naming`, `type_hints`, `comments_docstrings`)
  - `astropy__astropy-14539`: `0/4` cells complete
- next cell completed: `astropy__astropy-14182` x `remove_tests` x `rep_3`

## Astropy 14182 Remove-Tests 2026-04-28

- `astropy__astropy-14182` x `remove_tests` x `rep_3`
  - clean and degraded both passed official SWE-bench target tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `4 -> 5`
  - exploration efficiency moved `0.5 -> 0.2`
  - corrected total tokens moved `320309 -> 507518`
  - changed files stayed `2 -> 2`
  - RQ2 phase note: degraded ran six validation commands and had one failed validation command; clean had one successful validation command
  - current read: outcome-stable remove-tests result with changed test-side patch shape because `test_rst.py` was removed and the degraded run edited `test_fixedwidth.py`
- `astropy__astropy-14182` is now complete across all four strict degradation families:
  - `naming`
  - `type_hints`
  - `comments_docstrings`
  - `remove_tests`
- aggregate after refresh: `124` scored comparisons, `31` tasks, `11` represented repos, `9` fully complete repos, `11` clean-success to degraded-failure transitions, `11` PASS_TO_PASS regression-damage deltas
- Astropy tenth-repo path now has:
  - `astropy__astropy-14365`: `4/4` cells complete
  - `astropy__astropy-14182`: `4/4` cells complete
  - `astropy__astropy-14539`: `0/4` cells complete
- next cell completed: `astropy__astropy-14539` x `naming` x `rep_0`

## Astropy 14539 Naming 2026-04-28

- removed stale generated `runs/astropy__astropy-14539/codex-cli/clean/rep_0` from an incomplete April 22 partial before rerunning this cell
- `astropy__astropy-14539` x `naming` x `rep_0`
  - clean and degraded both passed official SWE-bench target tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit moved `2 -> 3`
  - exploration efficiency moved `1.0 -> 0.6667`
  - corrected total tokens moved `296989 -> 1620500`
  - changed files stayed `2 -> 2`
  - RQ2 phase note: degraded execution used `22` commands and four validation commands, with one failed validation command before final success
  - current read: outcome-stable naming cell with very high degraded token cost and heavier execution loop, but stable patch breadth
- aggregate after refresh: `125` scored comparisons, `32` tasks, `11` represented repos, `9` fully complete repos, `11` clean-success to degraded-failure transitions, `11` PASS_TO_PASS regression-damage deltas
- Astropy tenth-repo path now has:
  - `astropy__astropy-14365`: `4/4` cells complete
  - `astropy__astropy-14182`: `4/4` cells complete
  - `astropy__astropy-14539`: `1/4` cells complete (`naming`)
- next cell completed: `astropy__astropy-14539` x `type_hints` x `rep_1`

## Astropy 14539 Type-Hints 2026-04-28

- `astropy__astropy-14539` x `type_hints` x `rep_1`
  - clean and degraded both passed official SWE-bench target tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit stayed `2 -> 2`
  - exploration efficiency stayed `1.0 -> 1.0`
  - corrected total tokens moved `482719 -> 378447`
  - changed files stayed `2 -> 2`
  - RQ2 phase note: degraded used fewer total commands; both sides ran two successful validation commands
  - current read: low-signal type-hints cell with stable outcome, patch shape, and early search; degraded token cost was lower
- aggregate after refresh: `126` scored comparisons, `32` tasks, `11` represented repos, `9` fully complete repos, `11` clean-success to degraded-failure transitions, `11` PASS_TO_PASS regression-damage deltas
- Astropy tenth-repo path now has:
  - `astropy__astropy-14365`: `4/4` cells complete
  - `astropy__astropy-14182`: `4/4` cells complete
  - `astropy__astropy-14539`: `2/4` cells complete (`naming`, `type_hints`)
- next cell completed: `astropy__astropy-14539` x `comments_docstrings` x `rep_2`

## Astropy 14539 Comments/Docstrings 2026-04-28

- `astropy__astropy-14539` x `comments_docstrings` x `rep_2`
  - clean and degraded both passed official SWE-bench target tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit stayed `2 -> 2`
  - exploration efficiency stayed `1.0 -> 1.0`
  - corrected total tokens moved `306729 -> 284222`
  - changed files stayed `2 -> 2`
  - RQ2 phase note: both sides ran two successful validation commands and had no failed execution commands
  - current read: outcome-stable and patch-shape neutral comments/docstrings result, slightly cheaper on the degraded side
- aggregate after refresh: `127` scored comparisons, `32` tasks, `11` represented repos, `9` fully complete repos, `11` clean-success to degraded-failure transitions, `11` PASS_TO_PASS regression-damage deltas
- Astropy tenth-repo path now has:
  - `astropy__astropy-14365`: `4/4` cells complete
  - `astropy__astropy-14182`: `4/4` cells complete
  - `astropy__astropy-14539`: `3/4` cells complete (`naming`, `type_hints`, `comments_docstrings`)
- next cell completed: `astropy__astropy-14539` x `remove_tests` x `rep_3`

## Astropy 14539 Remove-Tests 2026-04-28

- `astropy__astropy-14539` x `remove_tests` x `rep_3`
  - clean and degraded both passed official SWE-bench target tests
  - FAIL_TO_PASS failures stayed `0 -> 0`
  - PASS_TO_PASS failures stayed `0 -> 0`
  - files opened before first edit stayed `2 -> 2`
  - exploration efficiency moved `1.0 -> 0.5`
  - corrected total tokens moved `345434 -> 291973`
  - changed files stayed `2 -> 2`
  - clean changed `astropy/io/fits/diff.py` and `astropy/io/fits/tests/test_diff.py`
  - degraded changed `astropy/io/fits/diff.py` and `astropy/io/fits/tests/test_fitsdiff.py`
  - current read: outcome-stable and cheaper degraded result, but remove-tests changed the test-side patch target because `test_diff.py` was removed
- `astropy__astropy-14539` is now complete across all four strict degradation families:
  - `naming`
  - `type_hints`
  - `comments_docstrings`
  - `remove_tests`
- aggregate after refresh: `128` scored comparisons, `32` tasks, `11` represented repos, `10` fully complete repos, `11` clean-success to degraded-failure transitions, `11` PASS_TO_PASS regression-damage deltas
- `astropy/astropy` is now the tenth fully complete repo.
- fully complete repos:
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
