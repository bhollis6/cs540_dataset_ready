# Evidence And Audit Appendix

This appendix explains what was checked and how much confidence to put in the exported scoring fields.

## Manual Audit Scope

The manual audit scope is **79 unique paired comparisons**, which equals **158 individual Codex runs** because every comparison has one clean run and one degraded run.

This scope covers every high-risk category without pretending that every line of all 256 run logs was reread manually.

| Audit bucket | Unique comparisons | Individual runs |
| --- | ---: | ---: |
| Clean passed, degraded failed | 11 | 22 |
| Regression-test damage | 11 | 22 |
| Top 12 absolute token deltas | 12 | 24 |
| Top 8 degraded-cheaper cases | 8 | 16 |
| Remove-tests patch-target shifts | 25 | 50 |
| Low/zero type-hints surface | 19 | 38 |
| Clean-already-failed rows | 27 | 54 |
| Astropy build-compatibility-sensitive rows | 12 | 24 |
| Deduplicated total | 79 | 158 |

The exact audit scope is in:

- `../tables/audit_and_manifests/manual_audit_scope_summary/manual_audit_scope_summary.*`
- `../tables/audit_and_manifests/manual_audit_scope/manual_audit_scope.*`

## What Was Checked

For each audited comparison, the audit scripts programmatically checked:

- the comparison JSON exists,
- clean and degraded oracle logs exist,
- clean and degraded Codex JSONL logs exist,
- exported clean/degraded success fields match the comparison packet,
- target-test and regression-test failure counts match the exported deltas,
- the row is interpreted in the right category: clean-pass to degraded-fail case, regression damage, clean-already-failed, low-signal type-hints, patch-target shift, high-token case, or degraded-cheaper case.

For the 13 comparisons that are either clean-pass/degraded-fail or regression-damage cases, the comparison packet and oracle-log tails were also inspected directly. The failures are real oracle-scored failures, not missing artifact rows.

What this audit does **not** claim: it does not mean every line of every Codex JSONL transcript was manually reread, and it does not validate causal intent inside the model. It validates that the official scoring artifacts exist, the exported outcome fields agree with those artifacts, and the high-risk rows are categorized cautiously.

## Audit Findings

The official scoring classification is valid for the final matrix:

- all 11 clean-pass/degraded-fail cases are naming degradation rows,
- all 11 regression-damage rows have preserved clean/degraded oracle artifacts,
- 10 of 11 regression-damage rows are naming,
- the one non-naming regression-damage row is `astropy__astropy-14365 x comments_docstrings`, where clean already failed the target,
- all audited rows have both clean and degraded agent JSONL logs.

Residual uncertainty is low for official target/regression scoring. It is medium for process interpretation because current Codex logs do not provide reliable timestamps or phase-specific token splits.

## Interpretation Rules

- If clean passed and degraded failed, count it as degradation-associated outcome damage.
- If clean already failed, do **not** count degraded target failure as degradation-caused.
- If degraded failed more regression tests, count it as regression damage even when the task already failed clean.
- If type-hints had zero or one annotation node, treat the row as valid but weak evidence for the type-hints condition.
- If remove-tests shifted the patch target, treat it as a strategy/process result. Official scoring remains valid because oracle replay restores the official tests.

## Validation Summary

The validation table checks:

- RQ1 row count = 128.
- RQ2 row count = 256.
- Unique tasks = 32.
- Represented repos = 11.
- Fully complete repos = 10.
- Clean-pass to degraded-fail cases = 11.
- Regression-damage rows = 11.
- No duplicate `(instance_id, condition, replication_index)` rows.
- Corrected tokens use `input_tokens + output_tokens`.
- RQ1 rows match comparison JSON packets for success flags, target/regression counts, selected condition, replication index, and core deltas.

The generated validation artifacts are:

- `../tables/sensitivity_and_validation/validation_summary/validation_summary.*`
- `../data/validation_summary.csv`
