# Experimental Pipeline: Measuring Codebase Agent-Readiness

## Overview

Our goal is to measure how specific code properties affect AI coding agent performance. We do this by taking well-structured repos, intentionally degrading one property at a time, and comparing agent performance on the same tasks before and after degradation.

The key design principle throughout: we never compare repo A to repo B. We compare repo A (clean) to repo A (degraded). This means natural differences between repos (size, domain, language quirks) cancel out. Any performance change is directly attributable to the property we degraded.

---

## Stage 1: Repository Selection

**What we do:** Curate a set of Python repositories from GitHub.

**Selection criteria:**
- Python (primary language)
- Active commits within last 6 months
- Has an existing test suite (pytest or unittest)
- Small to medium size (under ~100k LOC)
- Variety of domains (web frameworks, CLI tools, data processing, APIs)
- Exclude: ML training repos, massive monorepos

**Why these criteria:** We need repos that are well-structured enough to serve as a meaningful "gold standard" baseline. If we start with messy repos, degrading them further doesn't tell us much. We need test suites because they serve as our ground truth for whether the agent actually solved a task. We want variety in domain so our findings generalize and aren't just "this works for web frameworks."

**Target:** 10-15 well-chosen repos with strong test suites. We don't need 50. A smaller set with clean measurements is better than a large set with noisy data.

**Output:** A curated list of repos with justification for each selection.

---

## Stage 2: Static Feature Extraction

**What we do:** For each repo, extract measurable values for every property we plan to degrade.

**Features to extract:**
- Type annotation coverage (mypy or custom AST analysis, percentage of functions with type hints)
- Naming convention quality (agent-assisted qualitative assessment or automated readability scoring)
- Comments/docstrings coverage (count and spread of natural-language guidance in the repo)
- Test suite breadth and structure (test coverage where available, executable test count, preserved test-support infrastructure)

**Why this step matters:** This gives us our baseline measurements. We need to know what the repo looks like before we degrade it. These numbers also become the independent variables in our analysis. Down the line, this is what feeds into the RQ3 scoring tool.

**Output:** A feature matrix. One row per repo, one column per feature, real numbers.

---

## Stage 3: Historical Issue Selection

**What we do:** For each repo, find 3-5 historical issues (bugs or features) that were already resolved and have associated test changes.

**How to find them:** Look through merged PRs in the repo's git history. We want PRs that:
- Have a clear issue description or commit message explaining the problem
- Include test changes (new tests or modified tests that verify the fix)
- Touch a reasonable scope (not a one-line typo fix, not a massive refactor)
- Touch parts of the codebase that our mutations will affect (code with type hints, meaningful names, etc.)

**Why historical issues:** This is what makes the whole pipeline scalable. We don't need to understand each repo deeply or design custom tasks. The repo's own history gives us real tasks with built-in ground truth. We revert the patch, the tests fail. The agent solves it, the tests pass. Clean binary signal.

This is essentially the same approach SWE-bench uses, adapted for our controlled degradation design.

**Output:** For each repo, a list of 3-5 issue/PR pairs with the commit hashes needed to revert them.

---

## Stage 4: Codebase Mutation

**What we do:** For each repo, create degraded versions by modifying one property at a time.

**Mutations:**
1. Strip type hints (remove all type annotations via AST transformation)
2. Degrade naming (replace meaningful variable/function names with generic symbols like v0, v1)
3. Remove comments and docstrings (strip natural-language intent and usage guidance)
4. Remove test files (delete existing test files while preserving test infrastructure so the agent can still write and run its own tests)

For the first three degradations, existing test files are also degraded. Otherwise the agent could recover clean type, naming, and behavioral signals from the untouched tests.

**Why single mutations:** We isolate one variable at a time so we can cleanly attribute any performance change to that specific property. If we degrade naming and type hints at the same time and performance drops, we can't tell which one caused it. Single mutations keep the causal story clean. Combinations are a stretch goal if time permits.

**Why these four:** Hu et al. (ASE 2024) showed that naming quality has the largest impact on model understanding at the function level. Type hints have been shown to improve model accuracy in related work (Luo et al., 2025). Comments/docstrings remove a natural-language intent channel that agents clearly use during orientation, while test surface captures both verification and behavioral examples. These four give us a mix of properties with existing evidence and properties we can manipulate cleanly without breaking the repo.

