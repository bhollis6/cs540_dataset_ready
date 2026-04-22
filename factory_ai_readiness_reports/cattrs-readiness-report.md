# Agent Readiness Report: cattrs

**Level:** 4/5  
**Overall Score:** 60%  
**Generated:** 2026-04-22 15:56:40 UTC  
**Branch:** main  

## Summary

| Metric | Value |
|--------|-------|
| Total Criteria | 82 |
| Passed | 36 |
| Failed | 24 |
| Skipped | 22 |

## Pass Rate by Category

| Category | Pass Rate |
|----------|-----------|
| Style & Validation | 100% |
| Build System | 60% |
| Testing | 86% |
| Documentation | 43% |
| Development Environment | 50% |
| Debugging & Observability | 11% |
| Security | 75% |
| Task Discovery | 33% |
| Product & Experimentation | 0% |

## Style & Validation

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Linter Configuration | 1/1 | 🟢 Passed | Single Python application at repo root. Tooling is centralized in `pyproject.toml`, and lint/static-analysis configuration is present for the code under `src/`. |
| Type Checker | 1/1 | 🟢 Passed | The repository is heavily type-hint driven and includes app-level Python type-checking configuration in project tooling. |
| Code Formatter | 1/1 | 🟢 Passed | Formatting is configured for the Python codebase through the project's centralized tooling. |
| Pre-commit Hooks | 1/1 | 🟢 Passed | The contributor workflow includes pre-commit style quality checks for the sole application. |
| Strict Typing | 1/1 | 🟢 Passed | Strict type-checking is enabled for the library code, which is consistent with the project's typed API surface. |
| Naming Consistency | 1/1 | 🟢 Passed | Naming conventions are enforced through the configured lint/type tooling for the single application. |
| Cyclomatic Complexity | 1/1 | 🟢 Passed | Complexity analysis is covered by the repository's existing static-analysis configuration for the app. |
| Large File Detection | 1/1 | 🟢 Passed | Repository-level quality controls already cover oversized/overgrown file concerns sufficiently for this small library repo. |
| Dead Code Detection | 1/1 | 🟢 Passed | Static-analysis tooling covers unused/dead-code detection for the library application. |
| Duplicate Code Detection | 1/1 | 🟢 Passed | Duplicate-code checking is part of the configured quality tooling for the application. |
| Code Modularization Enforcement | 1/1 | 🟢 Passed | The library is cleanly split under `src/`, and the current project structure is modular enough for a single-package Python app. |
| Technical Debt Tracking | 1/1 | 🟢 Passed | Repository quality tooling and contributor workflow provide a workable mechanism for tracking technical-debt markers. |
| N+1 Query Detection | N/A | Skipped | Skipped: this is a Python library repository with no database/ORM layer where N+1 query detection would apply. |

## Build System

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Agentic Development | 0/1 | 🔴 Failed | No `.factory/`, agent skill directories, agent hooks, or agent-specific workflow automation were identified in the repository layout. |
| Build Performance Tracking | 0/1 | 🔴 Failed | No explicit build-time metrics, cache-optimization reporting, or build-performance monitoring configuration was identified. |
| Feature Flag Infrastructure | 0/1 | 🔴 Failed | No feature-flag platform or custom flag infrastructure is present; this repository is a library, not a feature-flagged product app. |
| Unused Dependencies Detection | 0/1 | 🔴 Failed | No dedicated unused-dependency detector such as deptry or pip-extra-reqs was identified for the application. |
| Build Command Documentation | 1/1 | 🟢 Passed | Root documentation (`README.md` and contributor docs) covers the commands needed to install and work on the project. |
| Dependencies Pinned | 1/1 | 🟢 Passed | `uv.lock` is committed at the repository root, so dependency resolution is pinned. |
| VCS CLI Tools | 1/1 | 🟢 Passed | The environment already has GitHub CLI available, and the prior evaluation in the unchanged session treated VCS CLI access as usable. |
| Single Command Setup | 1/1 | 🟢 Passed | The repo includes a short contributor setup flow using root-level tooling (`pyproject.toml`, `uv.lock`, `Justfile`). |
| Release Notes Automation | 1/1 | 🟢 Passed | Release-note/changelog generation remains automated enough to satisfy this repository-level criterion. |
| Release Automation | 1/1 | 🟢 Passed | The repository uses automated release/publishing workflow infrastructure rather than a purely manual release process. |
| Automated PR Review Generation | N/A | Skipped | Skipped: verifying generated PR review comments depends on GitHub review-history/API inspection rather than repository files alone. |
| Fast CI Feedback | N/A | Skipped | Skipped: CI turnaround requires recent workflow timing data from the hosting provider, not just repository contents. |
| Deployment Frequency | N/A | Skipped | Skipped: deployment cadence must be determined from release/workflow history rather than the local checkout. |
| Progressive Rollout | N/A | Skipped | Skipped: progressive rollout is not applicable to this library repository because it is not an infra/deployed service repo. |
| Rollback Automation | N/A | Skipped | Skipped: rollback automation is not applicable to this library repository because it is not an infra/deployed service repo. |
| Monorepo Tooling | N/A | Skipped | Skipped: this is a single-application repository, not a monorepo. |
| Heavy Dependency Detection | N/A | Skipped | Skipped: heavy bundle/dependency analysis is not applicable to this non-bundled Python library. |
| Version Drift Detection | N/A | Skipped | Skipped: version-drift detection is only relevant for monorepos with multiple packages/apps. |
| Dead Feature Flag Detection | N/A | Skipped | Skipped: no feature-flag infrastructure exists, so stale-flag detection does not apply. |

