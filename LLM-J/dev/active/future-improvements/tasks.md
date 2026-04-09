# Future Improvements

Tracked items from Codex staff review and ongoing development. Address before scaling beyond the 3-repo test set.

## Priority 1: Before Scaling to 10+ Repos

### Preflight Environment Isolation
- Currently installs historical repos into the active Python env via `pip install -e`
- Creates dependency leakage between candidates and mutates the operator's environment
- **Fix:** Isolated venvs per candidate or Docker containers for preflight runs
- **Where:** `src/deep_eval/preflight.py` → `_install_project()`

### Historical-State Sanitization
- Worktrees can still inherit future-history visibility from the bare clone
- Removing `origin` helps but tags, branches, and refs from later commits may still be accessible
- **Fix:** Implement full SWE-bench sanitization — delete future tags, prune all post-base-commit refs, verify with commit count check
- **Where:** `src/deep_eval/repo_manager.py` → `sanitize_worktree()`

## Priority 2: Better Experimental Sensitivity

### Navigation Depth Gating
- Stage 2 currently accepts based on total score alone (≥22/30)
- A candidate with navigation_depth=1 can be accepted if other scores are high
- But low navigation depth means degradation won't meaningfully affect the agent
- **Fix:** Add minimum `navigation_depth ≥ 3` as a hard gate, or flag low-nav candidates for manual review
- **Where:** `src/deep_eval/deep_judge.py` → `write_deep_results()` verified filter

### Per-Degradation Sensitivity Scoring
- `mutation_relevance` compresses 4 future degradations into one score
- Stage 4 will degrade: type hints, naming, directory structure, test coverage
- **Fix:** Score sensitivity per degradation dimension so downstream can pick tasks best suited for each mutation
- **Where:** `src/deep_eval/prompts.py` rubric, `src/deep_eval/models.py` response schema

### Deeper Context Retrieval
- First-degree imports miss dispatch chains, inheritance hierarchies, runtime composition
- Navigation depth scoring can be systematically understated
- **Fix:** Expand to symbol-level retrieval — follow class hierarchies, registered handlers, call targets
- **Where:** `src/deep_eval/context_extractor.py` → `collect_context_files()`

## Priority 3: Research Process Hygiene

### Artifact Provenance
- Output directories should capture: pipeline git commit, prompt hash, provider/model, Python version, timestamp, config snapshot
- Without this, reruns and comparisons are hard to defend
- **Where:** All output writers in `src/output/` and `src/deep_eval/deep_judge.py`

### Exclusion Taxonomy
- Rejected candidates should record structured reasons (patch failed, no FAIL_TO_PASS, low navigation, etc.)
- Useful for debugging and method writeup
- **Where:** `src/deep_eval/deep_judge.py` results output

### Anthropic Test Coverage
- `tests/test_anthropic_provider.py` skips if `anthropic` not installed
- Fine for local dev, but if Anthropic becomes a real CI path, install it in test env
- **Where:** `tests/test_anthropic_provider.py`

## Notes

- These items are not blocking for the 3-repo test set (starlette, httpx, cattrs)
- Address before scaling to 10-15 repos for the full experiment
- The preflight isolation is the single biggest research-rigor weakness
- Per-file Ruff E501 ignore for prompt files is intentional (pyproject.toml)
