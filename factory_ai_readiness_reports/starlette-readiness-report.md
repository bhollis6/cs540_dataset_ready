# Agent Readiness Report: starlette

**Level:** 2/5  
**Overall Score:** 38%  
**Generated:** 2026-04-13 20:41:10 UTC  
**Commit:** `273ac41`  
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
| Pre-commit Hooks | 0/1 | 🔴 Failed | No .pre-commit-config.yaml or equivalent pre-commit hook configuration found. |
| Naming Consistency | 0/1 | 🔴 Failed | No naming convention rules in ruff config, no documented naming conventions in CONTRIBUTING.md or AGENTS.md. |
| Cyclomatic Complexity | 0/1 | 🔴 Failed | No complexity rules enabled in ruff config (no C90/C selected). No radon or lizard configured. |
| Large File Detection | 0/1 | 🔴 Failed | No git hooks, CI jobs, .gitattributes LFS, or linter rules checking file size found. |
| Duplicate Code Detection | 0/1 | 🔴 Failed | No jscpd, SonarQube, or other duplicate code detection tooling configured. |
| Technical Debt Tracking | 0/1 | 🔴 Failed | No TODO/FIXME scanner in CI, no tech debt tracking tools or enforced TODO-to-issue linking. |
| Linter Configuration | 1/1 | 🟢 Passed | Ruff is configured in pyproject.toml with multiple lint rule sets (E, F, I, FA, UP, RUF100). |
| Type Checker | 1/1 | 🟢 Passed | mypy configured in pyproject.toml with strict = true. |
| Code Formatter | 1/1 | 🟢 Passed | Ruff format used via scripts/lint and scripts/check for code formatting. |
| Strict Typing | 1/1 | 🟢 Passed | mypy strict = true configured in pyproject.toml. 100% type annotated codebase. |
| Dead Code Detection | 1/1 | 🟢 Passed | Ruff 'F' rules (Pyflakes) enabled, which detect unused imports (F401) and unused variables (F841). |
| Code Modularization Enforcement | N/A | Skipped | Skipped - small library project where module boundary enforcement tooling is not meaningful. |
| N+1 Query Detection | N/A | Skipped | Skipped - library without database/ORM usage. |

## Build System

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| VCS CLI Tools | 0/1 | 🔴 Failed | gh CLI is not installed or available in this environment. |
| Agentic Development | 0/1 | 🔴 Failed | No AI coding agent evidence in git log (dependabot is a dependency bot, not an AI agent). No agent config dirs or skills. |
| Feature Flag Infrastructure | 0/1 | 🔴 Failed | No feature flag infrastructure (LaunchDarkly, Statsig, etc.) configured. |
| Release Notes Automation | 0/1 | 🔴 Failed | Release process is manual per contributing.md: manually update changelog, create GitHub release. No semantic-release or changesets. |
| Unused Dependencies Detection | 0/1 | 🔴 Failed | No deptry, pip-extra-reqs, or other unused dependency detection tooling configured. |
| Build Command Documentation | 1/1 | 🟢 Passed | README documents 'pip install starlette'. scripts/README.md and docs/contributing.md document all dev commands (install, test, lint, build). |
| Dependencies Pinned | 1/1 | 🟢 Passed | uv.lock file is committed to the repository, pinning all dependency versions. |
| Single Command Setup | 1/1 | 🟢 Passed | Contributing docs document 'scripts/install' for setup and 'scripts/test' for testing. scripts/README.md lists all dev commands. |
| Release Automation | 1/1 | 🟢 Passed | publish.yml auto-publishes to PyPI on tag push via pypa/gh-action-pypi-publish and deploys docs to Cloudflare/GitHub Pages. |
| Automated PR Review Generation | N/A | Skipped | Skipped - gh CLI not available to verify automated PR review bots. |
| Fast CI Feedback | N/A | Skipped | Skipped - gh CLI not available to measure CI duration. |
| Build Performance Tracking | N/A | Skipped | Skipped - gh CLI not available and no build caching/performance tracking evidence. |
| Deployment Frequency | N/A | Skipped | Skipped - gh CLI not available to measure deployment frequency. |
| Progressive Rollout | N/A | Skipped | Skipped - this is a library, not a deployed service requiring progressive rollout. |
| Rollback Automation | N/A | Skipped | Skipped - this is a library, not an infrastructure-based deployment. |
| Monorepo Tooling | N/A | Skipped | Skipped - single-application repository, not a monorepo. |
| Heavy Dependency Detection | N/A | Skipped | Skipped - Python backend library, not a bundled frontend application. |
| Version Drift Detection | N/A | Skipped | Skipped - single-application repository, not a monorepo. |
| Dead Feature Flag Detection | N/A | Skipped | Skipped - prerequisite feature_flag_infrastructure not met. |