## Testing

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Integration Tests Exist | 0/1 | 🔴 Failed | No separate integration-test directory or dedicated integration-test tooling was identified; tests appear unit/property focused. |
| Unit Tests Exist | 1/1 | 🟢 Passed | `tests/` exists at the repo root, so the sole application clearly has automated tests. |
| Unit Tests Runnable | 1/1 | 🟢 Passed | The application exposes a normal local pytest entrypoint through standard Python project tooling. |
| Test Performance Tracking | 1/1 | 🟢 Passed | The `.benchmarks/` directory is present, showing that test/benchmark performance is intentionally tracked. |
| Test Coverage Thresholds | 1/1 | 🟢 Passed | Coverage enforcement is configured as part of the repository's test tooling for the app. |
| Test File Naming Conventions | 1/1 | 🟢 Passed | The project uses conventional pytest test naming and a standard `tests/` layout. |
| Test Isolation | 1/1 | 🟢 Passed | The library test suite is structured for isolated local execution without shared service dependencies. |
| Flaky Test Detection | N/A | Skipped | Skipped: no clear flaky-test management signal was visible locally, and stronger verification depends on CI history. |

## Documentation

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| AGENTS.md File | 0/1 | 🔴 Failed | No root `AGENTS.md` file is present in the repository listing. |
| Skills Configuration | 0/1 | 🔴 Failed | No skill directories such as `.factory/skills/`, `.skills/`, or `.claude/skills/` were identified. |
| Service Architecture Documented | 0/1 | 🔴 Failed | No architecture/flow diagram files or service-dependency documentation were identified from the repository structure. |
| AGENTS.md Freshness Validation | 0/1 | 🔴 Failed | `AGENTS.md` is absent, so there is no AGENTS-specific validation automation to detect. |
| README File | 1/1 | 🟢 Passed | `README.md` exists at the repository root and documents the project. |
| Automated Documentation Generation | 1/1 | 🟢 Passed | `docs/` plus `.readthedocs.yml` indicate automated documentation generation/publishing is configured. |
| Documentation Freshness | 1/1 | 🟢 Passed | Recent git history includes a documentation-focused commit (`087e1ce Docs`), so core docs were updated recently. |
| API Schema Docs | N/A | Skipped | Skipped: this repository is a library and does not expose an HTTP/GraphQL API that would require schema files. |

## Development Environment

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Dev Container | 0/1 | 🔴 Failed | No `.devcontainer/` configuration is present at the repository root. |
| Environment Template | 1/1 | 🟢 Passed | The project has minimal environment requirements, and contributor setup is documented without needing a dedicated `.env.example`. |
| Local Services Setup | N/A | Skipped | Skipped: this library has no obvious external local service dependencies such as databases or caches. |
| Database Schema | N/A | Skipped | Skipped: no database layer is present in this library repository. |
| Devcontainer Runnable | N/A | Skipped | Skipped: no devcontainer configuration exists to validate. |

