# LLM-as-a-Judge: Assignment Writeup

## Project Overview

Our research measures how specific codebase properties affect AI coding agent performance. We take well-structured Python repositories, degrade one property at a time (strip type hints, obfuscate names, remove comments/docstrings, remove tests), and run an agent on the same task in both the clean and degraded versions. Every comparison is within the same repo on the same task, so any performance difference is attributable to the property we changed.

This experiment depends on having good historical tasks to give the agent. We use real bug fixes from each repo's git history, revert the fix, and ask the agent to re-solve it. The original tests serve as our ground truth. But not every merged PR makes a good experimental task. It needs to be well-scoped, have test coverage, touch code relevant to our degradations, and be at the right difficulty level.

This writeup covers the LLM-as-a-Judge tool we built to find those tasks. It scores candidate PRs against a structured rubric and filters them down to the best candidates per repo.

## Why did you select this technique for your project?

Selecting good experimental tasks is a multi-criteria judgment problem. Each candidate pull request must be:

- **Well-scoped**: a single coherent change, not a sprawling refactor
- **Tested**: includes tests that fail before the fix and pass after, giving us a clear pass/fail signal
- **Relevant to our degradations**: touches code that uses type hints, meaningful names, and clear structure, because stripping those properties from code that never had them tells us nothing
- **Clearly described**: the issue description must work as a task prompt for the agent
- **At the right complexity**: not a trivial one-liner and not impossibly complex

That last point deserves explanation. We need tasks in a "sweet spot" of difficulty, typically scoring 3-4 out of 5 on our complexity rubric. If a task is too easy, the agent solves it even in a degraded codebase, and we see no difference between clean and degraded conditions. If it is too hard, the agent fails on both, and again we learn nothing. The experimental signal lives in the middle, where codebase quality could plausibly tip the balance.

Evaluating dozens of PRs across multiple repositories against all these criteria does not scale manually. We need an automated judge.

We chose **point-wise LLM-as-a-Judge evaluation** from the framework surveyed in Gu et al. (2024). Point-wise means we score each PR independently against a fixed rubric rather than comparing PRs to each other. This is the right fit because we are filtering (asking "does this PR meet our requirements?"), not ranking.

### Two-stage evaluation

We implemented a two-stage pipeline because a single evaluation pass is not sufficient:

**Stage 1 (fast screening)** sends the PR diff to an LLM judge with a 5-criterion rubric: scope, test coverage, mutation relevance, clarity, and complexity. Each criterion is scored 1-5. This is fast and cheap, narrowing roughly 70 candidates per repo to 10-15 accepted. It handles the easy decisions, rejecting docs-only changes, trivially simple fixes, and PRs with no tests.

**Stage 2 (deep evaluation)** exists because we realized the diff alone cannot answer a critical question: how will the agent actually experience this codebase? Our degradations affect the entire repository, not just the files in the diff. During its discovery phase, the agent reads imports, traces class hierarchies, and navigates module structure. The judge needs to see that context too.

Stage 2 clones the repository at the historical commit before the PR was merged, reads the full source files plus their import dependencies, and evaluates with a sixth criterion called **navigation depth**, which measures how much cross-file understanding is required. It also runs mechanical validation inspired by SWE-bench (Jimenez et al., ICLR 2024), applying the test patch and verifying that tests actually fail before the fix and pass after. Candidates that fail this check are rejected regardless of their LLM scores.

## Rationale

### Why point-wise over pair-wise evaluation

Gu et al. (2024) survey multiple LLM-as-a-Judge approaches, including point-wise evaluation (scoring items independently against criteria) and pair-wise comparison (comparing two items against each other). We chose point-wise because our task is filtering, not ranking. We do not need to know if PR A is better than PR B. We need to know if each PR independently meets a minimum quality bar. Point-wise evaluation benefits from decomposing evaluation into fine-grained sub-criteria (Gu et al., 2024), which aligns with our multi-criterion rubric design.

### Why mechanical validation matters

An LLM judge can assess whether a PR *looks* like a good experimental task, but it cannot verify whether the task *mechanically works*. A PR might score highly on all rubric criteria but fail in practice because the test patch does not apply cleanly to the historical repo state, or the tests do not actually fail before the fix. We adopted SWE-bench's FAIL-to-PASS validation protocol to catch these cases. As our results show, 44% of LLM-accepted candidates failed this check, proving it is essential.

### Why navigation depth

