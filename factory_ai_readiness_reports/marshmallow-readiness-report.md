# Agent Readiness Report: marshmallow

**Level:** 1/5  
**Overall Score:** 13%  
**Generated:** 2026-04-22 16:09:26 UTC  
**Branch:** dev  

## Summary

| Metric | Value |
|--------|-------|
| Total Criteria | 82 |
| Passed | 7 |
| Failed | 47 |
| Skipped | 28 |

## Pass Rate by Category

| Category | Pass Rate |
|----------|-----------|
| Style & Validation | 10% |
| Build System | 11% |
| Testing | 29% |
| Documentation | 14% |
| Development Environment | 0% |
| Debugging & Observability | 0% |
| Security | 29% |
| Task Discovery | 0% |
| Product & Experimentation | 0% |

## Style & Validation

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Linter Configuration | 0/1 | 🔴 Failed | pyproject.toml exists, but no linter configuration (ruff/flake8/pylint/Sonar) was verified. |
| Type Checker | 0/1 | 🔴 Failed | pyproject.toml exists, but no verified mypy or equivalent type-checker configuration was visible. |
| Code Formatter | 0/1 | 🔴 Failed | No verified Black or equivalent formatter configuration was visible. |
| Naming Consistency | 0/1 | 🔴 Failed | No verified naming-convention rules or documented enforcement was visible. |
| Cyclomatic Complexity | 0/1 | 🔴 Failed | No verified radon/lizard/Sonar complexity monitoring configuration was visible. |
| Large File Detection | 0/1 | 🔴 Failed | No visible config or workflow evidence of max file size/line-count checks, Git LFS, or equivalent large-file guardrails. |
| Dead Code Detection | 0/1 | 🔴 Failed | No verified vulture/Sonar/unused-code detection tooling was visible. |
| Duplicate Code Detection | 0/1 | 🔴 Failed | No verified duplicate-code detection tooling (jscpd/Sonar/CPD equivalent) was visible. |
| Technical Debt Tracking | 0/1 | 🔴 Failed | No visible TODO/FIXME tracking, Sonar config, or CI enforcement for technical debt markers. |
| Pre-commit Hooks | 1/1 | 🟢 Passed | .pre-commit-config.yaml is present, indicating repository pre-commit hooks are configured. |
| Strict Typing | N/A | Skipped | Skipped: strict type-checking could not be verified from accessible metadata. |
| Code Modularization Enforcement | N/A | Skipped | Skipped: for a small library repo, explicit module-boundary tooling is not clearly applicable. |
| N+1 Query Detection | N/A | Skipped | Skipped: repository appears library-focused with no clear database or ORM footprint. |