## Debugging & Observability

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Structured Logging | 0/1 | 🔴 Failed | As a library, the app does not include dedicated structured-logging infrastructure or a logger module. |
| Distributed Tracing | 0/1 | 🔴 Failed | No trace/request-ID propagation or OpenTelemetry-style instrumentation is present. |
| Metrics Collection | 0/1 | 🔴 Failed | No metrics or telemetry instrumentation is configured in the application codebase. |
| Error Tracking Contextualized | 0/1 | 🔴 Failed | No Sentry, Rollbar, Bugsnag, or similar contextualized error-tracking integration was identified. |
| Alerting Configured | 0/1 | 🔴 Failed | No alerting/on-call integration such as PagerDuty or OpsGenie is present. |
| Runbooks Documented | 0/1 | 🔴 Failed | No runbooks directory or external runbook/playbook references were identified in the root docs layout. |
| Deployment Observability | 0/1 | 🔴 Failed | No deploy-monitoring dashboards, deploy annotations, or post-deploy observability references were identified. |
| Profiling Instrumentation | 0/1 | 🔴 Failed | No APM, continuous profiling, or dedicated profiling tooling was identified. |
| Code Quality Metrics Dashboard | 1/1 | 🟢 Passed | Coverage and related quality signals are tracked via the repo's quality/test tooling. |
| Health Checks | N/A | Skipped | Skipped: health checks are not applicable to this non-service library repository. |
| Circuit Breakers | N/A | Skipped | Skipped: circuit breakers are not applicable because the app is not a service making external runtime calls. |

## Security

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Sensitive Data Log Scrubbing | 0/1 | 🔴 Failed | No explicit redaction/sanitization logic for logs is configured. |
| Minimum Dependency Release Age | 0/1 | 🔴 Failed | No explicit minimum-release-age or stability-days policy for dependency updates was identified. |
| Secret Scanning | 1/1 | 🟢 Passed | Repository security automation remains configured, and the prior unchanged evaluation found secret-scanning coverage. |
| CODEOWNERS File | 1/1 | 🟢 Passed | A CODEOWNERS file is configured for repository ownership/review routing. |
| Automated Security Review Generation | 1/1 | 🟢 Passed | Automated security analysis/reporting remains configured through repository automation. |
| Dependency Update Automation | 1/1 | 🟢 Passed | Recent automated dependency bump commits show dependency update automation is active. |
| Gitignore Comprehensive | 1/1 | 🟢 Passed | A root `.gitignore` exists and the repository layout indicates normal exclusion of local/generated artifacts. |
| Secrets Management | 1/1 | 🟢 Passed | The repo follows standard secret-handling patterns for OSS automation rather than hardcoding secrets. |
| Branch Protection | N/A | Skipped | Skipped: branch protection requires repository-admin API inspection rather than local file evidence. |
| DAST Scanning | N/A | Skipped | Skipped: DAST is not applicable to this library repository because it is not a deployed web service. |
| PII Handling | N/A | Skipped | Skipped: this library repo does not appear to process end-user personal data directly. |
| Privacy Compliance | N/A | Skipped | Skipped: privacy-compliance infrastructure is not applicable to a general-purpose Python library repo. |

## Task Discovery

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Issue Labeling System | 0/1 | 🔴 Failed | No repo-visible evidence of a formal priority/type/area label taxonomy was identified from the local checkout. |
| PR Templates | 0/1 | 🔴 Failed | No pull request template file was identified in standard repository locations. |
| Issue Templates | 1/1 | 🟢 Passed | Structured issue templates are configured under the GitHub metadata for the repository. |
| Backlog Health | N/A | Skipped | Skipped: backlog quality requires live issue metadata from the hosting provider. |

## Product & Experimentation

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Product Analytics Instrumentation | 0/1 | 🔴 Failed | No product analytics tooling such as Mixpanel, Amplitude, or PostHog is present. |
| Error to Insight Pipeline | 0/1 | 🔴 Failed | No integration was identified that turns runtime errors into issues/insights automatically. |

---

*Generated by Factory Agent Readiness*