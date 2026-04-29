# Data

This folder contains source exports copied into the final-analysis bundle plus generated matrices and audit manifests.

- `rq1_comparisons_2026-04-26.*`: copied RQ1 paired comparison export.
- `rq2_phase_metrics_2026-04-26.*`: copied RQ2 clean/degraded process export.
- `rq1_enriched_analysis_matrix.csv`: RQ1 rows with profile-derived fields and analysis flags.
- `rq2_phase_delta_matrix.csv`: RQ2 process rows with paired clean/degraded deltas.
- `manual_audit_scope*`, `case_study_manifest.csv`, and related manifests: audit/review support files.

Copied source exports are sanitized for public handoff: preserved artifact paths are repo-relative provenance paths, not absolute paths from the experiment machine.
