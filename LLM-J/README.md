# LLM-as-a-Judge: PR Selection Pipeline

Selects high-quality historical PRs from GitHub repos for agent-readiness degradation experiments. Uses point-wise LLM-as-a-Judge evaluation with a two-stage pipeline: fast diff-based screening followed by deep evaluation with full repo context and mechanical FAIL-to-PASS validation.

## Quick Start

```bash
# 1. Install
pip install -e ".[dev]"

# 2. Set up your .env (copy from template)
cp .env.example .env
# Edit .env — you need GITHUB_TOKEN at minimum
# No API key needed if using Claude Code (default)

# 3. Scrape PRs from our target repos
python -m src.cli scrape --repos-file repos.json --output-dir ./candidates

# 4. Stage 1: Score candidates with LLM judge
python -m src.cli evaluate --input-dir ./candidates --output-dir ./results

# 5. Stage 2: Deep evaluation + mechanical validation
python -m src.cli deep-evaluate --candidates-dir ./candidates --results-dir ./results --output-dir ./deep_results
```

## What's Already Done

If results already exist from a previous run, **don't re-run** — that wastes LLM calls. Check these directories:

| Directory | Contents | Re-run? |
|---|---|---|
| `candidates/` | Scraped PR JSON files (169 total) | Only if adding repos |
| `results/` | Stage 1 scores, CSVs, manifests | Only if re-scoring |
| `deep_results/` | Stage 2 verified manifests with FAIL_TO_PASS validation | Only if re-evaluating |

## How It Works

### The Pipeline

```
GitHub repos (repos.json)
    │
    ▼
[1. Scrape] ─── GraphQL metadata ──► Heuristic pre-filters ──► REST diff fetch
    │                                                               │
    ▼                                                               ▼
candidates/*.json ─────────────────────────────────────► [2. Stage 1: LLM Judge]
    (169 PRs)                                              Score on 5 criteria
                                                           (diff-based, fast)
                                                                │
                                                                ▼
                                                    results/results.csv
                                                    results/*_selected_prs.json
                                                      (~10-15 ACCEPT per repo)
                                                                │
                                                                ▼
                                                    [3. Stage 2: Deep Evaluation]
                                                      ├── Clone repo
                                                      ├── Checkout base_commit
                                                      ├── Read full source files
                                                      ├── Pre-flight FAIL_TO_PASS validation
                                                      └── Expanded LLM eval (6 criteria)
                                                                │
                                                                ▼
                                                    deep_results/*_verified_manifest.json
                                                      (final 5 PRs per repo)
```

### Stage 1: Fast Screening

Scores each candidate PR on 5 criteria using only the diff:

| Criterion | What It Measures | Ideal |
|---|---|---|
| **Scope** | Single coherent change? | 4-5 |
| **Test Coverage** | Tests directly validate the fix? | 4-5 |
| **Mutation Relevance** | Touches code with type hints, good naming? | 4-5 |
| **Clarity** | Description clear enough for an agent? | 4-5 |
| **Complexity** | Non-trivial but not impossibly large? | 3-4 |

**Thresholds** (total out of 25): ACCEPT ≥18 | REVIEW 13-17 | REJECT <13

### Stage 2: Deep Evaluation

For the ~10-15 accepted PRs per repo, Stage 2:

1. **Clones the repo** and checks out `base_commit_sha` (the state before the PR)
2. **Reads full source files** the PR touches + first-degree imports
3. **Runs pre-flight validation** (SWE-bench style):
   - Applies test patch → runs pytest → confirms tests FAIL (bug exists)
   - Applies gold patch → runs pytest → confirms tests PASS (fix works)
   - PRs without FAIL→PASS tests are rejected
4. **Re-evaluates with 6 criteria** (adds Navigation Depth: how much cross-file understanding does the agent need?)

**Thresholds** (total out of 30): ACCEPT ≥22 | REVIEW 16-21 | REJECT <16

## Target Repos

Defined in `repos.json`:

| Repo | Domain | ~LOC |
|---|---|---|
| encode/starlette | Web framework | 14k |
| encode/httpx | HTTP client | 14k |
| python-attrs/cattrs | Data serialization | 8-12k |

## CLI Reference

### `scrape` — Fetch PRs from GitHub

```bash
# From repos.json
python -m src.cli scrape --repos-file repos.json --output-dir ./candidates

# Specific repos
python -m src.cli scrape --repo encode/starlette --repo encode/httpx --output-dir ./candidates
```

| Flag | Default | Description |
|---|---|---|
| `--repos-file` | — | JSON file with repo list |
| `--repo` | — | GitHub repo (owner/name), repeatable |
| `--output-dir` | `candidates` | Where to write candidate JSON files |
| `--max-prs` | 300 | Max merged PRs to fetch per repo |
| `--min-date` | `2022-01-01` | Skip PRs merged before this date |
| `--min-lines` | 5 | Min lines changed |
| `--max-lines` | 500 | Max lines changed |
| `--max-files` | 20 | Max files changed |
| `--no-skip-bot-prs` | — | Include bot PRs |

### `evaluate` — Stage 1 LLM scoring

```bash
# All candidates
python -m src.cli evaluate --input-dir ./candidates --output-dir ./results

# One repo
python -m src.cli evaluate --input-dir ./candidates --output-dir ./results --repo starlette

# Test with a few first
python -m src.cli evaluate --input-dir ./candidates --output-dir ./results --repo cattrs --max-candidates 5

# Reliability check (runs everything twice, computes ICC)
python -m src.cli evaluate --input-dir ./candidates --output-dir ./results --reliability-check
```

| Flag | Default | Description |
|---|---|---|
| `--input-dir` | `candidates` | Directory with candidate JSON files |
| `--output-dir` | `results` | Where to write results |
| `--repo` | — | Filter to one repo |
| `--max-candidates` | — | Limit number of candidates |
| `--provider` | `claude-code` | `claude-code`, `anthropic`, or `openrouter` |
| `--sonnet` / `--opus` | sonnet | Model shortcut |
| `--reliability-check` | false | Run twice, compute ICC |

### `deep-evaluate` — Stage 2 deep evaluation

```bash
# Full deep evaluation
python -m src.cli deep-evaluate --candidates-dir ./candidates --results-dir ./results --output-dir ./deep_results

# Pre-flight only (no LLM calls — check which PRs are mechanically valid)
python -m src.cli deep-evaluate --candidates-dir ./candidates --results-dir ./results --output-dir ./deep_results --preflight-only

# One repo
python -m src.cli deep-evaluate --candidates-dir ./candidates --results-dir ./results --output-dir ./deep_results --repo cattrs

# Use Opus for deeper reasoning
python -m src.cli deep-evaluate --candidates-dir ./candidates --results-dir ./results --output-dir ./deep_results --opus
```

### `audit-naming` — Repo-level naming readiness audit

```bash
python -m src.cli audit-naming --repo encode/httpx --output-dir ./audit_results
python -m src.cli audit-naming --repo encode/starlette --output-dir ./audit_results --live
```

This command creates a disposable worktree from the repo clone, runs the sibling naming audit, and writes a wrapped readiness report. `--live` uses `uv` + `rope` automatically and should only be used on disposable worktrees.

### `audit-repo` — Repo-level degradation readiness screen

```bash
python -m src.cli audit-repo --repo encode/httpx --output-dir ./audit_results
```

This command creates a disposable worktree and writes a repo-level readiness packet covering:
- type-hint surface
- comments/docstrings surface
- remove-tests viability
- dry-run naming surface

Use `audit-repo` as the broad static screen, then `audit-naming --live` for a deeper naming-specific check when a repo looks promising.

### `build-packet` — Human-review experiment packet

```bash
python -m src.cli build-packet --repo encode/httpx --results-dir ./results --deep-results-dir ./deep_results --readiness-dir ./audit_results --output-dir ./packets
```

This command assembles one repo-level review packet by combining:
- Stage 1 selected PR manifest
- Stage 2 verified manifest
- repo readiness report
- naming readiness report

