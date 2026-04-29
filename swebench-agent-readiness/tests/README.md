# Tests

This folder contains unit tests for the reusable experiment code in `../src/`.

The tests cover degradation transforms, task filtering, Codex metric parsing, run materialization helpers, oracle packet parsing, and related harness behavior. They are safe to run as normal unit tests; they do not launch new SWE-bench/Codex experiment runs.

Run from the repository root:

```bash
PYTHONPATH=. uv run --extra dev pytest
```
