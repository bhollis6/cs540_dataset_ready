# Staff Review Report: LLM-J

Date: 2026-03-24
Scope: Everything under `LLM-J/`
Reviewer framing: Staff-level review of the Stage 3 PR-selection and validation layer in the larger agent-readiness experiment.

## Executive Summary

This repository is the task-selection and validation layer for the larger experimental pipeline described in [`experimental_pipeline.md`](../../../experimental_pipeline.md). Conceptually, the design is strong. The docs show clear reasoning about experimental validity, the Stage 1 / Stage 2 split is correct, and the repo is already operating on real historical PR artifacts rather than just scaffolding.

The main issue is not lack of thought. The main issue is that the implementation still behaves like a research prototype in the places where the larger pipeline most needs rigor: downstream artifact contracts, provider parity, environment isolation, historical-state sanitization, and integration testing around Stage 2. The docs often describe the intended system more accurately than the code currently enforces.

This means the repo is strong as a design artifact and promising as a data-generation tool, but not yet fully trustworthy as a stable experimental substrate for Stage 4 through Stage 7.

## Context And Role In The Bigger Pipeline

Per [`experimental_pipeline.md`](../../../experimental_pipeline.md), this repo is not the whole experiment. It is the Stage 3 system that identifies valid historical tasks for:

1. Stage 4: codebase mutation
2. Stage 5: agent task runs
3. Stage 6: log parsing and bootstrap/execution splitting
4. Stage 7: analysis

That bigger-picture framing matters for the review:

- The goal here is not just to pick "good PRs."
- The goal is to pick PRs that will remain meaningful after whole-repo degradation.
- The output artifacts from this repo are not convenience files. They are the contract for downstream experimental stages.

The repository docs generally understand this correctly. The main implementation gap is that some of the critical assumptions described in the docs are not fully enforced in code.

## What Is Working Well

### 1. The experimental thinking is strong

The strongest part of this repo is the reasoning in:

- [`experimental_pipeline.md`](../../../experimental_pipeline.md)
- [`decisions.md`](../../../decisions.md)
- [`README.md`](../../../README.md)

The project clearly understands:

- why same-repo clean vs degraded comparisons are the core causal design
- why historical PRs are the right task source
- why FAIL_TO_PASS validation matters
- why Stage 2 needs full-repo context and not just diffs
- why navigation depth matters for the larger mutation study

That foundation is much stronger than most early research tooling.

### 2. The architecture is directionally correct

The decomposition into:

- scraper
- Stage 1 evaluator
- Stage 2 deep evaluation
- provider abstraction
- output writers

is the right shape for this system. The separation between Stage 1 fast screening and Stage 2 deeper validation is especially good. That design matches the experimental needs and avoids spending expensive deep-eval effort on obviously bad candidates.

### 3. The project already produces real artifacts

This is not a toy prototype with mocked data. The repo contains:

- candidate PR JSONs
- Stage 1 manifests and CSVs
- Stage 2 results
- a verified manifest

That is valuable because the current implementation can already reveal real process and contract problems before the later mutation and agent-run stages are built.

### 4. The docs are unusually useful

The docs do more than explain how to run commands. They explain why the system exists, what changed from the original spec, and how it ties into the future pipeline. That makes the repo much easier to reason about at staff level.

## Critical Findings

### 1. The Stage 2 verified manifest is currently not a trustworthy downstream contract

Severity: High

The most serious issue is in the final output artifact that is supposed to feed Stage 4 and Stage 5.

In [`src/deep_eval/deep_judge.py`](../../../src/deep_eval/deep_judge.py), the verified manifest writes:

```python
"base_commit_sha": r.preflight.candidate_id  # placeholder
```

This is visible in the generated output:

- [`deep_results/cattrs_verified_manifest.json`](../../../deep_results/cattrs_verified_manifest.json)

The file contains values like:

```json
"base_commit_sha": "cattrs_pr_117"
```

instead of an actual git SHA.

The same verified manifest also omits fields the README says downstream stages depend on, specifically `source_files` and `test_files`.

Why this matters:

- This breaks the handoff contract to Stage 4 and Stage 5.
- It introduces silent corruption into the most important downstream artifact.
- It means later pipeline stages either cannot run correctly or will need to recover data from other files, which defeats the point of a verified manifest.

This is the first thing that should be fixed.

### 2. Stage 2 provider support is inconsistent with the interface and docs

Severity: High

The CLI advertises `claude-code`, `anthropic`, and `openrouter` for `deep-evaluate`, but the implementation is not actually stage-aware across providers.

The clearest issue is Anthropic:

- [`src/providers/anthropic.py`](../../../src/providers/anthropic.py) defines a 5-criterion tool schema
- Stage 2 parsing in [`src/deep_eval/models.py`](../../../src/deep_eval/models.py) requires `navigation_depth`

That means Stage 2 with `--provider anthropic` is structurally broken.

Why this matters:

- The interface claims flexibility that does not exist.
- Reproducibility depends on the provider layer being honest and explicit.
- This kind of mismatch is especially dangerous in a research pipeline because it can fail late or produce inconsistent outputs across providers.

The system needs either:

- proper Stage 2 schemas for all supported providers, or
- a stricter supported-provider matrix in code and docs.

### 3. Preflight is not isolated enough for a controlled experiment

Severity: High

`run_preflight()` installs each historical project into the active Python environment using editable installs.

This creates several problems:

- dependency leakage across candidates
- environmental mutation on the operator machine
- lower reproducibility across runs
- hidden coupling between candidate order and test outcomes

That is acceptable for a quick prototype. It is not acceptable for the layer that establishes the validity of future experimental tasks.

Why this matters:

- FAIL_TO_PASS is supposed to be a mechanical oracle
- if the environment is dirty or shared, the oracle becomes weaker
- later research claims will rest on the assumption that these validations were stable and comparable

The preflight stage should move to isolated per-candidate environments or containers.

### 4. Historical-state sanitization is incomplete

Severity: High

The docs say the pipeline adopted SWE-bench’s approach to sanitizing the repo state so an agent cannot see future commits. The implementation only partially does this:

- removes `origin`
- expires reflog
- runs gc

It does not actually remove future refs, branches, or tags from the local clone. The bare clone still contains later history.

Why this matters:

- The repo state shown to the agent is not as historically sealed as the docs claim.
- This weakens the validity of "historical task" framing.
- It opens the door to future stages accidentally leaking information or letting the agent inspect metadata that should not exist yet.

This is not just hygiene. It is part of the experiment boundary.

## Important Non-Blocking Findings

### 5. The Stage 2 context model is too shallow for the stated goal

Severity: Medium

The Stage 2 context extractor reads:

- touched source files
- first-degree imports

That is not enough for many of the tasks this repo says it wants to select.

For these Python repos, the important context often lives in:

- registration paths
- subclass hierarchies
- dispatch wiring
- factories
- indirect call chains
- modules reached through runtime composition rather than static imports

This means navigation-depth scoring can be systematically understated.

The pipeline says Stage 2 exists because degradation affects the whole repo, not just the diff. The current context extraction only partially reflects that.

### 6. The final Stage 2 selection policy is not fully aligned with the experiment

Severity: Medium

The docs correctly frame Navigation Depth as central to experimental sensitivity, but the code does not really use it as a gating or ranking criterion beyond folding it into the total score.

That leads to cases like:

- `cattrs_pr_108` being accepted
- while its own Stage 2 summary says degradation would likely have limited impact

That is selection drift. It means Stage 2 can admit tasks that are valid bug-fix tasks but weak experimental tasks.

The repo should likely enforce one of:

- a minimum navigation depth
- a manual-review flag for low-navigation candidates
- per-mutation suitability scoring
- a final top-k policy that favors the most degradation-sensitive tasks

### 7. Several CLI knobs do not actually control behavior

Severity: Medium

Examples:

- `--accept-threshold` and `--review-threshold` are stored in config but not actually used in recommendation computation
- `evaluate --opus` is parsed but does not map to an Opus model as the help text suggests

Why this matters:

- It weakens trust in the CLI
- It hurts reproducibility
- It creates avoidable confusion when different runs are compared later

In research tooling, configuration honesty matters more than convenience.

### 8. The testing strategy is too helper-heavy and too integration-light

Severity: Medium

The current tests are mostly unit tests around:

- filters
- prompt construction
- simple model parsing
- CSV writing
- ICC calculation

Those are fine, but the highest-risk parts of the system are mostly untested:

- deep evaluation orchestration
- preflight patch application behavior
- verified manifest contract
- provider/schema compatibility across stages
- repo sanitization assumptions

This is why a serious output bug made it into a generated manifest despite the test suite passing cleanly.

## Code Quality Assessment

### Strengths

- Module boundaries are reasonable
- Naming is generally clear
- The code is easy to read
- The main flows are not overly abstracted
- The provider abstraction is directionally good

### Weaknesses

- Too much important state moves through loose dicts and side-loaded JSON
- Config is partially dynamic and partially hardcoded
- Some code comments and docs describe intended behavior rather than actual behavior
- Stage 2 data flow is not modeled strongly enough, which is why output contracts drifted
- The repo currently has a lot of lint drift despite being otherwise small

This is less about style and more about enforcement. The repo needs stronger typed contracts around the Stage 2 handoff path.

## Documentation Assessment

### What is good

- The docs explain the future direction clearly
- `experimental_pipeline.md` does a good job explaining where this repo is tied into the larger research pipeline
- `llm_judge_spec_v2(1).md` is useful as historical context
- `decisions.md` explains why the design changed

### What needs improvement

- The README overstates current output guarantees
- The provider matrix is not honest enough about what works in which stage
- The docs should distinguish "implemented," "partially implemented," and "planned"
- The exact output schemas should be documented explicitly, not only implied
- There should be run provenance metadata for artifacts

The docs are strong on rationale and weaker on operational truthfulness.