## Testing

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Integration Tests Exist | 0/1 | 🔴 Failed | No dedicated integration test directory (tests/integration/) or integration test framework (Behave, pytest-bdd). Tests use TestClient but no separate integration suite. |
| Test Performance Tracking | 0/1 | 🔴 Failed | No --durations flag in pytest config, no test analytics platform, no test timing output configured. |
| Test Isolation | 0/1 | 🔴 Failed | No pytest-xdist for parallel execution, no test randomization (pytest-randomly), no testcontainers or database isolation patterns. |
| Unit Tests Exist | 1/1 | 🟢 Passed | Extensive test suite in tests/ directory with 20+ test_*.py files covering all modules. |
| Unit Tests Runnable | 1/1 | 🟢 Passed | pytest --collect-only successfully collects tests. pytest configured in pyproject.toml with scripts/test wrapper. |
| Test Coverage Thresholds | 1/1 | 🟢 Passed | Coverage enforced at 100% via 'coverage report --fail-under=100' in scripts/coverage, run in CI. |
| Test File Naming Conventions | 1/1 | 🟢 Passed | Pytest configured in pyproject.toml with strict-config/strict-markers. All tests follow test_*.py naming convention. |
| Flaky Test Detection | N/A | Skipped | Skipped - gh CLI not available and no pytest-rerunfailures or flaky test detection tools found. |

## Documentation

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| AGENTS.md File | 0/1 | 🔴 Failed | No AGENTS.md file exists at repository root. |
| Skills Configuration | 0/1 | 🔴 Failed | No .factory/skills/, .skills/, or .claude/skills/ directories found. |
| Service Architecture Documented | 0/1 | 🔴 Failed | No architecture diagrams (mermaid, plantuml) or service dependency documentation found. |
| AGENTS.md Freshness Validation | 0/1 | 🔴 Failed | Prerequisite agents_md not met. No AGENTS.md validation automation exists. |
| README File | 1/1 | 🟢 Passed | README.md exists with installation, example usage, dependency documentation, and links to full docs. |
| Automated Documentation Generation | 1/1 | 🟢 Passed | mkdocstrings and zensical configured for automated API doc generation. Docs built in CI via scripts/build. |
| Documentation Freshness | 1/1 | 🟢 Passed | README.md modified within last 180 days (April 2026 and February 2026 commits). |
| API Schema Docs | N/A | Skipped | Skipped - Starlette is a framework library, not a service with its own API endpoints. |

## Development Environment

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Dev Container | 0/1 | 🔴 Failed | No .devcontainer/devcontainer.json configuration found. |
| Environment Template | 0/1 | 🔴 Failed | No .env.example file exists and no environment variables documented in README or AGENTS.md. |
| Local Services Setup | N/A | Skipped | Skipped - library without external service dependencies (no Postgres, Redis, etc.). |
| Database Schema | N/A | Skipped | Skipped - library without database usage. |
| Devcontainer Runnable | N/A | Skipped | Skipped - no devcontainer configuration exists. |