**Operationalization:** `LLM-J` now materializes this stage from the Stage 5 run plan. For each planned run, it checks out the historical base commit into an isolated worktree, sanitizes git history, and applies the requested single degradation using the manifest's explicit `degradation_targets` block.

**Output:** A per-run workspace tree under `runs/{repo_short}/{candidate_id}/{harness_id}/{condition}/rep_{replication}/` with `workspace/`, `issue_prompt.md`, `logs/`, and `metadata.json`.

---

## Stage 5: Agent Task Runs

**What we do:** For each repo, revert each historical issue and run the agent on it under all 5 conditions (1 clean + 4 degraded). Repeat each condition 2-3 times to account for non-determinism.

**The run structure for one repo:**
- 3-5 historical issues
- 5 conditions per issue (clean + 4 degradations)
- 2-3 replications per condition
- Total: roughly 30-75 runs per repo

**Agent / harness choice:** We currently plan to run two frontier subscription-backed harnesses in parallel:
- Claude via the Claude Code CLI harness
- Codex via the Codex CLI harness

This makes Stage 5 both an execution stage and a controlled cross-harness comparison. The primary comparisons still stay within the same repo and the same task:
- clean vs degraded for Claude
- clean vs degraded for Codex

We can then compare whether the degradation sensitivity patterns look similar across harness families without collapsing them into one pooled score too early.

**What the agent gets:** The codebase (clean or degraded), the issue description from the original PR/commit, and nothing else. No hints, no extra context.

**What we capture:** Full agent logs for every run. These logs contain everything we need for both bootstrap and execution measurement.

**Operationalization:** `LLM-J` now has an `execute-runs` workflow that consumes the Stage 5 run plan, auto-materializes selected Stage 4 workspaces, invokes the local Claude or Codex CLI harness, and then evaluates the run in a fresh oracle workspace for the same historical task. That oracle workspace rematerializes the same Stage 4 condition, replays only the agent's non-test changes, restores the hidden tests, and runs pytest there. It already writes normalized `result.json`, `metrics.json`, stdout/stderr logs, and final diffs; richer bootstrap parsing is still a separate Stage 6 task.

**Why replications:** Agents are non-deterministic. Same prompt, same codebase, slightly different behavior each time. Running 2-3 times per condition lets us average out randomness and report confidence intervals instead of single data points.

**Output:** A run-plan artifact plus, after Stage 4 materialization and live execution, a directory of run artifacts organized by repo, issue, harness, condition, and replication number.

---

## Stage 6: Log Parsing and Phase Splitting

**What we do:** Parse every agent log and split it into two phases: bootstrap and execution.

**How we split:** We find the first meaningful code edit in the log. Everything before that edit is bootstrap. Everything from that edit onward is execution.

**Why this split works:** Every agent naturally goes through a discovery phase before it starts making changes. It reads files, searches for things, explores the directory structure, and forms a plan. Then it starts editing. This is observable behavior we can extract from logs without needing to know anything about the repo. We're not asking the agent questions or grading its understanding. We're watching what it does.

**Bootstrap metrics (extracted from the pre-edit portion of the log):**
- Tokens consumed before first edit
- Number of files explored
- Number of dead-end file opens (files opened but not relevant to the task)
- Exploration efficiency (percentage of explored files that were actually relevant)
- Time to first edit

