# Agent Readiness Report: httpx

**Level:** 1/5  
**Overall Score:** 6%  
**Generated:** 2026-04-22 16:53:24 UTC  

## Summary

| Metric | Value |
|--------|-------|
| Total Criteria | 82 |
| Passed | 3 |
| Failed | 50 |
| Skipped | 29 |

## Pass Rate by Category

| Category | Pass Rate |
|----------|-----------|
| Style & Validation | 0% |
| Build System | 0% |
| Testing | 14% |
| Documentation | 14% |
| Development Environment | 0% |
| Debugging & Observability | 0% |
| Security | 17% |
| Task Discovery | 0% |
| Product & Experimentation | 0% |

## Style & Validation

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Linter Configuration | 0/1 | 🔴 Failed | No linter configuration was verifiable from the visible repository snapshot alone. |
| Type Checker | 0/1 | 🔴 Failed | No mypy/pyright or equivalent type-check configuration was verifiable from the visible snapshot. |
| Code Formatter | 0/1 | 🔴 Failed | No Black/Ruff formatter configuration was verifiable from the visible repository snapshot. |
| Pre-commit Hooks | 0/1 | 🔴 Failed | No pre-commit or equivalent hook configuration was verifiable from the visible snapshot. |
| Naming Consistency | 0/1 | 🔴 Failed | No enforceable naming-convention rules or documented conventions were verifiable from the visible snapshot. |
| Cyclomatic Complexity | 0/1 | 🔴 Failed | No complexity-analysis tooling or thresholds were verifiable from the visible snapshot. |
| Large File Detection | 0/1 | 🔴 Failed | No large-file detection mechanism was verifiable from the visible repository snapshot. |
| Dead Code Detection | 0/1 | 🔴 Failed | No dead-code or unused-symbol detection tooling was verifiable from the visible snapshot. |
| Duplicate Code Detection | 0/1 | 🔴 Failed | No duplicate-code detection tooling was verifiable from the visible snapshot. |
| Technical Debt Tracking | 0/1 | 🔴 Failed | No TODO/FIXME tracking, Sonar, or equivalent technical-debt tracking was verifiable from the visible snapshot. |
| Strict Typing | N/A | Skipped | Skipped: strict typing could not be confirmed from the visible snapshot. |
| Code Modularization Enforcement | N/A | Skipped | Skipped: for this single Python library, explicit module-boundary tooling was not clearly applicable from the snapshot. |
| N+1 Query Detection | N/A | Skipped | Skipped: this repository appears to be a client library, not a database-backed application. |

## Build System

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Build Command Documentation | 0/1 | 🔴 Failed | README.md exists, but a contributor build/setup command could not be confirmed from the visible snapshot. |
| Dependencies Pinned | 0/1 | 🔴 Failed | requirements.txt is present, but exact dependency pinning could not be verified from the visible snapshot. |
| VCS CLI Tools | 0/1 | 🔴 Failed | GitHub/GitLab CLI was unavailable (`gh` not installed), so authenticated VCS automation support is absent locally. |
| Agentic Development | 0/1 | 🔴 Failed | No visible agent configuration, agent workflows, or AI co-authorship evidence was available in the provided snapshot. |
| Single Command Setup | 0/1 | 🔴 Failed | A single fresh-clone setup command was not verifiable from the visible snapshot. |
| Feature Flag Infrastructure | 0/1 | 🔴 Failed | No feature-flag platform or custom flag infrastructure was verifiable from the visible snapshot. |
| Release Notes Automation | 0/1 | 🔴 Failed | CHANGELOG.md exists, but automated release-note generation was not verifiable from the visible snapshot. |
| Unused Dependencies Detection | 0/1 | 🔴 Failed | No unused-dependency detection tooling was verifiable from the visible snapshot. |
| Release Automation | 0/1 | 🔴 Failed | Automated release/publish pipelines were not verifiable from the visible snapshot. |
| Automated PR Review Generation | N/A | Skipped | Skipped: `gh`/`glab` CLI was unavailable and no file-based PR review comment automation was visible. |
| Fast CI Feedback | N/A | Skipped | Skipped: CI timing could not be measured because `gh`/`glab` CLI was unavailable. |
| Build Performance Tracking | N/A | Skipped | Skipped: no build-metrics evidence was visible, and workflow timing inspection required unavailable VCS CLI access. |
| Deployment Frequency | N/A | Skipped | Skipped: deployment frequency could not be verified without authenticated VCS CLI access. |
| Progressive Rollout | N/A | Skipped | Skipped: this appears to be a library repository, not a deployment/infra repository. |
| Rollback Automation | N/A | Skipped | Skipped: this appears to be a library repository, not a deployment/infra repository. |
| Monorepo Tooling | N/A | Skipped | Skipped: the repository appears to be a single-application repository, not a monorepo. |
| Heavy Dependency Detection | N/A | Skipped | Skipped: this Python library is not a bundled frontend application. |
| Version Drift Detection | N/A | Skipped | Skipped: the repository appears to be a single-application repository, not a monorepo. |
| Dead Feature Flag Detection | N/A | Skipped | Skipped: feature-flag infrastructure was not evident, so stale-flag detection was not applicable. |

