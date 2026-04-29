# Degradation Contract

This document defines the current handoff contract between Stage 3 (`LLM-J`) and Stage 4 (codebase degradation).

## Purpose

The degradation stage must apply controlled information loss without breaking repository functionality. The contract here is designed to keep the causal story clean:

- the agent should lose one information channel at a time
- the repository should remain runnable
- downstream tooling should know exactly which files to degrade versus preserve

## File Categories

Candidate JSON files and manifests may include these path groups:

- `source_files`
  - non-test source files changed by the historical PR
- `test_files`
  - executable/removable test files
  - examples: `tests/test_foo.py`, `foo_test.py`, `tests.py`
- `test_support_files`
  - preserved test infrastructure and support assets
  - examples: `conftest.py`, fixtures, helper modules under test directories, snapshot/test-data assets

Selected and verified manifests now also include:

- `degradation_targets`
  - explicit Stage 4 target lists derived from the file groups
  - this is the preferred downstream interface for deciding what to edit or preserve

This distinction matters because the remove-tests condition should delete existing executable tests while leaving enough infrastructure in place for the agent to write and run new tests.

## Per-Degradation Rules

### 1. Strip Type Hints

Target:

- degrade source files
- degrade existing executable tests
- degrade existing test-support Python files when they contain annotations

Do not:

- break imports or runtime behavior
- change non-Python assets just because they sit under a test-support directory

### 2. Naming Obfuscation

Target:

- degrade source files
- degrade existing executable tests
- degrade Python-based test-support infrastructure

Do not:

- rename in a way that breaks global cross-file references
- introduce nondeterministic naming

### 3. Remove Comments and Docstrings

Target:

- degrade source files
- degrade existing executable tests
- degrade Python-based test-support infrastructure

Do not:

- remove string literals that are not docstrings
- change runtime behavior

### 4. Remove Tests

Target:

- delete existing `test_files`

Preserve:

- `test_support_files`
- pytest configuration and support infrastructure needed for the agent to write and run its own tests

Rationale:

- the agent should lose existing behavioral examples and ready-made validation
- the agent should still be able to create new tests and execute them

## Manifest Shape

Per accepted PR, downstream tooling should prefer the explicit `degradation_targets` block:

```json
{
  "degradation_targets": {
    "type_hints": {
      "target_files": ["src/app.py", "tests/test_app.py", "tests/conftest.py"]
    },
    "naming": {
      "target_files": ["src/app.py", "tests/test_app.py", "tests/conftest.py"]
    },
    "comments_docstrings": {
      "target_files": ["src/app.py", "tests/test_app.py", "tests/conftest.py"]
    },
    "remove_tests": {
      "delete_files": ["tests/test_app.py"],
      "preserve_files": ["tests/conftest.py", "tests/fixtures/example.json"]
    }
  }
}
```

Notes:

- non-remove-tests degradations include Python-based test-support files
- non-Python support assets remain listed under `test_support_files` and `remove_tests.preserve_files`, but are not included in the other degradation target lists
- Stage 3 validates that `source_files`, `test_files`, and `test_support_files` do not overlap

## Selection Policy Implications

Stage 3 should prefer tasks where degradation has real surface area. That means:

- touched code should expose useful type, naming, and documentation signals before degradation
- existing tests should carry meaningful behavioral information
- navigation depth should be high enough that repo-wide degradation can matter

Current Stage 2 verified-manifest policy:

- preflight must pass
- Stage 2 LLM recommendation must be `ACCEPT`
- navigation depth must meet the configured minimum threshold

## Repo Audit Workflow

Before running experiments on a new repo, naming degradation should be audited on a disposable worktree.

Suggested workflow:

1. Run the broad static screen:
   - `python -m src.cli audit-repo --repo owner/name --output-dir ./audit_results`
2. Inspect:
   - type-hint surface
   - comments/docstrings surface
   - remove-tests viability
   - dry-run naming coverage
3. Run a naming-specific dry/live audit when the repo looks promising:
   - `python -m src.cli audit-naming --repo owner/name --output-dir ./audit_results`
   - `python -m src.cli audit-naming --repo owner/name --output-dir ./audit_results --live`
4. Inspect:
   - rename counts by class/function/variable
   - sample symbols
   - rename success rate
   - offset-not-found rate
   - refactoring-error rate
   - top skipped names

The goal is not zero skips. The goal is to verify that:

- the degradation is strong enough to matter
- framework/test discovery names are still preserved
- the remaining skip profile is understandable rather than arbitrary

## Review Packet

After generating repo readiness and task manifests, assemble a single review packet:

- `python -m src.cli build-packet --repo owner/name --results-dir ./results --deep-results-dir ./deep_results --readiness-dir ./audit_results --output-dir ./packets`

The packet combines:

- Stage 1 selected tasks
- Stage 2 verified tasks
- repo-level static readiness
- naming readiness

This packet is the intended human-review artifact before approving downstream degradation and agent-run stages.

Once the packet is approved, Stage 5 planning now flows through:

- `python -m src.cli build-run-plan --repo owner/name --deep-results-dir ./deep_results --packet-dir ./packets --candidates-dir ./candidates --output-dir ./run_plans`
- `python -m src.cli materialize-runs --repo owner/name --run-plan-dir ./run_plans --clones-dir ./clones --output-dir .`
- `python -m src.cli execute-runs --repo owner/name --run-plan-dir ./run_plans --clones-dir ./clones --output-dir .`

See [docs/agent_run_contract.md](agent_run_contract.md) for the current Stage 5 plan schema.

Current admission rubric dimensions:

- repo static surface viability
- Stage 1 task-pool depth
- Stage 2 verified-task depth
- naming live-audit readiness

The packet currently emits workflow labels:

- `GO`
- `REVIEW`
- `NO_GO`

These are meant to standardize human review, not replace it.

## Open Follow-On Work

- Continue hardening naming obfuscation so the intervention matches the intended experimental strength across real repos.
- Consider adding cached task/condition workspaces once live Stage 5 execution exists and materialization cost is better understood.
- Improve harness log richness and normalization so Stage 6 parsing can compare Claude and Codex using one schema.
