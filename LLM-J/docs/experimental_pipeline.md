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
- Directory structure metrics (depth, file count, average file size, nesting complexity)
- Test suite breadth (pytest-cov, percentage of code covered, number of test files)

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
3. Flatten directory structure (collapse nested directories, randomize file organization)
4. Remove test files (delete test suite, simulating a repo with no tests)

**Why single mutations:** We isolate one variable at a time so we can cleanly attribute any performance change to that specific property. If we degrade naming and type hints at the same time and performance drops, we can't tell which one caused it. Single mutations keep the causal story clean. Combinations are a stretch goal if time permits.

**Why these four:** Hu et al. (ASE 2024) showed that naming quality has the largest impact on model understanding at the function level. Type hints have been shown to improve model accuracy in related work (Luo et al., 2025). Directory structure and test suite breadth are practitioner-identified pain points (Gustafson, 2025) that no one has empirically measured yet. These four give us a mix of properties with existing evidence and properties we're testing for the first time.

**Output:** For each repo, 4 degraded versions alongside the original gold standard. 5 versions total per repo.

---

## Stage 5: Agent Task Runs

**What we do:** For each repo, revert each historical issue and run the agent on it under all 5 conditions (1 clean + 4 degraded). Repeat each condition 2-3 times to account for non-determinism.

**The run structure for one repo:**
- 3-5 historical issues
- 5 conditions per issue (clean + 4 degradations)
- 2-3 replications per condition
- Total: roughly 30-75 runs per repo

**Agent:** We plan to use a cost-efficient model running through an open-source coding agent harness like OpenCode or the Claude Code harness. The actual model will likely be a cheaper option (e.g., DeepSeek or a similar model) to keep token costs manageable across hundreds of runs. The specific model choice doesn't affect our findings much since we're measuring relative performance (clean vs degraded), not absolute capability. If time allows, we can run a subset of experiments with a frontier model to check whether the patterns hold across model tiers.

**What the agent gets:** The codebase (clean or degraded), the issue description from the original PR/commit, and nothing else. No hints, no extra context.

**What we capture:** Full agent logs for every run. These logs contain everything we need for both bootstrap and execution measurement.

**Why replications:** Agents are non-deterministic. Same prompt, same codebase, slightly different behavior each time. Running 2-3 times per condition lets us average out randomness and report confidence intervals instead of single data points.

**Output:** A directory of agent logs organized by repo, issue, condition, and replication number.

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

**Output:** A structured dataset with one row per run, columns for repo metadata, condition, phase metrics, and outcome.

---

## Stage 7: Analysis

**What we do:** Use the structured dataset to answer our research questions.

**For RQ1 (Which properties matter most?):**
Compare performance metrics between clean and each degraded condition. Calculate effect sizes for each property. Rank them by impact. Example finding: "Stripping type hints reduced execution success rate by X%, Cohen's d = Y."

**For RQ2 (Is agent-readiness multi-dimensional?):**
Compare the effect of each degradation across bootstrap and execution phases. If the same degradation hits both phases roughly equally, that suggests a single dimension. If different degradations affect different phases (e.g., naming quality matters for bootstrap but not execution, type hints matter for execution but not bootstrap), that's evidence of multi-dimensionality. We can also compute correlation coefficients between bootstrap scores and execution scores across all conditions. Weak correlation = independent dimensions.

**For RQ3 (Can we predict agent-readiness?):**
Build an agent-in-the-loop scoring tool that combines static feature extraction (from Stage 2) with an agent probe. The tool drops an agent into the repo with a structured rubric and grading criteria (a well-defined markdown prompt specifying what to evaluate and how to score it). The agent explores the repo, assesses properties like naming clarity, documentation coverage, structural organization, and test suite presence, and produces a multi-dimensional readiness score. We test this tool on held-out repos (repos not used in our main experiment) and compare its predicted scores against actual agent performance from our data. We also compare against heuristic baselines like Factory.ai's checklist approach. The goal is to show that an agent-grounded assessment outperforms static file-existence checks.

**Output:** Statistical results, effect sizes, correlation matrices, and model accuracy comparisons.

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
