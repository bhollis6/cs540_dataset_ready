# LLM-as-a-Judge: Historical PR Selection for Agent-Readiness Experiments

## Project Context

We're studying how degrading codebase properties (naming quality, type hints, comments/docstrings, and test surface) affects AI coding agent performance. Our experimental pipeline requires selecting 3-5 high-quality historical PRs per repo that we revert and ask agents to re-solve. Selecting good PRs is a judgment call with multiple criteria, and we need to do it across 10-15 repos with potentially dozens of candidates each. We use LLM-as-a-Judge (point-wise evaluation) to score and filter candidate PRs against a structured rubric.

## LLM-J Technique: Point-wise Evaluation

From the He et al. (2026) LLM-J framework:
- **T (Type):** Point-wise (score each PR independently against a rubric)
- **C (Criteria):** Scope, test coverage, mutation relevance, clarity, complexity
- **X (Item):** A candidate PR (issue description + patch diff + test changes)
- **R (Reference):** None needed (reference-free evaluation)
- **Y (Result):** Graded scores per criterion (1-5)
- **E (Explanation):** Reasoning for each score
- **F (Feedback):** Whether this PR is suitable for our experiments and why/why not

We chose point-wise over pair-wise because we're not ranking PRs against each other. We're filtering: does this PR meet our selection criteria or not. Each PR is evaluated independently against the same rubric.

## What We Need

A Python CLI tool that:
1. Takes candidate PRs scraped from a repo's git history (issue/commit info + patch diff + test diff)
2. Sends each PR to an LLM with a structured evaluation rubric
3. The LLM scores each PR on 5 criteria (1-5 scale) with reasoning
4. Parses responses and writes results to CSV
5. Filters candidates by a configurable score threshold
6. Outputs a ranked shortlist of the best PR candidates per repo

## Input Format

A directory of candidate PRs organized by repo. Each candidate is a JSON file:

```json
{
  "candidate_id": "fastapi_pr_4821",
  "repo": "tiangolo/fastapi",
  "pr_number": 4821,
  "title": "Fix token refresh race condition in OAuth2 middleware",
  "description": "When multiple requests hit the refresh endpoint simultaneously, the middleware could issue duplicate tokens. This PR adds a lock to serialize refresh operations.",
  "patch_diff": "diff --git a/fastapi/security/oauth2.py b/fastapi/security/oauth2.py\n--- a/fastapi/security/oauth2.py\n+++ b/fastapi/security/oauth2.py\n@@ -45,6 +45,15 @@...",
  "test_diff": "diff --git a/tests/test_security_oauth2.py b/tests/test_security_oauth2.py\n--- a/tests/test_security_oauth2.py\n+++ b/tests/test_security_oauth2.py\n@@ -102,6 +102,28 @@...",
  "files_changed": ["fastapi/security/oauth2.py", "tests/test_security_oauth2.py"],
  "source_files": ["fastapi/security/oauth2.py"],
  "test_files": ["tests/test_security_oauth2.py"],
  "test_support_files": [],
  "lines_added": 42,
  "lines_removed": 3,
  "has_test_changes": true
}
```

## Evaluation Rubric

The LLM scores each candidate on 5 criteria, 1-5 scale:

### 1. Scope (1-5)
Is this PR focused on a single coherent change?
- 1: Massive refactor touching dozens of unrelated files
- 3: Mostly focused but includes some unrelated cleanup
- 5: Single clear fix or feature, tightly scoped

### 2. Test Coverage (1-5)
Does this PR include or modify tests that verify the fix?
- 1: No test changes at all
- 3: Some test changes but they don't clearly verify the core fix
- 5: Clear test additions/modifications that directly validate the fix, could serve as pass/fail signal

### 3. Mutation Relevance (1-5)
Does this PR touch code that contains properties we plan to degrade (type hints, meaningful variable names, comments/docstrings, and surrounding test-readable behavior)?
- 1: Touches only config files, CI scripts, or auto-generated code
- 3: Some relevant code but mostly boilerplate
- 5: Core application code with type annotations, descriptive naming, meaningful comments/docstrings, and surrounding tests that would normally expose rich signals before degradation

### 4. Clarity (1-5)
Is the issue description clear enough to hand to an AI coding agent as a task prompt?
- 1: No description, just a commit hash with no context
- 3: Brief description that requires reading the code to understand
- 5: Clear problem statement, expected behavior, reproduction steps or context

### 5. Complexity (1-5)
Is this PR non-trivial but also not unreasonably large?
- 1: One-line typo fix or trivially simple change
- 2: Simple but real fix (a few lines, obvious solution)
- 3: Moderate complexity, requires understanding some context
- 4: Solid engineering task requiring navigation and reasoning
- 5: Too complex, would take a human hours to review (penalize this too)

**Note on Complexity scoring:** We want the sweet spot (3-4). Both 1-2 and 5 are bad for our experiments. Too simple means we can't measure meaningful differences between clean and degraded conditions. Too complex means the agent might fail regardless of codebase quality.

