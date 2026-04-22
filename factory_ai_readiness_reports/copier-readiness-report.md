# Agent Readiness Report: copier

**Level:** 2/5  
**Overall Score:** 21%  
**Generated:** 2026-04-22 16:59:18 UTC  
**Branch:** master  

## Summary

| Metric | Value |
|--------|-------|
| Total Criteria | 82 |
| Passed | 11 |
| Failed | 42 |
| Skipped | 29 |

## Pass Rate by Category

| Category | Pass Rate |
|----------|-----------|
| Style & Validation | 40% |
| Build System | 11% |
| Testing | 43% |
| Documentation | 29% |
| Development Environment | 0% |
| Debugging & Observability | 0% |
| Security | 17% |
| Task Discovery | 0% |
| Product & Experimentation | 0% |

## Style & Validation

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Naming Consistency | 0/1 | 🔴 Failed | No naming-convention rule or documented naming standard was confirmed. |
| Cyclomatic Complexity | 0/1 | 🔴 Failed | No complexity analysis tool or threshold configuration was confirmed. |
| Large File Detection | 0/1 | 🔴 Failed | No visible LFS config, file-size lint rule, or CI/hook evidence for large-file checks was confirmed from accessible repo metadata. |
| Dead Code Detection | 0/1 | 🔴 Failed | No dead-code detector such as vulture or equivalent configuration was confirmed. |
| Duplicate Code Detection | 0/1 | 🔴 Failed | No duplicate-code detection tooling was confirmed. |
| Technical Debt Tracking | 0/1 | 🔴 Failed | No TODO/FIXME scanner, Sonar config, or other technical-debt tracking mechanism was confirmed from visible files. |
| Linter Configuration | 1/1 | 🟢 Passed | pyproject.toml plus maintained pre-commit tooling is strong evidence that linting is configured for the Python app. |
| Type Checker | 1/1 | 🟢 Passed | Recent git history includes mypy dependency updates, indicating active type-check tooling. |
| Code Formatter | 1/1 | 🟢 Passed | Maintained pre-commit-based Python tooling strongly suggests formatter configuration is present. |
| Pre-commit Hooks | 1/1 | 🟢 Passed | Recent git history includes pre-commit dependency updates, strong evidence that pre-commit hooks are configured. |
| Strict Typing | N/A | Skipped | Skipped: mypy appears present, but strict-mode settings could not be confirmed. |
| Code Modularization Enforcement | N/A | Skipped | Skipped: for a small single-package Python project, explicit boundary tooling may not be meaningful. |
| N+1 Query Detection | N/A | Skipped | Skipped: no database or ORM usage is evident from accessible metadata. |

## Build System

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Build Command Documentation | 0/1 | 🔴 Failed | README.md exists, but accessible local metadata did not confirm a documented build/setup command in README or AGENTS.md. |
| VCS CLI Tools | 0/1 | 🔴 Failed | `gh` is not installed in this environment, so authenticated VCS CLI access is unavailable. |
| Agentic Development | 0/1 | 🔴 Failed | Recent git history shows dependency-bot activity only; no agent config, hook, or workflow evidence was visible. |
| Single Command Setup | 0/1 | 🔴 Failed | devbox.json and devtasks.py suggest reproducible setup, but accessible docs evidence did not confirm a documented fresh-clone single-command path. |
| Feature Flag Infrastructure | 0/1 | 🔴 Failed | No feature-flag SDK, config, or custom flag system was confirmed. |
| Release Notes Automation | 0/1 | 🔴 Failed | CHANGELOG.md exists, but automated release-note generation or publishing could not be confirmed from accessible metadata. |
| Unused Dependencies Detection | 0/1 | 🔴 Failed | No deptry, pip-extra-reqs, or equivalent unused-dependency check was confirmed. |
| Release Automation | 0/1 | 🔴 Failed | No release workflow, release-please, semantic-release, or other automated release pipeline was confirmed from accessible metadata. |
| Dependencies Pinned | 1/1 | 🟢 Passed | uv.lock is committed, so Python dependencies are pinned. |
| Automated PR Review Generation | N/A | Skipped | Skipped: VCS CLI is unavailable and no local evidence of automated PR review comment generation was confirmed. |
| Fast CI Feedback | N/A | Skipped | Skipped: CI timing could not be measured without authenticated VCS CLI access. |
| Build Performance Tracking | N/A | Skipped | Skipped: no workflow timing access and no local build-metrics configuration was confirmed. |
| Deployment Frequency | N/A | Skipped | Skipped: deploy cadence could not be measured from local files and VCS CLI access is unavailable. |
| Progressive Rollout | N/A | Skipped | Skipped: repository appears to be a Python CLI/library rather than an infrastructure/deployment repo. |
| Rollback Automation | N/A | Skipped | Skipped: repository appears to be a Python CLI/library rather than an infrastructure/deployment repo. |
| Monorepo Tooling | N/A | Skipped | Skipped: single-application repository; monorepo tooling is not applicable. |
| Heavy Dependency Detection | N/A | Skipped | Skipped: repository is not a bundled frontend application. |
| Version Drift Detection | N/A | Skipped | Skipped: single-application repository; monorepo version-drift tooling is not applicable. |
| Dead Feature Flag Detection | N/A | Skipped | Skipped: no feature-flag infrastructure was detected. |