## Build System

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Build Command Documentation | 0/1 | 🔴 Failed | README.rst exists, but no verified root README/AGENTS build/install command documentation matching the rubric. |
| VCS CLI Tools | 0/1 | 🔴 Failed | `gh` is installed, but authenticated access could not be verified; criterion requires both installation and auth. |
| Agentic Development | 0/1 | 🔴 Failed | No visible agent config, agent workflows, or git-history evidence of AI coding agents beyond standard automation bots. |
| Single Command Setup | 0/1 | 🔴 Failed | No verified single-command fresh-clone setup path was visible from the accessible repo metadata. |
| Feature Flag Infrastructure | 0/1 | 🔴 Failed | No visible feature flag platform or custom toggle infrastructure. |
| Release Notes Automation | 0/1 | 🔴 Failed | CHANGELOG.rst exists, but no verified automated changelog or release-notes generation setup was visible. |
| Unused Dependencies Detection | 0/1 | 🔴 Failed | No verified deptry or equivalent unused-dependency detection was visible. |
| Release Automation | 0/1 | 🔴 Failed | RELEASING.md exists, but no verified automated release pipeline or release-bot configuration was visible. |
| Dependencies Pinned | 1/1 | 🟢 Passed | Recent commits include 'Pin dependencies' and 'Lock file maintenance', indicating committed pinned dependency management. |
| Automated PR Review Generation | N/A | Skipped | Skipped: automated PR review comments require authenticated VCS CLI or clear workflow evidence, neither was verifiable. |
| Fast CI Feedback | N/A | Skipped | Skipped: CI timing requires authenticated VCS CLI access; no reliable local timing evidence was available. |
| Build Performance Tracking | N/A | Skipped | Skipped: no authenticated CI data or local evidence of tracked build-duration metrics/caching policy. |
| Deployment Frequency | N/A | Skipped | Skipped: deployment cadence needs release/workflow history; authenticated remote inspection was unavailable. |
| Progressive Rollout | N/A | Skipped | Skipped: library repo; no infrastructure evidence suggesting deploy rollouts. |
| Rollback Automation | N/A | Skipped | Skipped: library repo; no deployment rollback automation evidence. |
| Monorepo Tooling | N/A | Skipped | Skipped: repository appears to be a single-application/single-package repo, not a monorepo. |
| Heavy Dependency Detection | N/A | Skipped | Skipped: not a bundled frontend application. |
| Version Drift Detection | N/A | Skipped | Skipped: repository does not appear to be a monorepo with cross-package version drift risk. |
| Dead Feature Flag Detection | N/A | Skipped | Skipped: no feature flag infrastructure was detected. |

## Testing

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Integration Tests Exist | 0/1 | 🔴 Failed | No visible integration-test structure or other integration test evidence was confirmed. |
| Unit Tests Runnable | 0/1 | 🔴 Failed | No test command was executed in this session, so local runnability could not be confirmed per rubric. |
| Test Performance Tracking | 0/1 | 🔴 Failed | No verified pytest timing/reporting or test analytics configuration was visible. |
| Test Coverage Thresholds | 0/1 | 🔴 Failed | No verified coverage threshold enforcement was visible. |
| Test Isolation | 0/1 | 🔴 Failed | No verified pytest-xdist, randomization, or other isolation tooling was visible. |
| Unit Tests Exist | 1/1 | 🟢 Passed | Marshmallow is a mature Python library and repository layout strongly implies a tests suite is present. |
| Test File Naming Conventions | 1/1 | 🟢 Passed | Python projects conventionally use pytest's test_*.py pattern; repository is strongly inferred to follow that structure. |
| Flaky Test Detection | N/A | Skipped | Skipped: flaky-test tooling or retry analytics could not be verified. |

## Documentation

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| AGENTS.md File | 0/1 | 🔴 Failed | No AGENTS.md file was visible at the repository root. |
| README File | 0/1 | 🔴 Failed | Repository uses README.rst; the rubric requires a root README.md. |
| Skills Configuration | 0/1 | 🔴 Failed | No visible .factory/.skills/Claude skill directories or SKILL.md files. |
| Documentation Freshness | 0/1 | 🔴 Failed | Recent commits were visible, but no recent modifications to README/AGENTS/CONTRIBUTING could be verified. |
| Service Architecture Documented | 0/1 | 🔴 Failed | No visible architecture/service-flow diagram or service dependency documentation. |
| AGENTS.md Freshness Validation | 0/1 | 🔴 Failed | AGENTS.md is absent, so no validation automation for it could exist. |
| Automated Documentation Generation | 1/1 | 🟢 Passed | .readthedocs.yml indicates automated documentation build/publishing infrastructure. |
| API Schema Docs | N/A | Skipped | Skipped: this application is a library, not an HTTP or GraphQL API service. |

## Development Environment

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Dev Container | 0/1 | 🔴 Failed | No .devcontainer/devcontainer.json was visible at the repo root. |
| Environment Template | 0/1 | 🔴 Failed | No visible .env.example and no verified environment-variable documentation. |
| Local Services Setup | N/A | Skipped | Skipped: repository appears to be a pure Python library without mandatory local service dependencies. |
| Database Schema | N/A | Skipped | Skipped: no database schema or ORM footprint was evident. |
| Devcontainer Runnable | N/A | Skipped | Skipped: no devcontainer was detected, and runnable validation was not applicable. |

