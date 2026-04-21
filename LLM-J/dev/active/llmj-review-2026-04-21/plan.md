# LLM-J / Degradation Review Plan

Date: 2026-04-21

## Goal

Review the current `LLM-J` implementation and the sibling `degradation/` scripts against the updated experiment design spec in `experiment_design_spec_v2(1).docx`, then identify the concrete integration and correction work needed before wiring Stage 3 outputs into Stage 4 degradations.

## Review Scope

1. Read project docs and reconstruct the intended pipeline.
2. Inspect the Python implementation for scraping, Stage 1 judging, Stage 2 deep evaluation, output contracts, and test coverage.
3. Inspect teammate degradation scripts for type hints, naming, test removal, and comments/docstrings.
4. Compare both sides to the updated experiment spec.
5. Produce a prioritized findings list and recommended next actions.

## Expected Follow-On Work

- Update the `LLM-J` mutation-relevance rubric and related docs to reflect the new degradation set.
- Tighten Stage 2 selection so verified manifests match the navigation-depth policy.
- Define and implement the contract between verified manifests and degradation runners.
- Correct degradation behaviors that currently violate the new experimental rules.
