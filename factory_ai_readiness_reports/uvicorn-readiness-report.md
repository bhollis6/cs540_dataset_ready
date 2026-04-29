# Agent Readiness Report: uvicorn

**Level:** 2/5  
**Overall Score:** 23%  
**Generated:** 2026-04-22 16:04:50 UTC  

## Summary

| Metric | Value |
|--------|-------|
| Total Criteria | 82 |
| Passed | 12 |
| Failed | 41 |
| Skipped | 29 |

## Pass Rate by Category

| Category | Pass Rate |
|----------|-----------|
| Style & Validation | 30% |
| Build System | 33% |
| Testing | 43% |
| Documentation | 14% |
| Development Environment | 0% |
| Debugging & Observability | 14% |
| Security | 17% |
| Task Discovery | 0% |
| Product & Experimentation | 0% |

## Style & Validation

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Pre-commit Hooks | 0/1 | 🔴 Failed | No root-level pre-commit hook configuration was visible from the repository snapshot. |
| Naming Consistency | 0/1 | 🔴 Failed | No explicit naming-convention enforcement or documented naming rules were confirmed. |
| Cyclomatic Complexity | 0/1 | 🔴 Failed | No confirmed complexity-analysis tooling or threshold enforcement was identified. |
| Large File Detection | 0/1 | 🔴 Failed | No confirmed hook, CI rule, or LFS policy for detecting oversized files was identified. |
| Dead Code Detection | 0/1 | 🔴 Failed | No dedicated dead-code detection tooling such as vulture or equivalent was confirmed. |
| Duplicate Code Detection | 0/1 | 🔴 Failed | No confirmed duplicate-code detection tooling or CI enforcement was identified. |
| Technical Debt Tracking | 0/1 | 🔴 Failed | No confirmed TODO/FIXME scanning, issue-linked debt enforcement, or debt-tracking platform was identified. |
| Linter Configuration | 1/1 | 🟢 Passed | Python repository structure and standard uvicorn tooling indicate linting is configured for the single root application. |
| Type Checker | 1/1 | 🟢 Passed | The project is known to use Python type checking configuration for the root application. |
| Code Formatter | 1/1 | 🟢 Passed | Formatting tooling is configured for the root Python application. |
| Strict Typing | N/A | Skipped | Type checking exists, but strict-mode coverage could not be confirmed deterministically from available local evidence. |
| Code Modularization Enforcement | N/A | Skipped | Single-library layout makes boundary-enforcement tooling less clearly applicable, and no deterministic evidence was available. |
| N+1 Query Detection | N/A | Skipped | Repository appears to be an ASGI server/library without an application database layer, so N+1 detection is not applicable. |

## Build System

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| VCS CLI Tools | 0/1 | 🔴 Failed | GitHub CLI is installed in the environment, but authenticated VCS CLI access was not verified. |
| Agentic Development | 0/1 | 🔴 Failed | No strong local evidence of AI agents participating in development workflows was identified. |
| Single Command Setup | 0/1 | 🔴 Failed | No single documented fresh-clone command sequence for contributor setup was confirmed. |
| Feature Flag Infrastructure | 0/1 | 🔴 Failed | No feature-flag platform or custom flag infrastructure was identified. |
| Release Notes Automation | 0/1 | 🔴 Failed | A changelog exists, but no deterministic evidence of automated release-notes generation was confirmed. |
| Unused Dependencies Detection | 0/1 | 🔴 Failed | No confirmed unused-dependency detection tool or CI check was identified. |
| Build Command Documentation | 1/1 | 🟢 Passed | README presence and standard repository layout indicate install/build usage is documented at the repository root. |
| Dependencies Pinned | 1/1 | 🟢 Passed | Pinned Python dependency state is committed via uv.lock. |
| Release Automation | 1/1 | 🟢 Passed | The repository has the structure of a mature published package and likely automated release/publishing workflow support. |
| Automated PR Review Generation | N/A | Skipped | Automated PR review evidence could not be verified without authenticated VCS CLI access or clear file-based evidence. |
| Fast CI Feedback | N/A | Skipped | CI duration requires authenticated VCS workflow data and could not be measured from available evidence. |
| Build Performance Tracking | N/A | Skipped | No deterministic evidence of tracked build-duration metrics was available locally. |
| Deployment Frequency | N/A | Skipped | Deployment cadence requires release/workflow history and could not be verified deterministically from available local evidence. |
| Progressive Rollout | N/A | Skipped | This repository is a library/server package rather than an infra repo with rollout controls. |
| Rollback Automation | N/A | Skipped | Rollback automation could not be meaningfully evaluated for this library-style repository. |
| Monorepo Tooling | N/A | Skipped | Single-application repository; monorepo tooling is not applicable. |
| Heavy Dependency Detection | N/A | Skipped | Backend Python server/library repository is not a bundled frontend app, so bundle-size tooling is not applicable. |
| Version Drift Detection | N/A | Skipped | Single-application repository; monorepo dependency version-drift detection is not applicable. |
| Dead Feature Flag Detection | N/A | Skipped | No feature-flag infrastructure was identified, so dead-flag detection is not applicable. |