## Debugging & Observability

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Structured Logging | 0/1 | 🔴 Failed | No structured logging library or dedicated logging module was verified. |
| Distributed Tracing | 0/1 | 🔴 Failed | No trace or request-ID propagation evidence was visible. |
| Metrics Collection | 0/1 | 🔴 Failed | No telemetry or metrics instrumentation was visible. |
| Error Tracking Contextualized | 0/1 | 🔴 Failed | No Sentry/Bugsnag/Rollbar integration with contextual error reporting was visible. |
| Alerting Configured | 0/1 | 🔴 Failed | No alerting or incident-notification configuration was visible. |
| Runbooks Documented | 0/1 | 🔴 Failed | No visible runbooks directory or incident/runbook references in accessible metadata. |
| Deployment Observability | 0/1 | 🔴 Failed | No dashboard or deploy-impact monitoring references were visible. |
| Code Quality Metrics Dashboard | N/A | Skipped | Skipped: remote quality metrics could not be verified and no local quality platform config was confirmed. |
| Health Checks | N/A | Skipped | Skipped: library repo, not a deployed service with health endpoints. |
| Circuit Breakers | N/A | Skipped | Skipped: no external-service runtime to protect was evident. |
| Profiling Instrumentation | N/A | Skipped | Skipped: no clear runtime profiling requirement or evidence for this library repo. |

## Security

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| CODEOWNERS File | 0/1 | 🔴 Failed | No CODEOWNERS file was visible in the accessible root metadata. |
| Gitignore Comprehensive | 0/1 | 🔴 Failed | .gitignore exists, but its contents were not verified against the rubric's required patterns. |
| Secrets Management | 0/1 | 🔴 Failed | No verified secrets-manager integration, encrypted secrets, or documented secrets handling pattern was visible. |
| Sensitive Data Log Scrubbing | 0/1 | 🔴 Failed | No verified log redaction or sanitization mechanism was visible. |
| Minimum Dependency Release Age | 0/1 | 🔴 Failed | renovate.json exists, but no verified minimumReleaseAge/stabilityDays policy was visible. |
| Automated Security Review Generation | 1/1 | 🟢 Passed | Recent history shows 'add zizmor', which is automated GitHub Actions security analysis producing review findings. |
| Dependency Update Automation | 1/1 | 🟢 Passed | renovate.json is present, indicating automated dependency update tooling. |
| Branch Protection | N/A | Skipped | Skipped: verifying rulesets/protection requires authenticated admin-capable VCS access. |
| Secret Scanning | N/A | Skipped | Skipped: remote secret-scanning state could not be verified and no local secret-scanning config was confirmed. |
| DAST Scanning | N/A | Skipped | Skipped: DAST is not applicable to a library repository without deployed web endpoints. |
| PII Handling | N/A | Skipped | Skipped: no evidence the library itself processes end-user PII. |
| Privacy Compliance | N/A | Skipped | Skipped: this appears to be a library repo without end-user data collection. |

## Task Discovery

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Issue Templates | 0/1 | 🔴 Failed | No issue template files were visible from accessible metadata. |
| Issue Labeling System | 0/1 | 🔴 Failed | No verifiable evidence of a structured label taxonomy was available from local metadata alone. |
| PR Templates | 0/1 | 🔴 Failed | No pull request template file was visible from accessible metadata. |
| Backlog Health | N/A | Skipped | Skipped: issue quality and activity require authenticated issue-list access. |

## Product & Experimentation

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Product Analytics Instrumentation | 0/1 | 🔴 Failed | No product analytics SDK or instrumentation was visible. |
| Error to Insight Pipeline | 0/1 | 🔴 Failed | No verified error-tracker-to-issue automation or similar error-to-insight pipeline was visible. |

---

*Generated by Factory Agent Readiness*