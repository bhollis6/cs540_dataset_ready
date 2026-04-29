from __future__ import annotations

from common import DATA_DIR, TABLE_DIR, enriched_rq1, ensure_dirs, load_rq2, write_csv, write_markdown_table
from build_analysis_tables import rq2_correlations, rq2_delta_table, rq2_phase_summary


def main() -> None:
    ensure_dirs()
    rq1 = enriched_rq1()
    rq2 = load_rq2()
    delta = rq2_delta_table(rq2, rq1)
    summary = rq2_phase_summary(delta)
    correlations = rq2_correlations(delta)
    write_csv(delta, DATA_DIR / "rq2_phase_delta_matrix.csv")
    write_csv(summary, TABLE_DIR / "rq2_phase_metric_summary.csv")
    write_markdown_table(summary, TABLE_DIR / "rq2_phase_metric_summary.md")
    write_csv(correlations, TABLE_DIR / "rq2_phase_correlations.csv")
    write_markdown_table(correlations, TABLE_DIR / "rq2_phase_correlations.md")
    print(f"Wrote RQ2 enriched metrics to {DATA_DIR} and {TABLE_DIR}")


if __name__ == "__main__":
    main()
