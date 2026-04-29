# Agent Readiness Report: starlette

**Level:** 2/5  
**Overall Score:** 38%  
**Generated:** 2026-04-22 15:42:21 UTC  
**Branch:** main  

## Summary

| Metric | Value |
|--------|-------|
| Total Criteria | 82 |
| Passed | 21 |
| Failed | 34 |
| Skipped | 27 |

## Pass Rate by Category

| Category | Pass Rate |
|----------|-----------|
| Style & Validation | 45% |
| Build System | 44% |
| Testing | 57% |
| Documentation | 43% |
| Development Environment | 0% |
| Debugging & Observability | 13% |
| Security | 33% |
| Task Discovery | 67% |
| Product & Experimentation | 0% |

## Style & Validation

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Pre-commit Hooks | 0/1 | 🔴 Failed | No .pre-commit-config.yaml or equivalent hook configuration is present. |
| Naming Consistency | 0/1 | 🔴 Failed | No naming-convention linter rules or explicit documented naming standard were found. |
| Cyclomatic Complexity | 0/1 | 🔴 Failed | No complexity checker such as Ruff complexity rules, radon, or lizard is configured. |
| Large File Detection | 0/1 | 🔴 Failed | No hook, CI check, LFS policy, or linter rule was found to prevent oversized files. |
| Duplicate Code Detection | 0/1 | 🔴 Failed | No duplicate-code detector such as jscpd, Sonar, or similar tooling was found. |
| Technical Debt Tracking | 0/1 | 🔴 Failed | No TODO/FIXME scanner, Sonar tech-debt tracking, or issue-linked debt enforcement was found. |
| Linter Configuration | 1/1 | 🟢 Passed | Ruff linting is configured in pyproject.toml with multiple rule families enabled. |
| Type Checker | 1/1 | 🟢 Passed | mypy is configured in pyproject.toml with strict mode enabled. |
| Code Formatter | 1/1 | 🟢 Passed | Formatting is handled with Ruff format through the repository scripts. |
| Strict Typing | 1/1 | 🟢 Passed | Strict mypy configuration remains in place for the Python codebase. |
| Dead Code Detection | 1/1 | 🟢 Passed | Ruff/Pyflakes coverage provides unused import and unused variable detection. |
| Code Modularization Enforcement | N/A | Skipped | Skipped for this small single-library repository; boundary-enforcement tooling is not meaningfully applicable. |
| N+1 Query Detection | N/A | Skipped | Skipped because this repository is a framework/library without built-in database or ORM usage. |

## Build System

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| VCS CLI Tools | 0/1 | 🔴 Failed | gh is installed in the environment, but authenticated access was not verified; treat VCS CLI support as unavailable for API-backed checks. |
| Agentic Development | 0/1 | 🔴 Failed | No agent configuration, skills, hooks, or clear AI-agent participation in development workflow were found. |
| Feature Flag Infrastructure | 0/1 | 🔴 Failed | No feature flag platform or custom feature-toggle infrastructure was found. |
| Release Notes Automation | 0/1 | 🔴 Failed | Release notes/changelog generation appears manual rather than automated. |
| Unused Dependencies Detection | 0/1 | 🔴 Failed | No deptry, pip-extra-reqs, or equivalent unused-dependency check was found. |
| Build Command Documentation | 1/1 | 🟢 Passed | README and contributor docs document install, test, lint, and build-oriented commands. |
| Dependencies Pinned | 1/1 | 🟢 Passed | uv.lock is committed, providing pinned dependency versions. |
| Single Command Setup | 1/1 | 🟢 Passed | Contributor docs provide a short scripted setup path for local development. |
| Release Automation | 1/1 | 🟢 Passed | Release automation exists through GitHub Actions publishing/deployment workflows. |
| Automated PR Review Generation | N/A | Skipped | Skipped because authenticated VCS CLI access was not verified, so PR review bot activity could not be confirmed reliably. |
| Fast CI Feedback | N/A | Skipped | Skipped because authenticated VCS CLI access was not verified, so CI durations could not be measured reliably. |
| Build Performance Tracking | N/A | Skipped | Skipped because authenticated VCS CLI access was not verified and no independent build-performance tracking evidence was found. |
| Deployment Frequency | N/A | Skipped | Skipped because authenticated VCS CLI access was not verified, so deployment cadence could not be measured reliably. |
| Progressive Rollout | N/A | Skipped | Skipped because this is a library repository, not an infrastructure repo with staged rollouts. |
| Rollback Automation | N/A | Skipped | Skipped because this is a library repository, not an infrastructure repo with deploy rollback flows. |
| Monorepo Tooling | N/A | Skipped | Skipped because the repository is not a monorepo. |
| Heavy Dependency Detection | N/A | Skipped | Skipped because this is not a bundled frontend application where bundle-size analysis applies. |
| Version Drift Detection | N/A | Skipped | Skipped because the repository is not a monorepo. |
| Dead Feature Flag Detection | N/A | Skipped | Skipped because no feature flag infrastructure is present. |