## Judge Output Format

Prompt the LLM to respond in JSON:

```json
{
  "scope": {
    "score": 4,
    "reasoning": "PR is focused on the OAuth2 middleware race condition. Only touches the security module and its tests. Minor: also updates a type alias in utils.py but it's related."
  },
  "test_coverage": {
    "score": 5,
    "reasoning": "Adds 3 new test cases specifically for concurrent token refresh. Tests would fail without the fix and pass with it. Strong pass/fail signal."
  },
  "mutation_relevance": {
    "score": 4,
    "reasoning": "The changed code uses type annotations, descriptive function names (serialize_token_refresh, acquire_refresh_lock), and sits in a well-structured module path. Good candidate for naming and type hint degradation."
  },
  "clarity": {
    "score": 4,
    "reasoning": "Description clearly explains the race condition and the fix approach. Could be slightly more specific about reproduction steps but an agent should understand the task."
  },
  "complexity": {
    "score": 4,
    "reasoning": "Requires understanding the middleware flow, async locking patterns, and how the token refresh cycle works. Non-trivial but well-scoped. Good difficulty level."
  },
  "total_score": 21,
  "recommendation": "ACCEPT",
  "summary": "Strong candidate. Well-scoped fix with clear tests, touches type-annotated code in a structured module. Good complexity for measuring degradation impact."
}
```

Recommendation thresholds:
- **ACCEPT**: total score >= 18 (averaging 3.6+ per criterion)
- **REVIEW**: total score 13-17 (might be usable, flag for manual check)
- **REJECT**: total score < 13 (not suitable for experiments)

## Output

### Per-candidate results CSV (`results.csv`):

| candidate_id | repo | pr_number | scope | test_coverage | mutation_relevance | clarity | complexity | total_score | recommendation | summary |
|---|---|---|---|---|---|---|---|---|---|---|
| fastapi_pr_4821 | tiangolo/fastapi | 4821 | 4 | 5 | 4 | 4 | 4 | 21 | ACCEPT | Strong candidate... |
| fastapi_pr_3102 | tiangolo/fastapi | 3102 | 2 | 1 | 3 | 2 | 1 | 9 | REJECT | Trivial one-line... |

### Per-repo summary CSV (`summary.csv`):

| repo | total_candidates | accepted | review | rejected | top_candidates |
|---|---|---|---|---|---|
| tiangolo/fastapi | 24 | 5 | 8 | 11 | pr_4821, pr_3847, pr_5102, pr_4293, pr_3991 |

### Console output:
Print progress per candidate and a summary per repo showing how many were accepted/reviewed/rejected.

## PR Scraper

We already have candidate repos selected. Include a scraper script that pulls merged PRs from a given GitHub repo and formats them into the candidate JSON format.

The scraper should:
1. Take a GitHub repo (e.g., `tiangolo/fastapi`) and an optional max count
2. Hit the GitHub API to fetch merged PRs
3. For each PR, grab: title, body/description, patch diff, list of changed files, lines added/removed
4. Detect whether the PR includes test changes (look for files in `tests/`, `test_`, `_test.py`, etc.)
5. Split the diff into `patch_diff` (non-test changes) and `test_diff` (test changes)
6. Split test-related paths into:
   - `test_files`: executable/removable tests such as `test_*.py` and `*_test.py`
   - `test_support_files`: preserved infrastructure such as `conftest.py`, fixtures, and helpers
7. For selected and verified manifests, emit `degradation_targets` so Stage 4 can consume explicit edit/delete/preserve lists instead of recomputing policy
8. Output each PR as a JSON file in the candidate format

Pre-filter before sending to the judge to save API calls:
- Skip PRs that only touch docs, CI configs, or markdown files
- Skip PRs with 0 test file changes (we need test coverage as ground truth)
- Skip PRs with fewer than 5 lines changed (too trivial)
- Skip PRs with more than 500 lines changed (too large)

These pre-filters are coarse. The LLM judge does the nuanced evaluation after.

Requires a GitHub personal access token set as `GITHUB_TOKEN` env var.

## Reliability Measurement

To measure how consistent the judge is, run every candidate through the evaluation TWICE with the same prompt. Compute:
- **Per-criterion ICC** (Intraclass Correlation Coefficient) across the two runs
- **Exact agreement rate**: how often the two runs give the same score per criterion
- **Recommendation consistency**: how often the ACCEPT/REVIEW/REJECT label matches between runs

Report these in a separate `reliability.csv`.

This addresses the known point-wise calibration inconsistency issue noted in He et al.'s review. If ICC is high, we can trust the scores. If it's low on certain criteria, we note that as a limitation.

## Tech Stack

- Python 3.10+
- Anthropic API (claude-sonnet-4-20250514) or OpenAI API, configurable via env var or CLI flag
- `argparse` for CLI
- Dependencies: `anthropic` or `openai`, `requests`, `json`, `csv`, `pathlib`, `numpy` (for ICC calculation)
- Keep it simple, no frameworks

