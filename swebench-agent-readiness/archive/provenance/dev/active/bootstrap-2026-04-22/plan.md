# Plan

## Goal

Stand up the SWE-bench pivot workspace so implementation can begin in parallel with
the current `LLM-J` path.

## First-Pass Decisions

- consume SWE-bench as a pinned dependency, not a submodule or sibling clone
- choose `comments_docstrings` as the first executable non-test-removal degradation
- choose `remove_tests` as the second pilot degradation on the same task
- choose `pytest-dev__pytest-7432` as the first pilot task, with backups recorded separately
- choose `scikit-learn__scikit-learn-26194` as the second task once the first-task matrix is stable enough to widen

## First Build Target

1. validate the machine-readable eligibility record
2. install the upstream SWE-bench dependency and fetch the official row
3. materialize clean and degraded workspaces
4. run Codex on both
5. replay the official oracle host-locally
6. emit one oracle-backed comparison packet
7. run one more replication to check stability before widening the experiment surface
8. widen next with `remove_tests` on the same task before considering a second SWE-bench instance
9. widen to `scikit-learn__scikit-learn-26194` before adding more degradation types

## What We Implemented First

- eligibility schema and Python contract
- stdlib comments/docstrings degrader
- pilot run-spec contract
- official task snapshot adapter
- host-local materializer
- non-interactive Codex exec wrapper
- host-local oracle replay wrapper
- pilot comparison artifact contract
- oracle-backed packet wrapper
- lightweight Codex JSONL bootstrap-metrics parser

## What We Explicitly Deferred

- full Stage 5/6/7 workflow ports
- naming/type-hint heavy transformers
- broad task-slice automation before the first pilot runs end to end
- full containerized SWE-bench evaluation path in this environment, because Docker is unavailable here
- full stage-style bootstrap metric extraction before the first oracle-backed pilot result exists