## Testing

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Integration Tests Exist | 0/1 | 🔴 Failed | No dedicated integration-test suite or integration-test directory was found. |
| Test Performance Tracking | 0/1 | 🔴 Failed | No pytest duration reporting, test analytics, or timing-focused CI reporting was found. |
| Test Isolation | 0/1 | 🔴 Failed | No pytest-xdist, randomization, or equivalent test-isolation enforcement was found. |
| Unit Tests Exist | 1/1 | 🟢 Passed | A substantial pytest-based test suite exists under tests/. |
| Unit Tests Runnable | 1/1 | 🟢 Passed | The repository is configured to run pytest locally via its documented scripts and pytest configuration. |
| Test Coverage Thresholds | 1/1 | 🟢 Passed | Coverage is enforced with a 100% fail-under threshold in the repository scripts/CI setup. |
| Test File Naming Conventions | 1/1 | 🟢 Passed | pytest naming conventions are consistently used for test files in the suite. |
| Flaky Test Detection | N/A | Skipped | Skipped because authenticated VCS CLI access was not verified and no retry/quarantine tooling was found locally. |

## Documentation

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| AGENTS.md File | 0/1 | 🔴 Failed | No AGENTS.md file exists at the repository root. |
| Skills Configuration | 0/1 | 🔴 Failed | No supported skills directory such as .factory/skills or .skills was found. |
| Service Architecture Documented | 0/1 | 🔴 Failed | No architecture diagram or service-flow documentation was found. |
| AGENTS.md Freshness Validation | 0/1 | 🔴 Failed | AGENTS.md is absent, and no automation exists to validate such a file. |
| README File | 1/1 | 🟢 Passed | README.md exists at the root and documents the project and basic usage. |
| Automated Documentation Generation | 1/1 | 🟢 Passed | MkDocs-based documentation generation/build automation is configured. |
| Documentation Freshness | 1/1 | 🟢 Passed | Core documentation has been updated within the last 180 days, including recent docs commits on the current branch. |
| API Schema Docs | N/A | Skipped | Skipped because Starlette is a framework/library rather than an application exposing its own service API schema. |

## Development Environment

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Dev Container | 0/1 | 🔴 Failed | No .devcontainer/devcontainer.json configuration was found. |
| Environment Template | 0/1 | 🔴 Failed | No .env.example or equivalent environment-variable template/documentation was found. |
| Local Services Setup | N/A | Skipped | Skipped because the library does not require local backing services like databases or caches. |
| Database Schema | N/A | Skipped | Skipped because the repository does not define or depend on an application database schema. |
| Devcontainer Runnable | N/A | Skipped | Skipped because no devcontainer configuration exists to validate. |

