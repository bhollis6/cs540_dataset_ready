# Repo Profile Schema V1

## Purpose

Repo profiles define historical execution knowledge outside generic workflow code.

This is the main mechanism for preventing `LLM-J` from turning into a pile of
repo-specific conditionals inside Stage 2/4/5.

## Design Goals

- mostly declarative
- human-auditable
- narrow enough to avoid turning into arbitrary scripts
- expressive enough to capture real repo differences

## Proposed Shape

```yaml
repo: encode/httpx
profile_version: 1

runtime:
  os: ubuntu-22.04
  arch: x86_64
  python: "3.11"
  package_manager: uv

environment:
  env_commit_strategy: base_or_override
  system_packages: []
  env_vars: {}
  pre_install: []
  install_commands:
    - uv pip install -e .
  install_fallbacks:
    - pip install -e .
  post_install: []
  dependency_pins: {}

test:
  command: pytest -q
  selection_mode: explicit_nodeids
  plugin_policy:
    mode: default
    explicit_plugins: []
  env_vars: {}

historical_quirks:
  known_break_windows: []
  notes: []

degradation:
  supported_conditions:
    - type_hints
    - naming
    - comments_docstrings
    - remove_tests
  test_support_globs: []

admission:
  pilot_probe_target: 3
  pilot_min_verified_tasks: 2
```

## Field Notes

### `runtime`

Captures environment-wide execution assumptions.

### `environment`

Captures installation and dependency setup details.

Current real usage includes:
- install-time env vars for historical build/version quirks
- post-install test or optional-backend dependency surfaces
- repo-specific editable-install fallback behavior

### `test`

Captures test execution policy, including plugin behavior and required env vars.

Current real usage includes:
- explicit plugin loading when pytest autoload is disabled
- container/host parity for probe and real pytest execution paths

### `historical_quirks`

Captures unusual historical compatibility notes without leaking them into generic code.

### `degradation`

Captures repo-specific degradation safety and file-preservation details.

### `admission`

Stores pilot-phase thresholds without hard-coding them in the workflow engine.

## Current Status

This schema is no longer just a design target.

It is now wired into:
- host-backed Stage 2 probing
- Docker bundle generation for Stage 2 probing
- container-first Stage 2 runtime comparison / repo-admission reporting
- real repo profiles for:
  - `httpx`
  - `cattrs`
  - `starlette`

The main remaining work is not schema invention. It is using the schema to drive
Stage 4/5 substrate choices more directly.
