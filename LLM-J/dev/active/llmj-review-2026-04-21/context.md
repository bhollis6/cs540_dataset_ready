# Session Context

## Repo Layout

- Git root: `/home/caden/cs540_dataset_ready`
- Project under review: `/home/caden/cs540_dataset_ready/LLM-J`
- Teammate degradation scripts: `/home/caden/cs540_dataset_ready/degradation`

## Sync Status

- Ran `git pull --ff-only` from the git root via the `LLM-J` subdirectory.
- Pulled new sibling files into `degradation/` plus readiness reports at the git root.

## Documents Reviewed

- `README.md`
- `writeup.md`
- `repos_selection.md`
- `docs/decisions.md`
- `docs/experimental_pipeline.md`
- `docs/llm_judge_spec_v2(1).md`
- `docs/presentation_draft.md`
- `dev/active/staff-review-2026-03-24/report.md`
- `dev/active/future-improvements/tasks.md`
- `experiment_design_spec_v2(1).docx`

## Validation Run

- Used the user’s Fish helper `ai-env` to activate `/home/caden/venvs/ai-env`.
- Ran `python -m pytest -q` in `LLM-J`.
- Result: `40 passed in 0.57s`.

## Key Spec Delta Confirmed

- Directory flattening is no longer a degradation.
- Comments/docstrings removal is now a required degradation.
- Remove-tests must preserve test infrastructure such as `conftest.py`, fixtures, and shared helpers.
- The updated experiment description expects Stage 2 output to filter by navigation depth.

## Confirmed Decisions From 2026-04-21 Follow-Up

- Existing test files should also be degraded for the non-remove-tests conditions.
- Rationale: otherwise agents can recover clean naming, type, and behavioral signals from tests and partially bypass the intended degradation.
- The dedicated remove-tests condition is different:
  - remove existing test files only
  - preserve test infrastructure (`conftest.py`, fixtures, helpers, config) so the agent can still write and run its own tests
- This means Stage 4 needs a clearer distinction between:
  - removable test files
  - preserved test-support infrastructure

## Research Framing Notes

- The overall project direction is strong.
- The strongest design choice is the within-the-same-repo, within-the-same-task clean-vs-degraded comparison. That is the main causal strength of the study.
- Historical PRs plus FAIL_TO_PASS validation are the right task source and correctness check.
- Splitting behavior into bootstrap/discovery versus execution is a meaningful contribution if the metrics remain concrete and reproducible.

### Strength Ranking Of Research Questions

- `RQ1` is the strongest and should remain the centerpiece:
  - which codebase properties matter most for agent performance
- `RQ2` is good, but only if "multi-dimensional" is defined operationally through specific metrics rather than broad interpretation.
- `RQ3` is interesting but should be treated as exploratory unless the pipeline and dataset become extremely stable.

### Main Remaining Risks

- Degradation validity:
  - if a degradation is too weak, too partial, or breaks behavior, the causal story gets muddy
- Task-selection quality:
  - low-navigation or too-easy tasks can create false "no effect" results
- Harness/environment effects:
  - prompt, environment, or execution differences can dominate codebase effects if not controlled carefully
- Statistical power:
  - too few repos, tasks, or replications can leave the study underpowered
- Scope of claims:
  - results should be framed as evidence about the chosen agent/harness setup, not universal claims about all coding agents

### Analysis Guidance

- Prioritize effect sizes and confidence intervals over overconfident significance claims.
- Keep `RQ1` central in the writeup.
- Keep `RQ2` disciplined and metric-driven.
- Present `RQ3` conservatively unless the predictive signal is clearly robust.

## Degradation Implementation Assessment

- Teammate degradation work was directionally useful, but not yet aligned with the experiment contract.
- The scripts showed understanding of the rough degradation categories, but not yet the exact causal requirements of the study.
- The main problems were:
  - remove-tests removed too much infrastructure
  - non-remove-tests degradations skipped existing tests, which would leak clean signals
  - naming degradation was much narrower than the intended full intervention
- Bottom line:
  - not unusable
  - not research-ready without correction

## Current Contract Status

- Stage 1 and Stage 2 manifests now emit an explicit `degradation_targets` block per accepted PR.
- `LLM-J` validates that `source_files`, `test_files`, and `test_support_files` are disjoint before writing manifests.
- Non-remove-tests degradations now target:
  - source files
  - executable test files
  - Python-based test-support files
- Remove-tests now carries explicit:
  - `delete_files`
  - `preserve_files`
- This means the eventual Stage 4 harness should consume `degradation_targets` directly instead of re-deriving policy from prose or raw file buckets.

## Naming Degrader Status

- `degradation/naming_conventions.py` now protects discovery-critical test names and framework hooks instead of blindly renaming them.
- Protected cases now include:
  - top-level `test_*` functions in executable test files
  - `Test*` classes used for unittest / pytest class discovery
  - lifecycle and hook names such as `setUp`, `tearDown`, and `pytest_*`
