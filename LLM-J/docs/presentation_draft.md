# LLM-as-a-Judge: Presentation Draft

---

## Slide 1: Title

**LLM-as-a-Judge: Selecting Experimental Tasks for Agent-Readiness Research**

CS 540 | [Your names] | Spring 2026

**Talking points:**
- Quick overview of what we built and why
- Part of a larger experiment measuring how codebase quality affects AI coding agents

---

## Slide 2: The Big Picture

**How does codebase quality affect AI coding agents?**

- Take well-structured Python repos
- Degrade one property at a time: type hints, naming, directory structure, tests
- Run an agent on the same bug fix task, clean vs degraded
- Same repo, same task, only the degradation changes

**Talking points:**
- We never compare repo A to repo B, always clean vs degraded within the same repo
- If the agent struggles more on degraded code, that property matters
- The whole experiment depends on having good tasks to give the agent

---

## Slide 3: The Problem

**How do we find good experimental tasks?**

We need historical bug fixes from real repos where:
- The fix is well-scoped (not a massive refactor)
- Tests verify the fix (pass/fail ground truth)
- The code is relevant to our degradations (has type hints, good naming)
- The issue description is clear enough to hand to an agent
- Complexity is in the "sweet spot" (not trivial, not impossible)

Dozens of PRs per repo. Manual review doesn't scale.

**Talking points:**
- Sweet spot: too easy and degradation doesn't matter, too hard and the agent fails regardless
- We need the middle ground where codebase quality could tip the balance
- This is where LLM-as-a-Judge comes in

---

## Slide 4: Our Technique — Point-wise LLM-as-a-Judge

**Point-wise evaluation** (Gu et al., 2024): score each item independently against a rubric

