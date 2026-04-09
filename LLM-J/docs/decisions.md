# Decisions & Rationale

This document explains the techniques, design decisions, and reasoning behind the LLM-Judge PR selection pipeline. It serves as both a reference for collaborators and a record of what we learned along the way.

---

## 1. What This Tool Does

We're building the PR selection stage (Stage 3) of a larger experiment measuring how codebase properties affect AI coding agent performance. The tool:

1. Scrapes merged PRs from GitHub repos
2. Pre-filters with heuristics
3. Evaluates candidates with an LLM judge (Stage 1: diffs, Stage 2: full repo context)
4. Validates candidates mechanically (SWE-bench style FAIL_TO_PASS checks)
5. Outputs a verified set of 5 PRs per repo for downstream experimentation

---

## 2. Why LLM-as-a-Judge (Point-wise Evaluation)

We selected point-wise LLM-as-a-Judge from the Gu et al. (2024) framework:

- **T (Type):** Point-wise — score each PR independently against a rubric
- **C (Criteria):** Scope, test coverage, mutation relevance, clarity, complexity (+ navigation depth in Stage 2)
- **X (Item):** A candidate PR
- **R (Reference):** None (reference-free)
- **Y (Result):** Graded scores per criterion (1-5)

**Why point-wise over pair-wise:** We're filtering ("does this PR meet our criteria?"), not ranking ("is PR A better than PR B?"). Each PR is evaluated independently against the same rubric. Point-wise is the right fit per He et al. when filtering with structured criteria.

**Known limitation:** Point-wise calibration is inconsistent — the same PR can score differently across runs. We measured this: PR #115 in cattrs scored 16 on one run and 20 on the next. The `--reliability-check` flag (dual evaluation + ICC) quantifies this inconsistency.

---

## 3. Two-Stage Evaluation Design

### Stage 1: Fast Screening (diff-based)

**Input:** 169 candidate PRs (scraped from GitHub)
**What the judge sees:** PR title, description, patch diff, test diff, file lists
**Output:** ~10-15 accepted candidates per repo

Stage 1 is sufficient for filtering out obviously bad PRs: docs-only changes, trivial one-liners, PRs with no tests, unclear descriptions. The diff alone answers these questions well.

**Why diffs are enough for Stage 1:** Scope, test coverage, clarity, and basic complexity can all be assessed from diffs. We're not trying to deeply assess how the agent will experience the codebase — just filtering out noise.

### Stage 2: Deep Evaluation (full repo context + mechanical validation)

**Input:** ~10-15 accepted PRs per repo from Stage 1
**What the judge sees:** Full source files at `base_commit_sha`, first-degree import dependencies, the diff, test diff, and pre-flight validation results
**Output:** Final 5 verified PRs per repo

**Why Stage 2 exists:** The user identified a critical gap — the experiment degrades the *entire* repo, not just the files in the diff. An agent solving a PR will explore imports, class hierarchies, and related modules during its discovery phase. The judge needs to see those files to assess whether the task requires enough cross-file navigation that degradation would actually matter.

**Navigation Depth criterion (new in Stage 2):**
- 1: Fix is self-contained in one function
- 3: Need to understand 2-3 files and their relationships
- 5: Need to trace through multiple modules, class hierarchies, or architectural patterns

This is the key criterion for experimental sensitivity — we need tasks complex enough that degradation *could tip the balance*, but not so complex that the agent fails regardless.

---

## 4. What We Learned from SWE-bench

Our experiment shares core design with SWE-bench (Princeton, ICLR 2024). We studied their methodology and adopted several patterns:

### 4.1 Environment Setup: Checkout, Don't Revert

**Problem:** We initially planned to `git revert` PRs on the current codebase. This breaks because subsequent commits modify the same code, causing merge conflicts.

**SWE-bench's solution:** Check out the repo at `base_commit` (the state before the PR merged). The agent works in the historical repo state.