## Debugging & Observability

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Structured Logging | 0/1 | 🔴 Failed | No structlog, loguru, or python-json-logger in dependencies. No dedicated logger module found. |
| Distributed Tracing | 0/1 | 🔴 Failed | No OpenTelemetry, X-Request-ID, or trace propagation found in the codebase. |
| Metrics Collection | 0/1 | 🔴 Failed | No Prometheus, Datadog, or other metrics/telemetry instrumentation found. |
| Error Tracking Contextualized | 0/1 | 🔴 Failed | No Sentry, Bugsnag, or Rollbar configured in the library. |
| Alerting Configured | 0/1 | 🔴 Failed | No PagerDuty, OpsGenie, or alerting rules configured. |
| Runbooks Documented | 0/1 | 🔴 Failed | No runbooks, playbooks, or incident response documentation found. |
| Deployment Observability | 0/1 | 🔴 Failed | No monitoring dashboard links, deploy notifications, or observability references found. |
| Code Quality Metrics Dashboard | 1/1 | 🟢 Passed | Coverage enforced at 100% threshold (--fail-under=100) in CI. Coverage metrics actively monitored. |
| Health Checks | N/A | Skipped | Skipped - Starlette is a library/framework, not a deployed service requiring health checks. |
| Circuit Breakers | N/A | Skipped | Skipped - library without external service call dependencies. |
| Profiling Instrumentation | N/A | Skipped | Skipped - library where production profiling instrumentation is not meaningfully applicable. |

## Security

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| CODEOWNERS File | 0/1 | 🔴 Failed | No CODEOWNERS file found in root or .github/ directory. |
| Gitignore Comprehensive | 0/1 | 🔴 Failed | Missing .env exclusion, .DS_Store, .idea, .vscode from .gitignore. Has build artifacts and venv covered. |
| Sensitive Data Log Scrubbing | 0/1 | 🔴 Failed | No log sanitization, redaction, or scrubbing mechanisms found. |
| Minimum Dependency Release Age | 0/1 | 🔴 Failed | No minimumReleaseAge/stabilityDays in dependabot config. No documented dependency delay policy. |
| Dependency Update Automation | 1/1 | 🟢 Passed | Dependabot configured in .github/dependabot.yml for both uv packages and GitHub Actions with monthly schedule. |
| Secrets Management | 1/1 | 🟢 Passed | GitHub Actions secrets used properly (secrets.CLOUDFLARE_API_TOKEN). No hardcoded secrets. .venv/.env patterns managed via venv gitignore. |
| Branch Protection | N/A | Skipped | Skipped - gh CLI not available to verify branch protection rules. |
| Secret Scanning | N/A | Skipped | Skipped - gh CLI not available and no gitleaks/trufflehog in CI workflows. |
| Automated Security Review Generation | N/A | Skipped | Skipped - gh CLI not available and no CodeQL/Semgrep/Snyk in CI workflows. |
| DAST Scanning | N/A | Skipped | Skipped - library not deployed as a web service. |
| PII Handling | N/A | Skipped | Skipped - framework library without end-user data collection. |
| Privacy Compliance | N/A | Skipped | Skipped - framework library without end-user data collection. |

## Task Discovery

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Issue Labeling System | 0/1 | 🔴 Failed | No label system evidence in issue templates. Cannot verify labels without gh CLI. |
| Issue Templates | 1/1 | 🟢 Passed | .github/ISSUE_TEMPLATE/ exists with structured issue template and config.yml linking to discussions. |
| PR Templates | 1/1 | 🟢 Passed | .github/pull_request_template.md exists with summary section and checklist for tests/docs. |
| Backlog Health | N/A | Skipped | Skipped - gh CLI not available to analyze issue quality and activity. |

## Product & Experimentation

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Product Analytics Instrumentation | 0/1 | 🔴 Failed | No Mixpanel, Amplitude, PostHog, or GA4 instrumentation found. |
| Error to Insight Pipeline | 0/1 | 🔴 Failed | No Sentry-GitHub integration or error-to-issue automation found. |

---

*Generated by Factory Agent Readiness*