- Not pair-wise (we're filtering, not ranking)
- Each PR scored on 5 criteria, 1-5 scale
- ACCEPT ≥ 18/25 | REVIEW 13-17 | REJECT < 13

| Criterion | What It Measures |
|---|---|
| Scope | Single coherent change? |
| Test Coverage | Tests verify the fix? |
| Mutation Relevance | Code uses type hints, good naming? |
| Clarity | Description works as agent prompt? |
| Complexity | Sweet spot (3-4)? |

**Talking points:**
- Point-wise is the right fit because we're asking "does this PR meet our bar" not "is PR A better than PR B"
- The rubric is specific to our experiment, not generic quality

---

## Slide 5: Two-Stage Pipeline

```
69 scraped PRs
    ↓
[Stage 1] Score on diffs → 52 accepted
    ↓
[Stage 2] Clone repo, checkout historical state,
          read full files, run FAIL-to-PASS tests → 15 verified
    ↓
7 top candidates (navigation depth ≥ 3)
```

**Talking points:**
- Stage 1 is fast and cheap, uses only the diff
- But the diff doesn't show what the agent actually sees — the whole repo gets degraded
- Stage 2 checks out the actual historical repo, reads full source files, adds a 6th criterion: navigation depth
- Stage 2 also runs mechanical validation inspired by SWE-bench

---

## Slide 6: Why Two Stages?

**Stage 1 can't answer:** "Will degradation actually affect this task?"

- Agent explores the whole repo, not just the diff
- If the fix is self-contained in one function, degrading the rest doesn't matter
- We need to see the full files to judge navigation depth

**Stage 2 adds:**
- Full source file context (not just diffs)
- Navigation depth criterion (how much cross-file understanding?)
- Mechanical FAIL-to-PASS validation (does the task actually work?)

**Talking points:**
- Navigation depth is key to experimental sensitivity
- A task requiring 4+ files of understanding gives degradation more surface area

---

## Slide 7: SWE-bench Patterns We Adopted

Followed SWE-bench (Jimenez et al., ICLR 2024) methodology:

1. **Checkout, don't revert** — go to the historical state, don't try to undo on current code
2. **FAIL-to-PASS validation** — tests must fail before fix, pass after
3. **Patch fallback cascade** — `git apply` → `git apply --reject` → `patch --fuzz=5`
4. **Test isolation** — agent never sees the oracle tests

**Talking points:**
- Reverting on the current codebase causes merge conflicts — checking out the historical commit avoids this entirely
- SWE-bench's own audit found 68% of their initial samples had quality issues
- We adopted their mechanical validation to catch the same kind of problems

---

## Slide 8: Reliability — How Consistent Is the Judge?

Every candidate evaluated **twice**, same prompt. Computed ICC across runs.

| Criterion | ICC | Exact Agreement |
|---|---|---|
| Scope | 0.931 | 92.8% |
| Test Coverage | 0.967 | 87.0% |
| Mutation Relevance | 0.908 | 87.0% |
| Clarity | 0.844 | 72.5% |
| Complexity | 0.867 | 84.1% |
| **Recommendation** | — | **95.7%** |

**Talking points:**
- ICC above 0.85 on all criteria, which is strong
- Clarity is the most subjective, lowest ICC — makes sense
- Most importantly: 95.7% of the time, the judge gives the same ACCEPT/REVIEW/REJECT verdict
- This addresses the known calibration weakness of point-wise evaluation

---

## Slide 9: Results — Score Distributions

| Criterion | Average |
|---|---|
| Scope | 4.72 |
| Test Coverage | 4.13 |
| Mutation Relevance | 3.72 |
| Clarity | 3.59 |
| **Complexity** | **2.38** |

52 ACCEPT / 11 REVIEW / 6 REJECT out of 69 candidates

**Talking points:**
- Complexity was the lowest scorer — most starlette PRs are simple fixes
- This is why filtering for the sweet spot matters, only 31 of 69 hit the 3-4 range
- High scope scores reflect starlette's disciplined PR culture

---

## Slide 10: The Key Finding — Mechanical Validation Matters

**44% of LLM-accepted candidates failed pre-flight validation**

- 21 had no failing tests at the base commit
- 2 had tests that still failed after the gold patch
- These PRs scored well on the rubric but are mechanically broken

LLM scoring alone is not enough.

**Talking points:**
- This is the most important result
- Nearly half the candidates the judge liked turned out to be unusable
- Without this check we'd have bad data in our experiments
- Validates our decision to add SWE-bench-style mechanical validation

---

## Slide 11: Navigation Depth — Experimental Sensitivity

Of 15 Stage 2 accepted candidates:

| Navigation Depth | Count |
|---|---|
| 1 (self-contained) | 2 |
| 2 (one file hop) | 6 |
| 3 (2-3 files) | 5 |
| 4 (4+ files) | 2 |

**7 candidates with depth ≥ 3** — our strongest picks for degradation experiments

**Talking points:**
- Navigation depth tells us how much the agent needs to explore
- Higher depth = more exposure to degraded code during discovery
- These 7 are where we expect degradation to have the most measurable impact

---

## Slide 12: Pipeline Summary

```
69 scraped candidates
 → 52 Stage 1 ACCEPT (75%)
   → 29 pre-flight PASS (56%)
     → 15 Stage 2 ACCEPT (52%)
       → 7 with nav depth ≥ 3 (top picks)
```

Three layers: rubric scoring, mechanical validation, contextual depth assessment

**Talking points:**
- Each layer catches things the others miss
- Rubric catches bad PRs, pre-flight catches broken PRs, navigation depth catches low-sensitivity PRs
- The tool is reusable — every new repo goes through the same pipeline

---

## Slide 13: What's Next

- Run pipeline across all target repos (starlette, httpx, cattrs)
- 3-5 verified tasks per repo
- Begin degradation experiments: strip type hints, obfuscate names, flatten directories, remove tests
- Measure agent performance: bootstrap efficiency, task success, token usage

**Talking points:**
- The LLM-J tool is reusable infrastructure for the rest of the experiment
- Adding a repo is just one command, no manual review needed beyond the final shortlist
- Next stages will use the verified manifests this tool produces

---

## Slide 14: References

1. Gu et al. (2024). A Survey on LLM-as-a-Judge. arXiv:2411.15594
2. Jimenez et al. (2024). SWE-bench: Can Language Models Resolve Real-World GitHub Issues? ICLR 2024
3. OpenAI (2024). Introducing SWE-bench Verified