**What we adopted:**
- `git reset --hard base_commit_sha`
- Remove git remote (agent can't see future commits)
- Delete tags pointing to commits after the base commit
- Expire reflog, garbage collect
- This gives the agent an authentic view of the repo as it existed when the PR was created

### 4.2 Test Oracle: FAIL_TO_PASS Validation

**Problem:** How do we know a PR is a valid experimental task? Just because it has test changes doesn't mean those tests actually exercise the bug.

**SWE-bench's approach:**
1. At `base_commit + test_patch`: run tests → some must FAIL (the bug exists)
2. At `base_commit + test_patch + gold_patch`: run tests → they must PASS (the fix works)
3. Tests that go from FAIL → PASS are the ground truth signal

**What we adopted:** Stage 2 pre-flight validation runs this exact check. Candidates without FAIL_TO_PASS tests are rejected — they can't serve as valid experimental tasks regardless of how good they look to the LLM judge.

### 4.3 Patch Application Fallback

**Problem:** `git apply` frequently fails on historical patches due to whitespace, encoding, or context differences.

**SWE-bench's fallback cascade:**
1. `git apply --verbose`
2. `git apply --verbose --reject`
3. `patch --batch --fuzz=5 -p1`

**What we adopted:** Same cascade. Some candidates will still fail — that's acceptable. We document the failure and move on.

### 4.4 What SWE-bench Got Wrong (and we can avoid)

- **68% of SWE-bench samples were flagged** for underspecified problems or unfair tests (OpenAI's Verified audit)
- **32% of "solutions" were provided in issue comments** — agents could cheat by reading hints
- Tests checking exact error message strings were unfairly specific

Our mitigation: the LLM judge's Clarity criterion catches underspecified descriptions, and Stage 2's mechanical validation catches cases where tests don't actually exercise the bug.

---

## 5. Test Degradation Decision

**Decision:** YES, degrade existing test files along with source code.

**Rationale:** If we strip type hints from source but leave test files pristine, the agent can read the tests and recover type information for free. This defeats the purpose of the degradation.

**How it works:**
- **Existing test files** in the repo → degraded (they're part of the codebase the agent explores)
- **The PR's new tests** (oracle) → never degraded. The agent never sees them. They're applied after the agent finishes to check pass/fail. They're our measurement instrument.

This is a clean separation: everything the agent sees is degraded, the oracle stays clean.

---

## 6. PR Age and Repo Maturity

**Problem:** Old PRs (e.g., cattrs PR #25 from 2018) may come from when the codebase was immature — no type hints, poor structure, volatile API. Degrading an already-messy codebase won't show meaningful differences.

**Solution (two layers):**
1. **Date floor filter** in Stage 1: `--min-date 2022-01-01` (configurable). Coarse but cheap.
2. **Base state quality check** in Stage 2: When we checkout `base_commit_sha`, we can assess whether the repo at that point has the properties we plan to degrade. If it's already messy, the candidate is useless regardless of date.

---

## 7. Provider Architecture

**Default:** Claude Code CLI (`claude -p`) using the Max plan subscription. No API key needed.

**Why CLI over API:** The user has Claude Max with unlimited usage. Using the CLI avoids API key management and uses existing subscription credits.

**Model defaults:**
- Stage 1: Sonnet 4.6 (`claude-sonnet-4-6`) — fast, plenty smart for diff-based screening
- Stage 2: Opus 4.6 (`claude-opus-4-6`) recommended — better reasoning for full-context evaluation with 1M context window
- Switchable via `--sonnet` / `--opus` flags

**Other providers:** OpenRouter supported for alternative models (DeepSeek, etc.) via `--provider openrouter --model <model>`.

---

## 8. Clone Management

**Strategy:** One bare clone per repo, git worktrees per candidate.

**Why bare clone:** Stores only git objects (no working tree). Serves as a shared object database for all worktrees. We never accidentally modify it.

**Why worktrees over sequential checkouts:**
- Isolation: a failed cleanup doesn't dirty the state for the next candidate
- Disposable: delete and recreate if anything goes wrong
- Lightweight: worktrees share the object database, each is just a working directory
- Could enable parallel evaluation in the future

**Lifecycle:** Clone once per repo → create worktree for candidate → pre-flight + evaluate → destroy worktree → next candidate. Clones live in `clones/` (gitignored).

---

## 9. Heuristic Pre-filters

Applied during scraping (zero LLM cost):

| # | Filter | Rationale |
|---|--------|-----------|
| 1 | Has test file changes | Need tests as ground truth |
| 2 | Not test-only | Must touch source code |
| 3 | 5-500 lines changed | Not trivial, not massive |
| 4 | ≤20 files changed | Not a refactor |
| 5 | Has description (≥20 chars) | Need a task prompt for the agent |
| 6 | Merged after min_date | Repo maturity |
| 7 | Not a bot PR | Dependabot/renovate aren't real tasks |

These reduced 300 PRs per repo to ~40-70 candidates. The LLM judge handles nuanced evaluation after.

---

## 10. Reliability Measurement

**Method:** Run each candidate through evaluation twice with identical prompts. Compute:
- ICC(3,1) per criterion — Intraclass Correlation Coefficient
- Exact agreement rate — how often two runs give the same score
- Recommendation consistency — how often ACCEPT/REVIEW/REJECT matches

**Why:** Point-wise evaluation has known calibration inconsistency (He et al., 2026). If ICC is high, we trust the scores. If low on specific criteria, we note it as a limitation.

**Observation:** PR #115 scored 16 on first run, 20 on second. A 4-point swing (16% of total) on the same PR with the same prompt. This reinforces why mechanical validation (FAIL_TO_PASS) is essential — we can't rely solely on LLM scoring.

---

## 11. Data Flow

```
GitHub repos
    │
    ▼
[Scraper] ── GraphQL bulk metadata ──► Heuristic pre-filters
    │                                       │
    │                              REST diff fetch (survivors)
    │                                       │
    ▼                                       ▼
candidates/*.json ──────────────────► [Stage 1: LLM Judge]
                                            │
                                    results/results.csv
                                    results/*_selected_prs.json
                                            │
                                            ▼
                                   [Stage 2: Deep Evaluation]
                                     ├── Clone + checkout base_commit
                                     ├── Read full source files + imports
                                     ├── Pre-flight FAIL_TO_PASS validation
                                     └── Expanded LLM evaluation (6 criteria)
                                            │
                                            ▼
                                   deep_results/*_verified_manifest.json
                                            │
                                            ▼
                                   Stage 4: Codebase Mutation
                                   Stage 5: Agent Task Runs
                                   Stage 6: Log Parsing
                                   Stage 7: Analysis
```