## Testing

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Integration Tests Exist | 0/1 | 🔴 Failed | No dedicated integration-test directory or framework was confirmed from accessible files. |
| Test Performance Tracking | 0/1 | 🔴 Failed | No pytest duration reporting, test analytics, or other test-performance tracking was confirmed. |
| Test Coverage Thresholds | 0/1 | 🔴 Failed | No explicit coverage gate or fail-under setting was confirmed. |
| Test Isolation | 0/1 | 🔴 Failed | No parallelization, randomization, or isolated test-environment pattern was confirmed. |
| Unit Tests Exist | 1/1 | 🟢 Passed | A top-level tests/ directory is present. |
| Unit Tests Runnable | 1/1 | 🟢 Passed | tests/, pyproject.toml, and devtasks.py indicate local pytest execution is wired for the root application. |
| Test File Naming Conventions | 1/1 | 🟢 Passed | Python tests live under tests/, which aligns with standard pytest naming/layout conventions. |
| Flaky Test Detection | N/A | Skipped | Skipped: no local flaky-test tooling was confirmed and VCS CLI access is unavailable. |

## Documentation

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| AGENTS.md File | 0/1 | 🔴 Failed | No AGENTS.md file is visible at the repository root. |
| Skills Configuration | 0/1 | 🔴 Failed | No skill directory or valid SKILL.md files were confirmed. |
| Documentation Freshness | 0/1 | 🔴 Failed | Could not confirm README.md, AGENTS.md, or CONTRIBUTING.md updates within the last 180 days from accessible metadata. |
| Service Architecture Documented | 0/1 | 🔴 Failed | Documentation exists, but no architecture/flow diagram or explicit service dependency document was confirmed from visible filenames. |
| AGENTS.md Freshness Validation | 0/1 | 🔴 Failed | AGENTS.md is absent, so no AGENTS.md validation automation is present. |
| README File | 1/1 | 🟢 Passed | README.md exists at the repository root. |
| Automated Documentation Generation | 1/1 | 🟢 Passed | mkdocs.yml, docs/, and mkdocs_hooks.py show automated documentation site generation is configured. |
| API Schema Docs | N/A | Skipped | Skipped: the root application is a CLI/library rather than an HTTP API service. |

## Development Environment

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Dev Container | 0/1 | 🔴 Failed | No .devcontainer configuration was confirmed from accessible files. |
| Environment Template | 0/1 | 🔴 Failed | No .env.example or accessible environment-variable documentation was confirmed. |
| Local Services Setup | N/A | Skipped | Skipped: no external local service dependency is evident for this CLI/library repository. |
| Database Schema | N/A | Skipped | Skipped: no database schema files or DB usage are evident. |
| Devcontainer Runnable | N/A | Skipped | Skipped: devcontainer buildability could not be verified in this environment. |