## CLI Interface

```bash
# Scrape candidate PRs from a GitHub repo
python scrape_prs.py --repo tiangolo/fastapi --output-dir ./candidates --max-prs 30

# Scrape from multiple repos
python scrape_prs.py --repo tiangolo/fastapi --repo pallets/flask --output-dir ./candidates --max-prs 30

# Run evaluation on all candidates in a directory
python evaluate.py --input-dir ./candidates --output-dir ./results --model anthropic

# Run on a single candidate
python evaluate.py --input-file ./candidates/fastapi_pr_4821.json --output-dir ./results --model anthropic

# Run reliability check (evaluates everything twice, computes ICC)
python evaluate.py --input-dir ./candidates --output-dir ./results --model anthropic --reliability-check
```

## File Structure

```
llm-judge/
├── README.md                # Setup, how to run, how to interpret results, rationale
├── requirements.txt         # anthropic, openai, numpy, requests
├── scrape_prs.py            # Scrapes merged PRs from GitHub repos into candidate JSON files
├── evaluate.py              # Main evaluation script
├── prompts.py               # System prompt and rubric template
├── utils.py                 # JSON parsing, CSV writing, ICC calculation
├── candidates/              # Input directory (scraped PRs go here)
│   ├── fastapi_pr_4821.json
│   ├── fastapi_pr_3102.json
│   └── ...
└── results/                 # Output directory
    ├── results.csv
    ├── summary.csv
    └── reliability.csv
```

## README Should Cover

1. **What this tool does**: Point-wise LLM-as-a-Judge evaluation of candidate PRs for our agent-readiness experiments
2. **Why we chose this technique**: We need to filter dozens of candidate PRs per repo down to the best 3-5. This is a multi-criteria judgment call that doesn't scale manually across 10-15 repos. Point-wise evaluation scores each PR independently against a fixed rubric, which is the right fit when you're filtering rather than ranking. He et al. (2026) document that point-wise evaluation works well when guided by detailed criteria.
3. **Setup**: Install deps, set `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` and `GITHUB_TOKEN` env vars
4. **How to scrape candidate PRs**: Run scrape_prs.py with target repos
5. **How to run evaluation**: Run evaluate.py with flags
6. **How to interpret results**: What scores mean, what the threshold is, what reliability metrics indicate
7. **Reliability measurement**: We run each candidate twice and compute ICC to verify the judge is consistent. This addresses known calibration concerns with point-wise evaluation.
8. **Limitations**: Point-wise calibration inconsistency (mitigated by reliability check), potential self-bias if judge model is same family as coding agent

## Assignment Writeup (Include in README or separate doc)

### Why did you select this technique for your project?

We selected point-wise LLM-as-a-Judge evaluation because our experimental pipeline requires identifying high-quality historical pull requests to use as agent tasks. Each candidate PR must meet multiple criteria simultaneously: it needs to be well-scoped, include test coverage, touch code relevant to our planned degradations, have a clear issue description, and be at an appropriate difficulty level. Evaluating candidates against these criteria manually does not scale across 10-15 repositories with dozens of candidates each. Point-wise evaluation is the right fit because we are filtering candidates against a fixed rubric rather than ranking them against each other. This aligns with the He et al. (2026) framework, which documents that point-wise evaluation performs well when guided by detailed, structured criteria.

### How to measure the results

We measure reliability by running every candidate through the evaluation twice with the same prompt and computing Intraclass Correlation Coefficient across the two runs. This directly addresses the known calibration inconsistency of point-wise evaluation documented in He et al. We also report exact agreement rate per criterion (how often the two runs produce the same score) and recommendation consistency (how often the ACCEPT/REVIEW/REJECT label matches between runs). For the evaluation results themselves, we report score distributions per criterion across all candidates, acceptance rates per repo, and which criteria most frequently caused rejection.

### The results and metrics

Our primary metrics are per-criterion scores (1-5) for scope, test coverage, mutation relevance, clarity, and complexity, aggregated into a total score with an acceptance threshold of 18 out of 25. We report the number of candidates accepted, flagged for review, and rejected per repo. Reliability metrics include ICC per criterion, exact agreement rate, and recommendation consistency rate. We also report which criteria had the lowest average scores across candidates, which tells us something about the nature of our candidate pool (for example, if mutation relevance scores are consistently low, that signals most PRs don't touch code relevant to our experiments and we may need to adjust our repo selection).

## Important Notes

- The system prompt should tell the LLM it is an expert software engineer evaluating whether historical pull requests are suitable for a controlled experiment on AI coding agents. It should be told to evaluate strictly against the rubric and not be generous.
- If the LLM returns malformed JSON, retry once. If it fails again, log the error and skip that candidate.
- Strip any ```json fences from LLM responses before parsing.
- The rubric text should be included verbatim in the prompt so the judge knows exactly what each score level means.
- Complexity scoring is intentionally non-linear (both too simple and too complex are penalized). Make sure the prompt makes this clear.