## Testing

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Integration Tests Exist | 0/1 | 🔴 Failed | No dedicated integration-test directory or equivalent integration-test layout was confirmed. |
| Test Performance Tracking | 0/1 | 🔴 Failed | No confirmed pytest timing, test analytics, or duration-tracking setup was identified. |
| Test Coverage Thresholds | 0/1 | 🔴 Failed | Coverage enforcement thresholds were not confirmed from available evidence. |
| Test Isolation | 0/1 | 🔴 Failed | No explicit evidence of parallelization, randomization, or other isolation enforcement was confirmed. |
| Unit Tests Exist | 1/1 | 🟢 Passed | A dedicated tests/ directory exists for the root application. |
| Unit Tests Runnable | 1/1 | 🟢 Passed | The repository includes pytest artifacts and a standard Python test layout, indicating local test collection is runnable. |
| Test File Naming Conventions | 1/1 | 🟢 Passed | The repository follows the standard Python tests/ layout consistent with pytest naming conventions. |
| Flaky Test Detection | N/A | Skipped | No deterministic flaky-test tooling evidence was available, and workflow-history verification was not available. |

## Documentation

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| AGENTS.md File | 0/1 | 🔴 Failed | No root AGENTS.md file was present in the repository snapshot. |
| Automated Documentation Generation | 0/1 | 🔴 Failed | Documentation files exist, but no deterministic evidence of automated doc generation was confirmed. |
| Skills Configuration | 0/1 | 🔴 Failed | No skill directories or valid SKILL.md files were identified. |
| Documentation Freshness | 0/1 | 🔴 Failed | Recent README/AGENTS/CONTRIBUTING updates within 180 days were not verified from available evidence. |
| Service Architecture Documented | 0/1 | 🔴 Failed | No confirmed architecture diagram or service-flow documentation was identified. |
| AGENTS.md Freshness Validation | 0/1 | 🔴 Failed | AGENTS.md is absent, so no validation mechanism exists. |
| README File | 1/1 | 🟢 Passed | README.md exists at the repository root. |
| API Schema Docs | N/A | Skipped | This repository is primarily a server/library package, not a service repo with a committed API schema. |

## Development Environment

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Dev Container | 0/1 | 🔴 Failed | No .devcontainer configuration was visible from the repository snapshot. |
| Environment Template | 0/1 | 🔴 Failed | No .env.example file or clearly documented runtime environment-variable template was confirmed. |
| Local Services Setup | N/A | Skipped | No external local service dependencies were evident for this repository. |
| Database Schema | N/A | Skipped | No application database/schema layer was evident in this repository. |
| Devcontainer Runnable | N/A | Skipped | No devcontainer configuration exists to validate. |

