# Repository Selection

10 Python repositories selected for the agent-readiness degradation experiment. Each repo meets our selection criteria: Python primary language, active maintenance, strong test suite, small-to-medium size (under 50k LOC), well-structured code with type hints, and a history of PRs that include test changes.

## Selection Criteria

- Python as primary language
- Active commits within last 6 months
- Existing test suite (pytest or unittest) with good coverage
- Small to medium size (under ~50k LOC, ideally 5k-25k)
- Well-structured: type hints, good naming, clear directory structure
- Merged PRs regularly include test changes (needed for FAIL-to-PASS validation)
- Variety of domains so findings generalize
- Exclude: ML training repos, massive monorepos

## Selected Repos

| # | Repo | Domain | ~LOC | Stars |
|---|---|---|---|---|
| 1 | encode/starlette | Web framework | 14k | 12k |
| 2 | encode/httpx | HTTP client | 14k | 15k |
| 3 | python-attrs/cattrs | Data serialization | 8-12k | 1k |
| 4 | encode/uvicorn | ASGI server | 10k | 10k |
| 5 | marshmallow-code/marshmallow | Object serialization | 10k | 7k |
| 6 | pallets/click | CLI framework | 17k | 17k |
| 7 | jazzband/pip-tools | Dependency management CLI | 11k | 8k |
| 8 | hynek/structlog | Structured logging | 6k | 5k |
| 9 | pydantic/pydantic-settings | Config management | 6k | 1k |
| 10 | copier-org/copier | Project templating CLI | 16k | 3k |

## Per-Repo Rationale

### 1. encode/starlette
- **Domain:** Lightweight ASGI web framework (routing, middleware, WebSockets, sessions)
- **Why:** 100% test coverage, 100% type-annotated. PRs consistently include test changes. Very active with multiple releases in 2026. Clean class hierarchies in routing, middleware, and request handling make it ideal for testing naming and type hint degradation.
- **Concerns:** None significant. Strongest overall candidate.

### 2. encode/httpx
- **Domain:** Next-generation HTTP client (sync + async, HTTP/2, connection pooling)
- **Why:** 100% test coverage. Excellent architecture with clear base class patterns (`BaseClient` → `Client`/`AsyncClient`). Rich type annotations throughout. Different domain from starlette despite same org.
- **Concerns:** Activity slowed slightly in late 2025, but PRs continue into 2026.

### 3. python-attrs/cattrs
- **Domain:** Structured data conversion (composable converters for attrs, dataclasses, TypedDict)
- **Why:** Very active with 52+ test files. Type-annotation heavy by design (the library is built around types). Dispatch mechanism and converter chains create good cross-file navigation depth. Different domain from web projects.
- **Concerns:** Fewer total merged PRs than larger repos, but sufficient for our needs (42 candidates passed pre-filtering).

### 4. encode/uvicorn
- **Domain:** ASGI web server (HTTP/1.1, WebSockets, process management)
- **Why:** 100% coverage enforcement (`fail_under = 100` in config). Modern type hints with union syntax and Literal types. Every substantive PR includes test changes. Compact at ~10k LOC.
- **Concerns:** Docstrings are minimal (relies on type hints and naming instead). Some PRs are benchmark-only.

### 5. marshmallow-code/marshmallow
- **Domain:** Schema-based object serialization and validation
- **Why:** Mature project (3,700+ commits). Extensive type hints with `@typing.overload`, generics, TypedDict. 100% Python. Rich test culture with parametrized tests. High PR volume with tests consistently included.
- **Concerns:** Project is mature and mostly in maintenance mode, so feature PRs are less frequent than bugfix PRs.

### 6. pallets/click
- **Domain:** CLI framework for building command-line interfaces with composable commands
- **Why:** Excellent type hint usage including modern union syntax, `@t.overload`, generics, TypeVar. Clean module structure with 18 focused modules. PRs consistently paired with test changes. Foundational library used by thousands of projects.
- **Concerns:** Some PRs are docs-only or CI-only. Feature/bugfix PRs reliably include tests though.

### 7. jazzband/pip-tools
- **Domain:** CLI tools for managing pinned Python dependencies (`pip-compile`, `pip-sync`)
- **Why:** Best PR+test discipline of the CLI group. `py.typed` marker, strong type hints throughout. Clean structure with subdirectories for scripts, repositories, and internals. Ideal size at 11k LOC.
- **Concerns:** Some PRs are dependency bumps. Substantive PRs consistently include tests.

### 8. hynek/structlog
- **Domain:** Structured logging library with processor-based pipeline
- **Why:** Zero runtime dependencies. `py.typed` marker, mypy in strict mode. Clean modular architecture with clear separation of concerns. 18+ test files. Well-structured, small modules (~130 lines of logic each).
- **Concerns:** Lower volume of substantive PRs (many recent merges are automated updates). Single primary maintainer, so fewer community PRs.

### 9. pydantic/pydantic-settings
- **Domain:** Typed settings loading from env vars, .env files, TOML, YAML, CLI args, cloud secrets
- **Why:** Strictest type checking config of any candidate (`disallow_untyped_defs = true`). Modern union syntax, generics, ClassVar, Literal throughout. Good test coverage with branch analysis.
- **Concerns:** Smaller commit history (349 commits) means fewer PRs to sample. Some tests require cloud SDK mocking (moto for AWS). Depends on pydantic core, so understanding the codebase requires some pydantic knowledge.

### 10. copier-org/copier
- **Domain:** CLI and library for rendering project templates from local paths or Git repos
- **Why:** Exceptional code quality with custom type aliases, Google-style docstrings with Args sections, modern type hints. Strong PR+test pairing (PRs consistently add 40-55 lines of tests). Well-organized with public API modules paired with private implementation modules.
- **Concerns:** Many automated dependency-bump PRs from Renovate bot that need filtering. Human-authored PRs are well-structured though.

## Domain Coverage

| Domain Category | Repos |
|---|---|
| Web/Server | starlette, uvicorn |
| HTTP/Networking | httpx |
| Data/Serialization | cattrs, marshmallow |
| CLI Tools | click, pip-tools, copier |
| Configuration | pydantic-settings |
| Logging/Observability | structlog |

## Repos Considered But Not Selected

| Repo | Reason |
|---|---|
| tiangolo/typer | Large PRs, single-author push style, harder to isolate individual tasks |
| tox-dev/tox | 29k LOC, on the larger side, deep module nesting complicates patching |
| pypa/pipx | Less consistent test pairing than other CLI candidates |
| falconry/falcon | 44k LOC, too large for our target size range |
| apiflask/apiflask | Smaller community (1k stars), inherits Flask architecture |
| Fatal1ty/mashumaro | Lower visibility (900 stars), heavy metaprogramming |
| python-jsonschema/jsonschema | Tests inside package (unconventional structure complicates extraction) |
