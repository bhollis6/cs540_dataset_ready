# Container Migration Plan

## Goal

Move the current `LLM-J` custom-repo path toward a more reproducible architecture
without destabilizing the working pipeline all at once.

## Principles

1. Keep Stage 1 and Stage 7 on host.
2. Move runtime-risk stages first.
3. Keep the broad oracle.
4. Use repo profiles instead of scattering repo-specific fixes in generic code.

## Stage Order

### Phase 1: Stage 2 First

Containerize:
- historical preflight
- gold-patch validation
- base/test/gold transition checks

Reason:
- this is where `starlette`-style environment brittleness currently shows up
- it gives the highest reproducibility value first

Success condition:
- `httpx`, `cattrs`, and `starlette` can be re-probed through the new Stage 2 substrate
- failures become more clearly attributable to repo/task issues rather than host drift

Current implementation checkpoint:
- a host-backed, profile-aware Stage 2 probe now exists
- a container-bundle generator now exists to prepare:
  - repo snapshot tarball
  - Dockerfile
  - install script
  - probe script
  - metadata
- structured host-side `probe_results/` artifacts now exist:
  - `probe_result.json`
  - install/probe/container stdout/stderr logs
  - `docker_exit_code.txt`
- real Docker-backed Stage 2 probe success has now been demonstrated for:
  - `httpx`
  - `cattrs`
  - `starlette`
- a matched host-vs-container comparison artifact now exists for the pilot set
- repo-packet reporting now treats the container probe as the hard Stage 2 runtime gate
- host probing is now explicitly demoted to a fast heuristic

Interpretation:
- Stage 2 containerization is no longer just a design target
- repo profiles are now validated by real execution differences:
  - `httpx` works with a relatively light profile
  - `cattrs` needs a heavy optional-backend/test surface
  - `starlette` needs explicit plugin/test-surface support
- the next migration step should treat the container-backed Stage 2 probe as the primary repo-admission authority

### Phase 2: Stage 4 On The Same Substrate

Keep host-based:
- run planning / artifact assembly
- git-history inspection
- deterministic degradation transforms

Containerize:
- environment-bearing clean task snapshot materialization
- dependency installation for clean/degraded workspaces
- clean/degraded validation on the same substrate used by Stage 2

Reason:
- the risky part of Stage 4 is the historical runtime substrate, not the text transform itself
- clean and degraded workspaces should be validated where Stage 2 already proved repo viability

Success condition:
- clean and degraded workspaces are reproducible, separable, and valid on the container substrate

### Phase 3: Stage 5 On The Same Substrate

Keep host-based first:
- subscription CLI harness invocation
- prompt/log capture
- local auth/session management

Containerize first:
- oracle replay
- post-agent evaluation
- hidden-test execution

Later option:
- full in-container agent execution once the harness auth boundary can be projected cleanly

Reason:
- the practical auth boundary for frontier CLIs currently lives on the host
- the repo/runtime substrate for validation and oracle replay should still converge with Stage 2/4

Success condition:
- oracle scoring no longer depends on host Python state
- Stage 5 can use host-driven harnesses without losing runtime reproducibility on repo execution

## Non-Goals For The First Migration Pass

- building a custom runtime HTTP server
- full cluster orchestration
- rigid final admission thresholds
- solving every repo with one generic install recipe

## Expected Benefits

- clearer repo-vs-environment failure diagnosis
- less host contamination
- better reproducibility
- cleaner path to scaling beyond the current repo set