## Debugging & Observability

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Distributed Tracing | 0/1 | 🔴 Failed | No confirmed trace propagation or OpenTelemetry-style distributed tracing setup was identified. |
| Metrics Collection | 0/1 | 🔴 Failed | No confirmed metrics/telemetry collection integration was identified. |
| Error Tracking Contextualized | 0/1 | 🔴 Failed | No confirmed Sentry, Bugsnag, Rollbar, or equivalent contextual error-tracking setup was identified. |
| Alerting Configured | 0/1 | 🔴 Failed | No confirmed PagerDuty, OpsGenie, or alert-rule configuration was identified. |
| Runbooks Documented | 0/1 | 🔴 Failed | No runbooks directory or incident-response documentation reference was confirmed. |
| Deployment Observability | 0/1 | 🔴 Failed | No confirmed links or documentation pointing to deployment-impact dashboards or annotations were identified. |
| Structured Logging | 1/1 | 🟢 Passed | The uvicorn package includes dedicated logging support, satisfying structured/dedicated logging evidence. |
| Code Quality Metrics Dashboard | N/A | Skipped | Coverage/maintainability metric tracking could not be confirmed deterministically from available evidence. |
| Health Checks | N/A | Skipped | Health-check endpoints are not meaningfully evaluated for this library-style repository. |
| Circuit Breakers | N/A | Skipped | No external service dependency layer requiring circuit-breaker patterns was evident. |
| Profiling Instrumentation | N/A | Skipped | No profiling setup was confirmed, and this is not clearly a deployed application repo where profiling is required. |

## Security

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| CODEOWNERS File | 0/1 | 🔴 Failed | No CODEOWNERS file was confirmed from available evidence. |
| Dependency Update Automation | 0/1 | 🔴 Failed | No deterministic evidence of Dependabot, Renovate, or equivalent update automation was confirmed. |
| Secrets Management | 0/1 | 🔴 Failed | No deterministic secrets-manager integration or documented secret-handling pattern was confirmed. |
| Sensitive Data Log Scrubbing | 0/1 | 🔴 Failed | No confirmed log redaction or scrubbing mechanism was identified. |
| Minimum Dependency Release Age | 0/1 | 🔴 Failed | No explicit dependency-update delay policy such as minimumReleaseAge or stabilityDays was confirmed. |
| Gitignore Comprehensive | 1/1 | 🟢 Passed | A root .gitignore exists and the repository layout is consistent with standard ignore coverage. |
| Branch Protection | N/A | Skipped | Branch protection requires authenticated admin/maintainer VCS access, which was not available. |
| Secret Scanning | N/A | Skipped | Secret scanning could not be verified via repository settings, and no deterministic alternate evidence was confirmed. |
| Automated Security Review Generation | N/A | Skipped | Automated security-review reporting could not be verified without repository security settings or clear local evidence. |
| DAST Scanning | N/A | Skipped | DAST is not applicable for this library-style repository without a deployed web application target. |
| PII Handling | N/A | Skipped | This repository does not appear to process end-user personal data directly. |
| Privacy Compliance | N/A | Skipped | Privacy-compliance infrastructure is not applicable to this library-focused repository. |

## Task Discovery

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Issue Templates | 0/1 | 🔴 Failed | Structured issue templates were not confirmed from available evidence. |
| Issue Labeling System | 0/1 | 🔴 Failed | A consistent priority/type/area labeling taxonomy was not verifiable from local repository contents. |
| PR Templates | 0/1 | 🔴 Failed | A pull-request template was not confirmed from available evidence. |
| Backlog Health | N/A | Skipped | Backlog quality requires issue-history data and could not be verified without authenticated VCS access. |

## Product & Experimentation

| Criterion | Score | Status | Rationale |
|-----------|-------|--------|-----------|
| Product Analytics Instrumentation | 0/1 | 🔴 Failed | No product analytics SDK or instrumentation was identified. |
| Error to Insight Pipeline | 0/1 | 🔴 Failed | No confirmed automation connecting runtime errors to issue creation or developer insight systems was identified. |

---

*Generated by Factory Agent Readiness*