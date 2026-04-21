# Tasks

## Completed

- [x] Pull latest teammate changes.
- [x] Map the repo and sibling degradation directory.
- [x] Read the project docs and updated experiment design spec.
- [x] Inspect the `LLM-J` source tree and tests.
- [x] Inspect the sibling degradation scripts.
- [x] Run the `LLM-J` test suite in the user’s Python environment.
- [x] Record review context for follow-on sessions.
- [x] Update `LLM-J` prompts/docs for comments-docstrings degradation and test degradation policy.
- [x] Add Stage 2 navigation-depth gating for verified manifests.
- [x] Split executable test files from preserved test-support infrastructure in the Stage 3/Stage 4 contract.
- [x] Patch first-pass degradation script behavior to stop exempting tests and to preserve test infrastructure in remove-tests.
- [x] Add a dedicated degradation contract doc and link it from the main README.
- [x] Make the naming degrader inspectable without `rope` and deterministic across runs.
- [x] Emit explicit validated `degradation_targets` in Stage 1 and Stage 2 manifests.
- [x] Harden the naming degrader to preserve test discovery hooks while covering more safe local bindings.
- [x] Add regression tests in `LLM-J` for the sibling naming degrader contract.
- [x] Run live `rope` audits on disposable real-repo worktrees and tighten offset matching / skip reporting.
- [x] Add a reusable `naming_audit.py` helper for per-repo naming-readiness reports.
- [x] Add an `audit-naming` CLI workflow in `LLM-J` that prepares disposable worktrees and wraps sibling audit reports.
- [x] Add a repo-level static readiness screen for all degradation surfaces via `audit-repo`.
- [x] Add a combined repo experiment packet workflow for one-stop human review before Stage 4/Stage 5.
- [x] Add an explicit admission rubric and markdown review packet output for consistent human repo approval.

## Recommended Next Work

- [ ] Finish replacing remaining stale documentation references to directory-structure degradation where they still matter.
- [ ] Wire the eventual Stage 4 harness to consume `degradation_targets` directly.
- [ ] Tighten degradation implementations that currently fall short of the full-intensity spec, especially naming obfuscation.
- [ ] Add repo-level integration tests that cover the full Stage 2 manifest contract and the degradation handoff.

## Confirmed Decisions

- [x] Degrade existing test files for non-remove-tests conditions (`type_hint`, `naming`, `comments/docstrings`).
- [x] Preserve test infrastructure in the remove-tests condition so the agent can still write and run new tests.