## Debugging & Observability

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Structured Logging | 0/1 | 🔴 Failed | No structured logging library or dedicated logger module was confirmed. |
| Distributed Tracing | 0/1 | 🔴 Failed | No request/trace propagation tooling was confirmed. |
| Metrics Collection | 0/1 | 🔴 Failed | No metrics or telemetry instrumentation was confirmed. |
| Error Tracking Contextualized | 0/1 | 🔴 Failed | No Sentry, Bugsnag, or Rollbar configuration with context enrichment was confirmed. |
| Alerting Configured | 0/1 | 🔴 Failed | No PagerDuty, OpsGenie, or custom alerting configuration was confirmed. |
| Runbooks Documented | 0/1 | 🔴 Failed | No runbooks directory or incident/runbook references were confirmed. |
| Deployment Observability | 0/1 | 🔴 Failed | No monitoring dashboard references or deploy-impact observability pointers were confirmed. |
| Code Quality Metrics Dashboard | N/A | Skipped | Skipped: no API/CLI access to code scanning and no local Sonar/quality-platform configuration was confirmed. |
| Health Checks | N/A | Skipped | Skipped: the root application is not a deployed web service. |
| Circuit Breakers | N/A | Skipped | Skipped: no external service dependency pattern is evident. |
| Profiling Instrumentation | N/A | Skipped | Skipped: no profiling configuration or meaningful profiling target was confirmed. |

## Security

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| CODEOWNERS File | 0/1 | 🔴 Failed | No CODEOWNERS file was confirmed from accessible files. |
| Gitignore Comprehensive | 0/1 | 🔴 Failed | Could not inspect .gitignore contents to verify exclusion of env files, IDE files, OS files, and build artifacts. |
| Secrets Management | 0/1 | 🔴 Failed | No secrets manager integration, encrypted secrets, or validated env-template pattern was confirmed. |
| Sensitive Data Log Scrubbing | 0/1 | 🔴 Failed | No log redaction or sanitization mechanism was confirmed. |
| Minimum Dependency Release Age | 0/1 | 🔴 Failed | renovate.json exists, but a minimumReleaseAge/stabilityDays policy could not be confirmed. |
| Dependency Update Automation | 1/1 | 🟢 Passed | renovate.json is present, indicating automated dependency update tooling is configured. |
| Branch Protection | N/A | Skipped | Skipped: authenticated VCS CLI access is unavailable, so branch protection could not be queried. |
| Secret Scanning | N/A | Skipped | Skipped: VCS CLI is unavailable and no local secret-scanning configuration was confirmed. |
| Automated Security Review Generation | N/A | Skipped | Skipped: no API/CLI access to code scanning and no local automated security-review reporting config was confirmed. |
| DAST Scanning | N/A | Skipped | Skipped: repository is not a deployed web service. |
| PII Handling | N/A | Skipped | Skipped: no personal-data processing is evident from accessible metadata. |
| Privacy Compliance | N/A | Skipped | Skipped: repository appears to be a developer CLI/library rather than an end-user data collection app. |

## Task Discovery

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Issue Templates | 0/1 | 🔴 Failed | No issue template directory was confirmed from accessible files. |
| Issue Labeling System | 0/1 | 🔴 Failed | A consistent issue label taxonomy cannot be verified from local files alone. |
| PR Templates | 0/1 | 🔴 Failed | No pull request template was confirmed from accessible files. |
| Backlog Health | N/A | Skipped | Skipped: open-issue metadata could not be sampled without authenticated VCS CLI access. |

## Product & Experimentation

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Product Analytics Instrumentation | 0/1 | 🔴 Failed | No product analytics SDK or instrumentation was confirmed. |
| Error to Insight Pipeline | 0/1 | 🔴 Failed | No error-to-issue automation or Sentry/GitHub integration was confirmed. |

---

*Generated by Factory Agent Readiness*