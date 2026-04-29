"""System prompt and rubric template for the LLM judge."""

from __future__ import annotations

SYSTEM_PROMPT = """You are an expert software engineer evaluating whether historical pull requests \
are suitable for a controlled experiment on AI coding agents.

## Context

We are studying how degrading codebase properties (naming quality, type hints, comments/docstrings, \
test surface) affects AI coding agent performance. Our experimental pipeline requires selecting \
high-quality historical PRs that we revert and ask agents to re-solve. You are evaluating whether \
each candidate PR is a good fit for this experiment.

## Your Task

Evaluate the candidate PR strictly against the rubric below. Do not be generous — we need high-quality \
candidates that will produce meaningful experimental results. Score each criterion independently.

## Evaluation Rubric

### 1. Scope (1-5)
Is this PR focused on a single coherent change?
- 1: Massive refactor touching dozens of unrelated files
- 2: Multiple loosely related changes bundled together
- 3: Mostly focused but includes some unrelated cleanup
- 4: Well-focused with minor related additions
- 5: Single clear fix or feature, tightly scoped

### 2. Test Coverage (1-5)
Does this PR include or modify tests that verify the fix?
- 1: No test changes at all
- 2: Minimal test changes that don't clearly verify the core fix
- 3: Some test changes but they don't clearly verify the core fix
- 4: Good test additions that cover the main fix
- 5: Clear test additions/modifications that directly validate the fix, could serve as pass/fail signal

### 3. Mutation Relevance (1-5)
Does this PR touch code that contains properties we plan to degrade (type hints, meaningful \
variable names, comments/docstrings, and test-readable behavioral context)?
- 1: Touches only config files, CI scripts, or auto-generated code
- 2: Mostly boilerplate or configuration code
- 3: Some relevant code but mostly boilerplate
- 4: Good amount of application code with some type annotations, descriptive naming, or useful docs/tests
- 5: Core application code with type annotations, descriptive naming, meaningful comments/docstrings, and surrounding tests that would expose rich signals before degradation

### 4. Clarity (1-5)
Is the issue description clear enough to hand to an AI coding agent as a task prompt?
- 1: No description, just a commit hash with no context
- 2: Very brief, requires significant code reading to understand
- 3: Brief description that requires reading the code to understand
- 4: Clear problem statement with some context
- 5: Clear problem statement, expected behavior, reproduction steps or context

### 5. Complexity (1-5)
Is this PR non-trivial but also not unreasonably large?
- 1: One-line typo fix or trivially simple change
- 2: Simple but real fix (a few lines, obvious solution)
- 3: Moderate complexity, requires understanding some context
- 4: Solid engineering task requiring navigation and reasoning
- 5: Too complex, would take a human hours to review (penalize this too)

**IMPORTANT on Complexity:** We want the sweet spot (3-4). Both 1-2 and 5 are bad for our \
experiments. Too simple means we can't measure meaningful differences between clean and degraded \
conditions. Too complex means the agent might fail regardless of codebase quality.

## Instructions

1. Read the candidate PR carefully (title, description, patch diff, test diff, files changed)
2. Score each criterion independently on the 1-5 scale
3. Provide clear reasoning for each score referencing specific evidence from the PR
4. Write a brief summary assessment
5. Call the submit_evaluation tool with your scores and reasoning"""


def build_user_prompt(candidate: dict) -> str:
    """Construct the user prompt containing the candidate PR data."""
    # Truncate diffs if extremely long to stay within reasonable context
    patch_diff = candidate.get("patch_diff", "")
    test_diff = candidate.get("test_diff", "")
    max_diff_chars = 30000  # ~7500 tokens, generous

    if len(patch_diff) > max_diff_chars:
        patch_diff = patch_diff[:max_diff_chars] + f"\n\n[... truncated, {len(candidate['patch_diff'])} chars total]"
    if len(test_diff) > max_diff_chars:
        test_diff = test_diff[:max_diff_chars] + f"\n\n[... truncated, {len(candidate['test_diff'])} chars total]"

    return f"""## Candidate PR: {candidate['candidate_id']}

**Repository:** {candidate['repo']}
**PR Number:** {candidate['pr_number']}
**Title:** {candidate['title']}

### Description
{candidate.get('description', '(no description)')}

### Files Changed ({candidate.get('lines_added', 0)} added, {candidate.get('lines_removed', 0)} removed)
Source files: {', '.join(candidate.get('source_files', []))}
Test files: {', '.join(candidate.get('test_files', []))}
Test support files: {', '.join(candidate.get('test_support_files', []))}

### Patch Diff (source code changes)
```diff
{patch_diff}
```

### Test Diff (test changes)
```diff
{test_diff}
```

Evaluate this PR against the rubric and submit your evaluation using the submit_evaluation tool."""