- The collector also now covers more safe local bindings inside hazard-free functions:
  - tuple/list assignment targets
  - `for` / `async for` loop targets
  - `with ... as ...` bindings
  - walrus (`:=`) bindings
- Regression coverage for this behavior now lives in `LLM-J/tests/test_naming_degrader_contract.py`.
- Main remaining naming gap:
  - broader but still behavior-preserving obfuscation beyond safe locals and function/class names, especially when validating against real repos with `rope` installed

## Live Naming Audit Notes

- A real `rope`-backed rename pass was run on disposable worktrees for local target repos using `uv run --with rope`.
- Dry-run audits after the fixture / placeholder / short-class protections showed:
  - `httpx`: 927 rename candidates
  - `starlette`: 1155 rename candidates
  - `cattrs`: 872 rename candidates
- The first live `starlette` run exposed a major silent-skip issue:
  - 808 successful renames
  - 347 total skips
  - only 70 skips were visible `rope` refactoring errors
- Cause:
  - many later symbols in the same file were being skipped because `_find_near()` only searched a local window around stale offsets after earlier renames shifted the file
- Fix applied:
  - `_find_near()` now falls back to a whole-file nearest-match search
  - rename stats now break skips down into:
    - missing resource
    - offset not found
    - refactoring errors
    - other errors
- Fresh live `starlette` rerun after the fix:
  - 922 successful renames
  - 233 total skips
  - 74 offset-not-found
  - 159 refactoring errors
- Remaining high-frequency live refactoring-error names in `starlette`:
  - `response`
  - `session`
  - `text`
  - `handle`
  - `close`
  - `url_path_for`
  - `body`
- Interpretation:
  - the next remaining naming work is less about offset churn and more about deciding whether to pre-skip some repeated override/protocol-style names or accept them as normal `rope` limitations
- Fresh live `httpx` run after the same fixes:
  - 822 successful renames
  - 105 total skips
  - 41 offset-not-found
  - 64 refactoring errors
- Highest-frequency live refactoring-error names in `httpx`:
  - `aclose`
  - `length`
  - `close`
  - `flush`
  - `decoded`
  - `handle_async_request`
  - `body`
  - `more_body`
- Cross-repo takeaway:
  - some failures repeat around interface / protocol / transport-style names
  - but the exact high-frequency names differ between repos
  - so a broad global skiplist would likely overfit and weaken the degradation more than necessary

## Naming Audit Tooling

- Added `degradation/naming_audit.py` as a reusable per-repo readiness helper.
- It produces structured JSON with:
  - dry-run rename counts
  - file coverage
  - sample candidate symbols
  - optional live-run rename/skip metrics when run with `--live`
- `RenameStats` now also exposes machine-readable skip breakdowns and top skipped names.
- This gives a repeatable repo-gate workflow instead of relying on manual shell inspection for each target repo.
- Added `python -m src.cli audit-naming` as the `LLM-J` entry point for that process.
- The CLI now:
  - reuses the bare clone cache
  - creates a disposable sanitized worktree
  - runs the sibling audit helper
  - writes a wrapped `{repo}_naming_readiness.json` report
- This is a small but real step toward the desired seamless pipeline: one repo command, human review on the report, then later handoff into degradation and agent-run stages.

## Repo Readiness Screen

- Added `degradation/repo_readiness.py` as a broader static repo screen.
- Added `python -m src.cli audit-repo` as the `LLM-J` entry point for that screen.
- The repo screen reports:
  - type-hint surface
  - comments/docstrings surface
  - remove-tests viability
  - dry-run naming surface
- It also emits provisional per-condition statuses:
  - `PASS`
  - `REVIEW`
  - `FAIL`
- These are intentionally conservative screening heuristics, not final experimental thresholds.
- Intended usage:
  - `audit-repo` first as the broad go/review/no-go packet
  - `audit-naming --live` next when naming-specific viability needs deeper confirmation

## Experiment Packet

- Added `python -m src.cli build-packet` as the repo-level review artifact builder.
- It combines:
  - Stage 1 selected manifest
  - Stage 2 verified manifest
  - repo readiness report
  - naming readiness report
- Output:
  - `{repo}_experiment_packet.json`
- Purpose:
  - give the human reviewer one place to decide whether a repo is ready to move into Stage 4 degradation and Stage 5 agent runs
- Current decision labels:
  - `GO`
  - `REVIEW`
  - `NO_GO`
- These are still heuristic workflow labels, not final research claims.
- The packet now includes an explicit admission rubric with four criteria:
  - repo static surface viability
  - Stage 1 task-pool depth
  - Stage 2 verified-task depth
  - naming live-audit readiness
- It also writes a markdown companion file so the human review step is readable without opening raw JSON.
