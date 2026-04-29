# Agent Run Contract

This document defines the current Stage 5 planning contract for downstream agent runs.

## Purpose

Stage 3 now selects tasks. Stage 4 has an explicit degradation handoff. Stage 5 needs the same level of structure so the actual experiment harness does not improvise:

- which repos are runnable
- which tasks should be run
- which harnesses are in scope
- how many replications to schedule
- where logs and metrics should land

The current contract now includes both a real Stage 4 materialization step and a real Stage 5 runner. The run plan still standardizes the artifact that the execution layer consumes.

## Current Harness Choice

The current planned harness set is:

- `claude-code`
  - family: Claude
  - access mode: subscription CLI
- `codex-cli`
  - family: Codex
  - access mode: subscription CLI

Rationale:

- both are real coding-agent environments the user already has access to
- both are worth comparing because the same degradation may affect the two harness families differently
- the core causal comparison still stays within the same repo, task, and harness

## Run-Plan Artifact

Use:

- `python -m src.cli build-run-plan --repo owner/name --deep-results-dir ./deep_results --packet-dir ./packets --candidates-dir ./candidates --output-dir ./run_plans`

Inputs:

- verified manifest from Stage 2
- experiment packet from repo admission review
- candidate JSON files for issue title/description recovery

Outputs:

- `{repo}_run_plan.json`
- `{repo}_run_plan.md`

The run plan expands each verified task across:

- the `clean` condition
- `type_hints`
- `naming`
- `comments_docstrings`
- `remove_tests`
- each selected harness
- each replication

## Gating Rules

The run plan emits one of three planning states:

- `READY`
  - verified tasks exist and the repo packet is `GO`
- `REVIEW_REQUIRED`
  - verified tasks exist, but the repo packet is `REVIEW` or missing
- `BLOCKED`
  - no verified tasks exist, or the repo packet is `NO_GO`

Important:

- a run plan can still be emitted in `REVIEW_REQUIRED` or `BLOCKED` states
- only `READY` or explicitly human-approved `REVIEW_REQUIRED` repos should move into live Stage 5 execution

## Per-Run Contents

Each planned run should carry:

- repo id
- candidate id / PR number
- base historical commit
- harness metadata
- condition
- replication number
- issue title and description
- FAIL_TO_PASS oracle tests
- Stage 4 degradation targets for that condition
- expected output paths for logs, metrics, and result summaries

For degraded conditions, the Stage 5 plan should use the manifest's `degradation_targets` block directly rather than recomputing file policy.

## Expected Run Layout

The current path template is:

- `runs/{repo_short}/{candidate_id}/{harness_id}/{condition}/rep_{replication}/`

Expected files under each run root:

- `metadata.json`
- `issue_prompt.md`
- `workspace/`
- `logs/`
- `result.json`
- `metrics.json`

This is meant to keep Stage 6 parsing simple and deterministic.

## Stage 4 Materialization

Use:

- `python -m src.cli materialize-runs --repo owner/name --run-plan-dir ./run_plans --clones-dir ./clones --output-dir .`

This command consumes the Stage 5 run plan, creates one isolated historical workspace per selected run, sanitizes git history, and applies the run's Stage 4 degradation directly from `stage4_plan.targets`.

Important:

- the first implementation materializes one workspace per planned run, even when multiple runs share the same task/condition
- this is intentionally redundant but correct because each harness/replication will later mutate its own workspace
- a cached condition-level workspace layer can be added later if materialization cost becomes significant

Per materialized run, Stage 4 now writes:

- `workspace/`
- `issue_prompt.md`
- `logs/`
- `metadata.json`

`metadata.json` records the exact Stage 4 result summary so the later Stage 5 runner does not need to guess what changed.

## Metrics Contract

Bootstrap metrics:

- `tokens_before_first_edit`
- `files_opened_before_first_edit`
- `dead_end_file_opens`
- `relevant_files_opened`
- `exploration_efficiency`
- `time_to_first_edit_seconds`

Execution metrics:

- `task_success`
- `total_tokens`
- `total_cost_usd`
- `edits_applied`
- `test_commands_run`
- `completion_reason`

Artifacts to preserve:

- raw agent log
- applied patch
- post-run test output
- final repository diff

## Stage 5 Execution

Use:

- `python -m src.cli execute-runs --repo owner/name --run-plan-dir ./run_plans --clones-dir ./clones --output-dir .`

This command consumes the Stage 5 run plan, auto-materializes the selected run roots if needed, invokes the planned harness in the agent workspace, then performs oracle evaluation in a fresh isolated Stage 4 workspace for the same run.

Important:

- the oracle workspace rematerializes the same historical base commit and degradation condition
- only the agent's non-test changes are replayed into that workspace before hidden tests are restored
- this prevents agent-edited tests from polluting task scoring while still preserving the agent's code changes

Per executed run, it now writes:

- `result.json`
- `metrics.json`
- `logs/agent_prompt.md`
- `logs/agent_stdout.log`
- `logs/agent_stderr.log`
- `logs/post_run_test_output.txt`
- `logs/final_repo_diff.patch`

The first implementation normalizes the run outcome itself even though bootstrap-log parsing is still future work. That means:

- the runner records structured completion state and oracle success/failure now
- Stage 6 is responsible for enriching bootstrap/execution process metrics from preserved harness logs
- some metrics, such as exact Codex `tokens_before_first_edit`, remain `null` unless the harness logs expose enough information to recover them

## Stage 6 Parsing

Use:

- `python -m src.cli parse-runs --repo owner/name --execution-dir /path/to/stage5_outputs`

This command consumes `{repo}_stage5_execution.json`, parses the Stage 5 logs, updates each selected `metrics.json`, and writes:

- `{repo}_stage6_metrics.json`
- `{repo}_stage6_metrics.md`

Current parser coverage:

- Codex JSONL logs:
  - `files_opened_before_first_edit`
  - `dead_end_file_opens`
  - `relevant_files_opened`
  - `exploration_efficiency`
  - final cumulative token usage when `turn.completed.usage` is present
- Claude debug logs:
  - `time_to_first_edit_seconds`

Current limits:

- `total_cost_usd` still remains `null` unless the local harness logs expose it explicitly
- Claude still lacks reliable file-open counts from the current debug logs
- Codex still lacks `time_to_first_edit_seconds` because the current JSONL stream does not carry per-event timestamps
- Codex still lacks exact `tokens_before_first_edit` and post-edit token split because usage is reported as final cumulative usage
- Stage 6 does not yet emit command/message/edit/validation counts split around first edit, but these are recoverable from existing ordered Codex JSONL logs

## Open Follow-On Work

- Define how Claude and Codex logs will be normalized so Stage 6 parsing uses one schema.
- Extend Codex Stage 6 parsing with RQ2-lite process metrics: command counts, validation command counts, failed command counts, message counts, edit-event counts, and edit/test/edit rework proxies split around first edit.
- Decide whether both harnesses should use the same replication count or whether frontier-cost constraints justify asymmetric replication later.
- Consider adding a cached task/condition workspace layer so repeated harness/replication runs do not all require independent Stage 4 materialization from scratch.
- Improve live harness observability so both Claude and Codex preserve richer action traces, not just normalized final results plus stdout/stderr artifacts.