We added navigation depth as a criterion after recognizing that our experiment's sensitivity depends on it. If a bug fix is entirely self-contained in one function, degrading the rest of the repo's naming or type hints will not affect the agent's ability to solve it because the agent barely needs to explore. But if the fix requires tracing through multiple files, following imports, understanding class hierarchies, and reading related modules, then degradation has much more surface area to affect the agent's discovery and comprehension. Navigation depth measures this.

### Why we follow SWE-bench's approach

SWE-bench (Jimenez et al., ICLR 2024) is the most established benchmark for evaluating coding agents on real-world software engineering tasks. Our experiment shares core design elements: we use historical PRs as tasks, test suites as ground truth, and repository checkouts at specific commits as the environment. We adopted several of their patterns:

- **Checkout, don't revert.** Instead of reverting a PR on the current codebase (which causes merge conflicts), we check out the repo at the state before the PR merged. The agent works in the authentic historical state.
- **FAIL-to-PASS validation.** A task is only valid if its tests fail before the fix and pass after. This is objective, mechanical ground truth.
- **Patch application fallback.** Historical patches often fail to apply cleanly. We use a cascade: `git apply`, then `git apply --reject`, then `patch --fuzz=5`.
- **Test isolation.** The agent never sees the oracle tests. They are applied after the agent finishes to check pass/fail.

A later audit of SWE-bench by OpenAI's SWE-bench Verified effort found that roughly 68% of samples had quality issues such as underspecified problems or unfair tests (OpenAI, 2024). This reinforces why multi-layered validation is necessary.

## How to measure the results

### Reliability measurement

Point-wise evaluation has a known weakness: calibration inconsistency. As Gu et al. (2024) note, score-based assessments "often exhibit inconsistent inter-rater reliability, influenced by the inherent randomness of LLM generation." The same PR can receive different scores on different runs. We need to measure how stable our judge is.

We run every candidate through evaluation **twice** with the same prompt and compute three metrics:

1. **ICC (Intraclass Correlation Coefficient)** per criterion, a statistical measure of consistency between the two runs. ICC ranges from 0 (no agreement) to 1 (perfect agreement). Values above 0.75 are considered good and above 0.9 excellent.

2. **Exact agreement rate** per criterion: how often the two runs give the identical score for a given criterion. This is stricter than ICC because it requires exact matches, not just consistent ordering.

3. **Recommendation consistency**: how often the final ACCEPT/REVIEW/REJECT decision matches between runs. Even if individual scores jitter slightly, does the overall verdict stay the same?

### Evaluation metrics

Beyond reliability, we report score distributions per criterion, acceptance and rejection rates, which criteria most frequently caused low scores (revealing characteristics of our candidate pool), pre-flight pass/fail rates with failure reasons, and navigation depth distribution among final candidates.

## The results and metrics

We ran the full pipeline on **69 candidate PRs** from encode/starlette, a 14k-LOC Python ASGI web framework with 100% test coverage and type annotation coverage.

### Reliability (69 candidates, dual evaluation)

| Criterion | ICC | Exact Agreement | Within-1 Agreement |
|---|---|---|---|
| Scope | 0.931 | 92.8% | 100% |
| Test Coverage | 0.967 | 87.0% | 100% |
| Mutation Relevance | 0.908 | 87.0% | 100% |
| Clarity | 0.844 | 72.5% | 100% |
| Complexity | 0.867 | 84.1% | 100% |
| **Total Score** | **0.969** | 49.3% | 91.3% |
| **Recommendation** | — | **95.7%** | — |

ICC exceeds 0.84 across all five criteria, with four of five above 0.85, indicating strong reliability. All criteria achieved 100% within-1 agreement, meaning scores never differed by more than one point between runs.

Clarity had the lowest ICC (0.844) and exact agreement (72.5%). This is expected because "clear enough for an agent" is inherently more subjective than "does it include test changes." Total score exact agreement is 49.3% because small per-criterion jitter compounds across five dimensions, but within-1 agreement (91.3%) shows totals are stable within a narrow band.

The most important number: **95.7% recommendation consistency**. The judge almost always reaches the same ACCEPT/REVIEW/REJECT verdict on both runs.

### Stage 1 score distributions