**Execution metrics (extracted from the post-edit portion of the log):**
- Task success (binary: did the reverted tests pass after the agent's changes?)
- Total tokens to completion
- Number of incorrect attempts or reverts
- Total cost

**Why these metrics:** Bootstrap metrics tell us how efficiently the agent oriented itself. A well-organized repo with clear naming should produce a shorter, more focused bootstrap. Execution metrics tell us how effectively the agent completed the task. Together they let us compare whether a given degradation hurts orientation, task completion, or both.

**Operationalization:** `LLM-J` now has a first `parse-runs` workflow that consumes `{repo}_stage5_execution.json`, enriches each `metrics.json`, and writes a Stage 6 summary artifact. The first pass is intentionally asymmetric:
- Codex JSONL logs currently support file-exploration metrics such as `files_opened_before_first_edit`, `dead_end_file_opens`, `relevant_files_opened`, and `exploration_efficiency`
- Claude debug logs currently support `time_to_first_edit_seconds`
- Codex JSONL logs now expose final cumulative token usage, including cached input tokens; cost still remains unavailable unless the local harness logs expose it explicitly
- exact Codex `tokens_before_first_edit`, post-edit token split, and `time_to_first_edit_seconds` are still unavailable from the current Codex logs
- additional Codex process metrics such as command counts, validation command counts, failed command counts, and edit/test/edit rework proxies are recoverable from existing ordered JSONL logs and should be added as lightweight Stage 6 enrichment

**Output:** A structured dataset with one row per run, columns for repo metadata, condition, phase metrics, and outcome.

---

## Stage 7: Analysis

**What we do:** Use the structured dataset to answer our research questions.

**For RQ1 (Which properties matter most?):**
Compare performance metrics between clean and each degraded condition. Calculate effect sizes for each property. Rank them by impact. Example finding: "Stripping type hints reduced execution success rate by X%, Cohen's d = Y."

**For RQ2 (Is agent-readiness multi-dimensional?):**
Compare the effect of each degradation across bootstrap and execution phases. If the same degradation hits both phases roughly equally, that suggests a single dimension. If different degradations affect different phases (e.g., naming quality matters for bootstrap but not execution, type hints matter for execution but not bootstrap), that's evidence of multi-dimensionality. We can also compute correlation coefficients between bootstrap scores and execution scores across all conditions. Weak correlation = independent dimensions.

Current framing: RQ2 is a supporting process analysis unless the larger RQ1 scale-out shows stronger outcome movement. The near-term question is whether degradations change how agents search, validate, edit, and spend tokens even when final pass/fail outcomes are preserved.

**For RQ3 (Can we predict agent-readiness?):**
Build an agent-in-the-loop scoring tool that combines static feature extraction (from Stage 2) with an agent probe. The tool drops an agent into the repo with a structured rubric and grading criteria (a well-defined markdown prompt specifying what to evaluate and how to score it). The agent explores the repo, assesses properties like naming clarity, documentation coverage, structural organization, and test suite presence, and produces a multi-dimensional readiness score. We test this tool on held-out repos (repos not used in our main experiment) and compare its predicted scores against actual agent performance from our data. We also compare against heuristic baselines like Factory.ai's checklist approach. The goal is to show that an agent-grounded assessment outperforms static file-existence checks.

**Output:** Statistical results, effect sizes, correlation matrices, and model accuracy comparisons.

**Operationalization:** `LLM-J` now has a `build-task-packet` workflow that turns a Stage 7 summary into a focused single-task packet for one candidate and harness. It reads the underlying `result.json` artifacts so the packet can include not just aggregate deltas, but also condition-by-condition failure notes such as FAIL_TO_PASS misses, PASS_TO_PASS regressions, and missing hidden-test targets. This gives us a clean handoff artifact for the first “mini-study” on a single task before we scale to repo-level or cross-repo analysis.

---

## On Handoff (Why We're Excluding It)

The original design included a third phase: handoff (killing an agent mid-task and measuring whether a fresh agent can continue). We're excluding this from the core study for the following reasons:

The second agent's performance depends heavily on what the first agent chose to leave behind: whether it wrote good commit messages, left notes, or produced readable partial code. That's agent behavior, not a codebase property, and we can't cleanly separate the two. We would need to standardize the handoff context so heavily (same kill point, same information given to the second agent, same partial progress) that it becomes its own research project with its own set of confounds.

Bootstrap and execution are measurable directly from logs with minimal assumptions. Handoff requires us to control too many additional variables to produce reliable results within our scope.

We will mention handoff as a natural extension in our Future Work section.

---

## Summary: What Makes This Pipeline Work

1. **We never need to deeply understand each repo.** Historical issues give us tasks. Test suites give us ground truth. Logs give us metrics.
2. **We never compare across repos.** Every comparison is the same repo, same task, clean vs degraded. Natural repo differences cancel out.
3. **Everything is extractable from logs.** No manual grading, no custom evaluation, no bespoke questions per repo.
4. **Single mutations keep the causal story clean.** One property changes, everything else stays the same, performance change is attributable.
5. **The hard part is building the tooling, not scaling it.** Once mutation scripts, log parsers, and the run pipeline exist, adding more repos and issues is mostly automated.