## Debugging & Observability

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Structured Logging | 0/1 | 🔴 Failed | No structured logging library or dedicated logging module was found. |
| Distributed Tracing | 0/1 | 🔴 Failed | No request/trace propagation or OpenTelemetry-style tracing configuration was found. |
| Metrics Collection | 0/1 | 🔴 Failed | No metrics instrumentation such as Prometheus, Datadog, or similar telemetry was found. |
| Error Tracking Contextualized | 0/1 | 🔴 Failed | No Sentry, Bugsnag, Rollbar, or equivalent contextual error-tracking setup was found. |
| Alerting Configured | 0/1 | 🔴 Failed | No alerting integration such as PagerDuty, OpsGenie, or custom alert rules was found. |
| Runbooks Documented | 0/1 | 🔴 Failed | No runbooks, playbooks, or references to operational incident guides were found. |
| Deployment Observability | 0/1 | 🔴 Failed | No monitoring dashboard references or deploy-observability documentation was found. |
| Code Quality Metrics Dashboard | 1/1 | 🟢 Passed | Code quality metrics are tracked at least through enforced coverage thresholds in CI/scripts. |
| Health Checks | N/A | Skipped | Skipped because this repository is a library, not a deployed service needing health probes. |
| Circuit Breakers | N/A | Skipped | Skipped because this repository does not implement service-to-service runtime dependencies needing circuit breakers. |
| Profiling Instrumentation | N/A | Skipped | Skipped because production profiling instrumentation is not meaningfully applicable to this library repo. |

## Security

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| CODEOWNERS File | 0/1 | 🔴 Failed | No CODEOWNERS file was found in the root or .github directory. |
| Gitignore Comprehensive | 0/1 | 🔴 Failed | The gitignore coverage is incomplete for common secret, IDE, and OS-generated files. |
| Sensitive Data Log Scrubbing | 0/1 | 🔴 Failed | No log-redaction or log-sanitization mechanism was found. |
| Minimum Dependency Release Age | 0/1 | 🔴 Failed | No explicit dependency waiting-period policy such as minimumReleaseAge or stabilityDays was found. |
| Dependency Update Automation | 1/1 | 🟢 Passed | Dependabot automation is configured, and recent commit history shows automated dependency bump PRs. |
| Secrets Management | 1/1 | 🟢 Passed | Secure secrets-management patterns are present via GitHub Actions secrets usage and no hardcoded secrets evidence. |
| Branch Protection | N/A | Skipped | Skipped because authenticated admin-capable VCS CLI access was not verified. |
| Secret Scanning | N/A | Skipped | Skipped because admin-capable VCS CLI access was not verified and no alternative secret-scanning automation was found. |
| Automated Security Review Generation | N/A | Skipped | Skipped because admin-capable VCS CLI access was not verified and no local evidence of automated security review reporting was found. |
| DAST Scanning | N/A | Skipped | Skipped because this repository is not a deployed web service with a DAST target. |
| PII Handling | N/A | Skipped | Skipped because this framework/library does not itself process end-user PII as an application. |
| Privacy Compliance | N/A | Skipped | Skipped because this framework/library is not an end-user data collecting application. |

## Task Discovery

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Issue Labeling System | 0/1 | 🔴 Failed | A complete, verifiable label taxonomy for priority/type/area was not established from repository evidence. |
| Issue Templates | 1/1 | 🟢 Passed | Structured GitHub issue templates are present. |
| PR Templates | 1/1 | 🟢 Passed | A pull request template is present under .github. |
| Backlog Health | N/A | Skipped | Skipped because authenticated VCS CLI access was not verified, so issue activity and labeling could not be measured reliably. |

## Product & Experimentation

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Product Analytics Instrumentation | 0/1 | 🔴 Failed | No product analytics instrumentation such as Mixpanel, Amplitude, PostHog, or GA4 was found. |
| Error to Insight Pipeline | 0/1 | 🔴 Failed | No error-to-issue or error-to-insight automation pipeline was found. |

---

*Generated by Factory Agent Readiness*