## Testing

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Integration Tests Exist | 0/1 | 🔴 Failed | No dedicated integration-test directory or equivalent integration-test structure was verifiable from the visible snapshot. |
| Unit Tests Runnable | 0/1 | 🔴 Failed | Tests appear present, but local runnability could not be verified because no test command execution was available in this audit. |
| Test Performance Tracking | 0/1 | 🔴 Failed | No test timing/performance tracking configuration was verifiable from the visible snapshot. |
| Test Coverage Thresholds | 0/1 | 🔴 Failed | No enforceable coverage threshold configuration was verifiable from the visible snapshot. |
| Test File Naming Conventions | 0/1 | 🔴 Failed | No explicit test naming convention configuration was verifiable from the visible snapshot. |
| Test Isolation | 0/1 | 🔴 Failed | No explicit test-isolation or parallelization tooling was verifiable from the visible snapshot. |
| Unit Tests Exist | 1/1 | 🟢 Passed | A `tests` directory is present at the repository root, indicating unit-test coverage exists. |
| Flaky Test Detection | N/A | Skipped | Skipped: no flaky-test tooling was visible, and PR/workflow history inspection required unavailable VCS CLI access. |

## Documentation

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| AGENTS.md File | 0/1 | 🔴 Failed | No `AGENTS.md` file was visible at the repository root. |
| Automated Documentation Generation | 0/1 | 🔴 Failed | `mkdocs.yml` and `docs/` are present, but automated doc generation from code or workflows was not verifiable from the visible snapshot. |
| Skills Configuration | 0/1 | 🔴 Failed | No skills directory or valid skill definitions were verifiable from the visible snapshot. |
| Documentation Freshness | 0/1 | 🔴 Failed | Recent updates to README/AGENTS/CONTRIBUTING within 180 days could not be verified from the provided git snapshot. |
| Service Architecture Documented | 0/1 | 🔴 Failed | No architecture diagram or service-flow documentation was verifiable from the visible snapshot. |
| AGENTS.md Freshness Validation | 0/1 | 🔴 Failed | `AGENTS.md` was not present, so no AGENTS validation automation was evident. |
| README File | 1/1 | 🟢 Passed | `README.md` exists at the repository root. |
| API Schema Docs | N/A | Skipped | Skipped: this repository appears to be a client library, not a service exposing an API schema. |

## Development Environment

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Dev Container | 0/1 | 🔴 Failed | No devcontainer configuration was verifiable from the visible snapshot. |
| Environment Template | 0/1 | 🔴 Failed | No `.env.example` or clearly documented environment template was verifiable from the visible snapshot. |
| Local Services Setup | N/A | Skipped | Skipped: no external service dependencies were evident for this Python library. |
| Database Schema | N/A | Skipped | Skipped: no database-backed application or schema requirement was evident. |
| Devcontainer Runnable | N/A | Skipped | Skipped: no devcontainer was visible to exercise, and devcontainer CLI availability was not established. |