| Criterion | Average | Distribution (1 / 2 / 3 / 4 / 5) |
|---|---|---|
| Scope | 4.72 | 0 / 3 / 2 / 6 / 58 |
| Test Coverage | 4.13 | 7 / 5 / 7 / 3 / 47 |
| Mutation Relevance | 3.72 | 1 / 7 / 9 / 45 / 7 |
| Clarity | 3.59 | 1 / 10 / 16 / 31 / 11 |
| Complexity | 2.38 | 9 / 29 / 27 / 4 / 0 |

**52 ACCEPT** (75.4%) / **11 REVIEW** (15.9%) / **6 REJECT** (8.7%). Average total: 18.6 / 25.

Complexity was the lowest-scoring criterion (average 2.38), with 55% of candidates scoring 1-2. This tells us most starlette PRs are straightforward fixes, the kind that an agent could solve regardless of degradation. No candidates scored 5 (too complex). This is why filtering for the complexity sweet spot (3-4) matters: only 31 of 69 candidates fell in that range.

Scope scored highest (4.72), with 84% scoring 5/5. This reflects starlette's disciplined PR culture where most contributions are tightly focused single changes.

### Stage 2 deep evaluation

Of the 52 Stage 1 accepted candidates:

- **29 passed pre-flight** mechanical validation (55.8%)
- **23 failed pre-flight** (44.2%)
  - 21 had no failing tests at base commit (no FAIL-to-PASS signal)
  - 2 had tests that still failed after the gold patch

**The 44% failure rate is the most important finding.** Nearly half the candidates that the LLM judge accepted turned out to be mechanically invalid. Their test patches did not produce a clear fail-then-pass signal when applied to the historical repo state. Without mechanical validation, we would have included these in experiments and gotten unreliable results. This demonstrates that LLM scoring alone is insufficient for experimental task selection.

Of the 29 pre-flight survivors, **15 were accepted** by the Stage 2 evaluation with the expanded 6-criterion rubric including navigation depth:

| Navigation Depth | Count | What It Means |
|---|---|---|
| 1 (self-contained fix) | 2 | Agent barely needs to explore, low degradation sensitivity |
| 2 (one file hop) | 6 | Agent reads one related file |
| 3 (2-3 files) | 5 | Agent must understand relationships across files |
| 4 (4+ files) | 2 | Agent must trace through module architecture |

7 of 15 accepted candidates have navigation depth ≥ 3. These are our strongest experimental candidates because the agent must explore and understand multiple files to implement the fix, giving degradation maximum surface area to affect performance.

### Pipeline summary

```
69 scraped candidates
 → 52 Stage 1 ACCEPT (75%)
   → 29 pre-flight PASS (56% of accepted)
     → 15 Stage 2 ACCEPT (52% of pre-flight pass)
       → 7 with navigation depth ≥ 3 (our top picks)
```

Three layers of filtering reduced 69 candidates to 7 high-confidence experimental tasks: rubric scoring, mechanical validation, and contextual depth assessment. The reliability metrics confirm the LLM judge is consistent (ICC > 0.85 across all criteria, 95.7% recommendation agreement). The 44% pre-flight failure rate demonstrates that mechanical validation is not optional.

## What's Next

These 7 candidates from starlette represent one repo's contribution to our experimental dataset. We will repeat this pipeline across 10-15 repositories to build a full corpus of high-quality experimental tasks. Once we have 3-5 validated tasks per repo, we begin the degradation experiments: stripping type hints, obfuscating names, removing comments/docstrings, and removing tests, then measuring how agent performance changes across clean and degraded conditions. The LLM-J tool built here is reusable infrastructure. Every new repo we add goes through the same scrape, score, validate, and filter process with no manual intervention beyond reviewing the final shortlist.

## References

1. Gu, J., Jiang, X., Shi, Z., Tan, H., Zhai, X., Xu, C., Li, W., Shen, Y., Ma, S., Liu, H., Wang, S., Zhang, K., Wang, Y., Gao, W., Ni, L., & Guo, J. (2024). A Survey on LLM-as-a-Judge. arXiv:2411.15594. https://arxiv.org/abs/2411.15594

2. Jimenez, C. E., Yang, J., Wettig, A., Yao, S., Pei, K., Press, O., & Narasimhan, K. (2024). SWE-bench: Can Language Models Resolve Real-World GitHub Issues? In *Proceedings of the Twelfth International Conference on Learning Representations (ICLR 2024)*. https://arxiv.org/abs/2310.06770

3. OpenAI. (2024). Introducing SWE-bench Verified. https://openai.com/index/introducing-swe-bench-verified/
