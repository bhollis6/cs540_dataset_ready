"""Stage 2 system prompt and user prompt builder with full file context."""

from __future__ import annotations

DEEP_SYSTEM_PROMPT = """You are an expert software engineer evaluating whether historical pull requests \
are suitable for a controlled experiment on AI coding agents.

## Context

We are studying how degrading codebase properties (naming quality, type hints, comments/docstrings, \
and test surface) affects AI coding agent performance. We will:
1. Check out the repo at the state BEFORE this PR was merged
2. Apply degradations (strip type hints, obfuscate names, etc.) to the ENTIRE repo
3. Drop an AI agent into the degraded repo with only the issue description
4. The agent must explore, understand, and implement the fix
5. We check if the PR's tests pass after the agent's changes

You are evaluating whether this PR makes a good experimental task. You can see the FULL source files \
as they exist at the base commit (before the fix), plus related files the agent would likely need to \
read. Evaluate strictly — we need tasks where codebase degradation could meaningfully affect agent performance.

## Evaluation Rubric

### 1. Scope (1-5)
Is this PR focused on a single coherent change?
- 1: Massive refactor touching dozens of unrelated files
- 3: Mostly focused but includes some unrelated cleanup
- 5: Single clear fix or feature, tightly scoped

### 2. Test Coverage (1-5)
Does this PR include tests that verify the fix?
- 1: No test changes at all
- 3: Some test changes but they don't clearly verify the core fix
- 5: Clear test additions that directly validate the fix, strong pass/fail signal

### 3. Mutation Relevance (1-5)
Looking at the FULL source files (not just the diff), does the code that must be understood to solve \
this task contain properties we plan to degrade?
- 1: Mostly config, boilerplate, or auto-generated code
- 3: Some relevant code but sparse type hints, weak naming, or limited documentation/test signal
- 5: Rich type annotations, descriptive naming, meaningful comments/docstrings, and strong surrounding tests that would normally help the agent orient before degradation

### 4. Clarity (1-5)
Is the issue description clear enough to hand to an AI coding agent as a task prompt?
- 1: No description, just a commit hash
- 3: Brief description that requires reading code to understand
- 5: Clear problem statement, expected behavior, reproduction steps

### 5. Complexity (1-5)
Is this PR non-trivial but also not unreasonably large?
- 1: One-line typo fix
- 3: Moderate complexity, requires understanding some context
- 4: Solid engineering task requiring navigation and reasoning
- 5: Too complex, would take a human hours (penalize this too)

**IMPORTANT on Complexity:** We want the sweet spot (3-4). Both too simple and too complex are bad.

### 6. Navigation Depth (1-5) ★ NEW
Looking at the full source files and their imports, how much cross-file understanding does the agent \
need to solve this task?
- 1: Fix is self-contained in one function. No cross-file understanding needed.
- 2: Need to read one other file or understand one call chain.
- 3: Need to understand 2-3 files and their relationships (imports, class hierarchies, shared types).
- 4: Need to trace through 4+ files, understand module boundaries, or follow a lifecycle.
- 5: Need to understand deep architectural patterns spanning many modules.

**Why this matters:** If the task can be solved by reading one function, degrading the rest of the \
repo won't affect agent performance. We need tasks where the agent MUST explore and navigate.

## Instructions

1. Read the full source files carefully — these show the codebase as the agent will see it
2. Read the related/dependency files — these are what the agent would likely explore
3. Read the diff to understand what the fix actually changes
4. Score each criterion independently, referencing specific evidence
5. For Navigation Depth, trace what an agent would need to read and understand to implement the fix
6. Call the submit_evaluation tool with your scores and reasoning"""


def build_deep_user_prompt(
    candidate: dict,
    source_contents: dict[str, str],
    dep_contents: dict[str, str],
    preflight_summary: str | None = None,
) -> str:
    """Construct the Stage 2 user prompt with full file context."""

    # Build source files section
    source_section = ""
    for path, content in sorted(source_contents.items()):
        source_section += f"\n#### {path}\n```python\n{content}\n```\n"

    # Build dependency files section
    dep_section = ""
    if dep_contents:
        for path, content in sorted(dep_contents.items()):
            dep_section += f"\n#### {path}\n```python\n{content}\n```\n"
    else:
        dep_section = "\n(no local dependency files found)\n"

    # Build preflight section
    preflight_section = ""
    if preflight_summary:
        preflight_section = f"\n### Pre-flight Validation\n{preflight_summary}\n"

    # Truncate diffs if extremely long (keep full files as priority)
    patch_diff = candidate.get("patch_diff", "")
    test_diff = candidate.get("test_diff", "")
    max_diff = 30000
    if len(patch_diff) > max_diff:
        patch_diff = patch_diff[:max_diff] + f"\n[... truncated, {len(candidate['patch_diff'])} chars total]"
    if len(test_diff) > max_diff:
        test_diff = test_diff[:max_diff] + f"\n[... truncated, {len(candidate['test_diff'])} chars total]"

    return f"""## Candidate PR: {candidate['candidate_id']}

**Repository:** {candidate['repo']}
**PR Number:** {candidate['pr_number']}
**Title:** {candidate.get('title', '(no title)')}

### Description
{candidate.get('description', '(no description)')}

### Full Source Files (at base commit, BEFORE the fix)
These are the complete files that the PR modifies, as they exist in the repo before the fix:
{source_section}

### Related Files (first-degree imports)
These are files imported by the source files above — the agent would likely read these during exploration:
{dep_section}

### Patch Diff (what the fix changes)
```diff
{patch_diff}
```

### Test Diff (test changes added by the PR)
```diff
{test_diff}
```
{preflight_section}

Evaluate this PR against the rubric. Pay special attention to Navigation Depth — trace what an agent \
would need to read and understand across files to implement this fix."""
