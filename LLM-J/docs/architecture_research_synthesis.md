# Architecture Research Synthesis

## Research Conclusions We Are Adopting

From the two deep-research memos and our current empirical work, these points are now
the working architecture direction for `LLM-J`:

1. `git checkout` is not the environment.
2. Stage 2, Stage 4, and Stage 5 are the runtime-risk stages and should move onto a containerized substrate.
3. `LLM-J` needs a repo-profile layer instead of accumulating more repo-specific hacks in generic workflow code.
4. Repo admission and task admission must stay separate.
5. `httpx` is not a bad repo; it is a good repo with a strict oracle.
6. The broader regression oracle should stay because the naming failures are a real signal, not evaluation noise.

## What We Are Adopting

### `env_commit`

Add an `env_commit` concept as a first-class field.

Purpose:
- separate the code snapshot from the environment-definition snapshot
- allow future SWE-bench-style behavior where environment files may come from a different historical point than the base code itself

Initial rule:
- default `env_commit = base_commit`
- only specialize later where needed

### Repo Profiles

Move repo-specific execution knowledge into declarative profile files rather than
embedding more of it in generic Stage 2/4/5 workflow logic.

Examples of profile-owned concerns:
- Python version
- package manager choice
- install commands
- explicit dependency pins
- test command
- plugin policy
- env vars
- post-install test/backends dependency surface
- system packages
- known historical quirks

### Containerization Order

Do not containerize everything at once.

Adopt the staged migration:
1. containerize Stage 2 first
2. re-run `httpx`, `cattrs`, and `starlette` through the new Stage 2 probe
3. move Stage 4 and Stage 5 onto the same substrate after Stage 2 is stable

Current status:
- Step 1 is now materially complete for the initial repo set
- all three pilot repos have successful Docker-backed Stage 2 probe results
- matched host-vs-container reruns now exist for the same pilot commits
- the packet/reporting path now has a container-first `stage2_runtime_probe` gate
- the important remaining work is to move Stage 4 validation and Stage 5 oracle replay onto the same substrate while keeping task admission separate

### Broader Oracle Reporting

Keep the broad oracle and explicitly report:
- target fix success
- regression surface damage

This matches what we observed in `httpx` under `naming`, where the agent could satisfy
the target FAIL_TO_PASS tests while still causing broader PASS_TO_PASS regressions.

## What We Are Not Adopting Yet

### Rigid Long-Term Thresholds

Not yet adopting as hard pilot rules:
- mandatory `3/3` historical probes
- mandatory `>=15` verified tasks per repo

Reason:
- useful eventual targets
- too rigid for the current phase

### HTTP Runtime Layer

Not building a dedicated runtime server yet.

Reason:
- interesting later
- not the current bottleneck

### Blind Faith In `uv --exclude-newer`

Will use it as a strong default direction, but not assume it solves every repo.

Some repos will still need:
- explicit pins
- special install steps
- repo-specific profile overrides

## Immediate Architecture Program

Completed:
1. add `env_commit`
2. define repo profile schema v1
3. design and implement containerized Stage 2 probe preparation
4. re-probe `httpx`, `cattrs`, `starlette` through Docker-backed Stage 2 bundles
5. compare matched host-vs-container Stage 2 outcomes across the pilot repo set
6. make the container-backed Stage 2 probe the primary repo-admission authority in packet/reporting logic

Next:
1. move Stage 4 environment-bearing workspace construction and validation onto the container substrate
2. keep Stage 5 harness invocation host-side initially, but move oracle replay/evaluation container-first
3. generate real repo packets for the pilot repos once readiness/naming artifacts are present on the current lane