## Debugging & Observability

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Structured Logging | 0/1 | 🔴 Failed | No structured logging library or dedicated logging module was verifiable from the visible snapshot. |
| Distributed Tracing | 0/1 | 🔴 Failed | No request/trace propagation or tracing instrumentation was verifiable from the visible snapshot. |
| Metrics Collection | 0/1 | 🔴 Failed | No metrics or telemetry instrumentation was verifiable from the visible snapshot. |
| Error Tracking Contextualized | 0/1 | 🔴 Failed | No Sentry/Bugsnag/Rollbar-style contextualized error tracking was verifiable from the visible snapshot. |
| Alerting Configured | 0/1 | 🔴 Failed | No alerting or incident notification configuration was verifiable from the visible snapshot. |
| Runbooks Documented | 0/1 | 🔴 Failed | No runbooks directory or runbook references were verifiable from the visible snapshot. |
| Deployment Observability | 0/1 | 🔴 Failed | No deploy-impact dashboard references or deployment observability documentation were verifiable from the visible snapshot. |
| Code Quality Metrics Dashboard | N/A | Skipped | Skipped: no code-quality platform evidence was visible, and deeper inspection required unavailable VCS CLI access. |
| Health Checks | N/A | Skipped | Skipped: this appears to be a library repository rather than a deployed service with health endpoints. |
| Circuit Breakers | N/A | Skipped | Skipped: circuit-breaker patterns were not clearly applicable to this library repository from the visible snapshot. |
| Profiling Instrumentation | N/A | Skipped | Skipped: profiling instrumentation was not clearly applicable to this library repository from the visible snapshot. |

## Security

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| CODEOWNERS File | 0/1 | 🔴 Failed | No `CODEOWNERS` file was verifiable from the visible snapshot. |
| Gitignore Comprehensive | 0/1 | 🔴 Failed | An ignore file likely exists, but comprehensive exclusion of env/build/IDE/OS files could not be verified from the visible snapshot. |
| Secrets Management | 0/1 | 🔴 Failed | No secrets manager integration, encrypted secrets, or documented secrets-handling pattern was verifiable from the visible snapshot. |
| Sensitive Data Log Scrubbing | 0/1 | 🔴 Failed | No log redaction or scrubbing mechanism was verifiable from the visible snapshot. |
| Minimum Dependency Release Age | 0/1 | 🔴 Failed | No minimum dependency release-age policy or tooling was verifiable from the visible snapshot. |
| Dependency Update Automation | 1/1 | 🟢 Passed | Recent commit history includes an automated-looking dependency bump (`actions/setup-python`), which is strong evidence of dependency update automation. |
| Branch Protection | N/A | Skipped | Skipped: branch protection requires authenticated VCS CLI/admin access, which was unavailable. |
| Secret Scanning | N/A | Skipped | Skipped: no secret-scanning tooling was visible, and native repository checks required unavailable VCS CLI/admin access. |
| Automated Security Review Generation | N/A | Skipped | Skipped: no automated security review reports were visible, and native checks required unavailable VCS CLI/admin access. |
| DAST Scanning | N/A | Skipped | Skipped: this appears to be a library repository, not a deployed web service suitable for DAST. |
| PII Handling | N/A | Skipped | Skipped: no end-user data processing was evident for this repository. |
| Privacy Compliance | N/A | Skipped | Skipped: this appears to be a developer library, and no end-user data collection/compliance surface was evident. |

## Task Discovery

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Issue Templates | 0/1 | 🔴 Failed | No issue template directory was verifiable from the visible snapshot. |
| Issue Labeling System | 0/1 | 🔴 Failed | No repository label taxonomy could be verified from the local snapshot without authenticated VCS access. |
| PR Templates | 0/1 | 🔴 Failed | No pull request template was verifiable from the visible snapshot. |
| Backlog Health | N/A | Skipped | Skipped: backlog health requires issue metadata from authenticated VCS CLI access, which was unavailable. |

## Product & Experimentation

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Product Analytics Instrumentation | 0/1 | 🔴 Failed | No product analytics SDK or instrumentation was verifiable from the visible snapshot. |
| Error to Insight Pipeline | 0/1 | 🔴 Failed | No error-to-issue or error-to-insight automation was verifiable from the visible snapshot. |

---

*Generated by Factory Agent Readiness*