## Pipeline Gaps And Better Ideas

This repo already captures many of the obvious nuances. The main remaining opportunities are not "forgotten basics." They are the next layer of rigor and the next layer of experimental usefulness.

### 1. Score per degradation dimension, not just generic mutation relevance

Right now, `mutation_relevance` compresses multiple future degradations into one score.

That is too coarse for what Stage 4 will eventually need.

A better Stage 2 output would estimate sensitivity separately for:

- type-hint degradation
- naming degradation
- directory-structure degradation
- test-surface degradation

This would let downstream stages choose tasks that are actually sensitive to the specific mutation being studied.

### 2. Add explicit mutation feasibility checks

A candidate can be:

- mechanically valid
- well-scoped
- reasonably described

and still be a poor candidate for the mutation study if the relevant code barely has type hints, uses little internal structure, or is too local for repo-level degradation to matter.

Stage 2 should not only ask "is this a good bug-fix task?"
It should ask "is this a good mutation-sensitive bug-fix task?"

### 3. Build a richer task viability bundle

Instead of the verified manifest only being a shortlist, it should become a full handoff artifact containing:

- base SHA
- merge SHA
- oracle tests
- source/test files
- environment setup recipe
- mutation-relevant files
- navigation-depth notes
- setup risks
- exclusion reasons for rejected candidates

That would make later stages more robust and auditable.

### 4. Use uncertainty-aware review for borderline cases

Reliability is currently optional and mostly diagnostic.

A better process would be:

- single evaluation for obvious rejects
- dual evaluation for borderline candidates
- manual review only for disagreement cases near threshold

That keeps cost controlled while focusing human attention where model instability actually matters.

### 5. Improve context retrieval for Stage 2

A better retrieval strategy would not stop at first-degree imports.

It should consider:

- symbol definitions referenced in diffs
- inheritance chains
- registered handlers and dispatch paths
- call targets
- modules imported by already-retrieved local files

This would make navigation-depth scoring more faithful to what an agent actually experiences during bootstrap.

### 6. Start versioning experimental artifacts properly

Every output directory should capture:

- pipeline git commit
- prompt hash
- provider and model
- Python version
- install strategy
- timestamp
- config snapshot

Without this, later reruns and comparisons will be hard to defend.

### 7. Capture exclusion taxonomy now

Rejected candidates should not just disappear. Record structured reasons such as:

- patch failed to apply
- tests do not fail at base
- tests do not pass after gold patch
- low navigation depth
- low mutation feasibility
- unclear prompt
- environment setup unstable

That metadata will help with both debugging and future method writeup.

## What This Repository Should Probably Become Next

The next maturity step is not "more code."
It is "turning this from a useful prototype into a research-grade task curation system."

That means:

- strong Stage 2 contracts
- isolated preflight environments
- explicit provider compatibility
- integration tests over deep evaluation
- artifact provenance
- more experiment-aligned task scoring

If that happens, this repo can become a strong backbone for the later mutation and agent-run stages.

If that does not happen, the biggest risk is that downstream work grows on top of unstable assumptions and the project loses time debugging artifacts instead of learning from experiments.

## Recommended Next Steps

### Priority 0: Fix the blocking contract issues

1. Fix the Stage 2 verified manifest so it contains correct SHAs and all downstream-required fields.
2. Add an integration test that validates the verified manifest schema and contents.
3. Make the provider matrix explicit and fail fast for unsupported Stage 2 providers.

### Priority 1: Make preflight experimentally credible

1. Move preflight into isolated per-candidate environments or containers.
2. Harden git sanitization so future refs are genuinely hidden.
3. Capture setup/provenance metadata per candidate run.

### Priority 2: Align task selection with the actual mutation study

1. Add per-mutation sensitivity scoring instead of a single generic relevance score.
2. Introduce a stronger policy for low-navigation tasks.
3. Consider a final top-k selection stage optimized for experimental sensitivity, not just general PR quality.

### Priority 3: Improve retrieval and testing

1. Replace first-degree-import-only context with richer task-relevant retrieval.
2. Add integration tests for deep evaluation and provider compatibility.
3. Add regression tests around real generated artifacts, not just helper functions.

### Priority 4: Improve research process hygiene

1. Add run manifests and versioning metadata to results directories.
2. Record structured rejection/exclusion reasons.
3. Document what is implemented vs planned vs partially implemented.

## Verification Performed During Review

I ran:

```bash
pytest -q
ruff check .
```

Observed results:

- `pytest -q`: 34 passed
- `ruff check .`: failed with 44 issues

The passing test suite is not enough evidence of correctness for Stage 2 because the highest-risk output path is not covered by integration-level tests.

## Final Assessment

You did think through most of the important nuances. The repo does not read like someone missed the core conceptual risks. The real gap is that the implementation has not yet caught up to the level of nuance already present in the design documents.

That is a better problem to have than the reverse.

The next step is not rethinking the whole project. The next step is hardening the contract, environment, and validation layers so the later experimental stages can trust the outputs from this one.