The output is meant to be the single artifact a human reviews before approving Stage 4 / Stage 5 runs. It now writes both:
- `{repo}_experiment_packet.json`
- `{repo}_experiment_packet.md`

The packet includes an admission rubric with explicit criteria for:
- repo static surface viability
- Stage 1 task-pool depth
- Stage 2 verified-task depth
- naming live-audit readiness

| Flag | Default | Description |
|---|---|---|
| `--candidates-dir` | `candidates` | Candidate JSON files from scrape |
| `--results-dir` | `results` | Stage 1 results (manifests) |
| `--output-dir` | `deep_results` | Where to write deep results |
| `--clones-dir` | `clones` | Where to store bare git clones |
| `--repo` | — | Filter to one repo |
| `--preflight-only` | false | Only run mechanical validation, skip LLM |
| `--skip-preflight` | false | Only run LLM eval, skip mechanical validation |
| `--context-budget` | no limit | Max chars for source context |
| `--sonnet` / `--opus` | sonnet | Model shortcut |

## Output Files

### Stage 1 (`results/`)

| File | What's In It |
|---|---|
| `results.csv` | All candidates: scores per criterion, recommendation, summary |
| `results_detailed.json` | Same as CSV but with full per-criterion reasoning |
| `summary.csv` | Per-repo counts: accepted, review, rejected |
| `{repo}_selected_prs.json` | Manifest of accepted PRs with git SHAs and degradation targets for Stage 2 / Stage 4 |
| `reliability.csv` | ICC and agreement metrics (only with `--reliability-check`) |

### Stage 2 (`deep_results/`)

| File | What's In It |
|---|---|
| `{repo}_deep_results.json` | Full results: preflight status, 6-criterion scores, reasoning |
| `{repo}_verified_manifest.json` | **Final output** — only PRs that passed both preflight AND LLM eval |
| `{repo}_naming_readiness.json` | Repo-level naming degradation audit summary |
| `{repo}_repo_readiness.json` | Repo-level static degradation readiness summary |
| `{repo}_experiment_packet.json` | Combined human-review packet for repo admission |
| `{repo}_experiment_packet.md` | Human-readable review packet summary |

The selected and verified manifests include `base_commit_sha`, `source_files`, `test_files`, `test_support_files`, and a `degradation_targets` block for each accepted PR. `test_files` are removable executable tests; `test_support_files` are preserved test infrastructure such as `conftest.py`, fixtures, and helpers. `degradation_targets` makes the Stage 4 policy explicit by listing which files each degradation should edit or preserve.

See [docs/degradation_contract.md](/home/caden/cs540_dataset_ready/LLM-J/docs/degradation_contract.md:1) for the current Stage 3 → Stage 4 handoff rules.

## Environment

- **Python 3.10+**
- **Claude Code CLI** required (default provider). No API key needed.
- **GitHub token** required for scraping (`GITHUB_TOKEN` in `.env`). Classic PAT with `public_repo` scope.
- Alternatively: `--provider anthropic` (needs `ANTHROPIC_API_KEY`) or `--provider openrouter` (needs `OPENROUTER_API_KEY`)

## Pre-filter Pipeline

Before any LLM calls, candidates are filtered heuristically during scraping:

1. Must include test file changes
2. Must touch source code (not test-only)
3. 5-500 lines changed
4. ≤20 files changed
5. Has a meaningful PR description (≥20 chars)
6. Merged after `--min-date` (default: 2022-01-01)
7. Not a bot PR (dependabot, renovate)

## Tests

```bash
python -m pytest tests/ -v
```

## Naming Audit

Use the sibling audit helper before trusting naming degradation on a new repo:

```bash
python ../degradation/naming_audit.py /path/to/disposable-worktree
uv run --with rope python ../degradation/naming_audit.py /path/to/disposable-worktree --live
```

The dry-run report shows projected rename coverage and sample symbols. The live report adds rename success/skip rates plus the most common skipped names so you can judge whether the repo is safe and strong enough for the naming condition.
