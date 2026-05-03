#!/usr/bin/env python3
"""Wilcoxon signed-rank tests on paired clean-vs-degraded deltas.

Tests H0: median(delta) = 0 for each (condition, metric) using the combined
paired matrix. Pooled across both backends. Per-backend and per-repo splits
are intentionally out of scope here.

All outputs are written into this script's own directory:
- signed_rank_tests.csv / .md   raw results
- STATS.md                      narrative report
- signed_rank_tests.png         summary figure (median deltas + significance)
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DATA = ROOT / "combined_analysis" / "data"

CONDITIONS = ["naming", "type_hints", "comments_docstrings", "remove_tests"]
CONDITION_LABELS = {
    "naming": "Naming",
    "type_hints": "Type hints",
    "comments_docstrings": "Comments/\ndocstrings",
    "remove_tests": "Remove\ntests",
}
CONDITION_LABELS_FLAT = {
    "naming": "Naming",
    "type_hints": "Type hints",
    "comments_docstrings": "Comments/docstrings",
    "remove_tests": "Remove tests",
}

METRICS = [
    ("token_delta_pct", "Corrected tokens (% of clean)", "%"),
    ("token_delta", "Corrected tokens (absolute)", "tokens"),
    ("files_opened_delta", "Files opened before first edit", "files"),
    ("exploration_efficiency_delta", "Exploration efficiency", "fraction"),
    ("hidden_bug_fix_failed_delta", "Hidden bug-fix failures", "tests"),
    ("regression_failed_delta", "Regression failures", "tests"),
]


def holm(pvals: np.ndarray) -> np.ndarray:
    """Holm-Bonferroni step-down adjustment."""
    pvals = np.asarray(pvals, dtype=float)
    n = len(pvals)
    order = np.argsort(pvals)
    adj = np.empty(n)
    running_max = 0.0
    for rank, idx in enumerate(order):
        candidate = (n - rank) * pvals[idx]
        running_max = max(running_max, candidate)
        adj[idx] = min(running_max, 1.0)
    return adj


def stars(p: float) -> str:
    if np.isnan(p):
        return ""
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return "ns"


def run_tests(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for metric_key, metric_label, _ in METRICS:
        per_metric: list[dict[str, object]] = []
        for condition in CONDITIONS:
            sub = df[df["condition"] == condition]
            deltas = pd.to_numeric(sub[metric_key], errors="coerce").dropna().to_numpy()
            n_total = int(len(deltas))
            n_nonzero = int(np.sum(deltas != 0))
            n_pos = int(np.sum(deltas > 0))
            n_neg = int(np.sum(deltas < 0))
            median = float(np.median(deltas)) if n_total else float("nan")
            mean = float(np.mean(deltas)) if n_total else float("nan")
            stat: float
            pval: float
            if n_nonzero >= 1:
                try:
                    result = stats.wilcoxon(
                        deltas,
                        zero_method="wilcox",
                        alternative="two-sided",
                        nan_policy="omit",
                    )
                    stat = float(result.statistic)
                    pval = float(result.pvalue)
                except ValueError:
                    stat, pval = float("nan"), float("nan")
            else:
                stat, pval = float("nan"), float("nan")
            per_metric.append(
                {
                    "metric": metric_label,
                    "metric_key": metric_key,
                    "condition": CONDITION_LABELS_FLAT[condition],
                    "condition_key": condition,
                    "n_pairs": n_total,
                    "n_nonzero": n_nonzero,
                    "n_positive": n_pos,
                    "n_negative": n_neg,
                    "median_delta": median,
                    "mean_delta": mean,
                    "wilcoxon_W": stat,
                    "p_value": pval,
                }
            )
        pvals = np.array([r["p_value"] for r in per_metric], dtype=float)
        valid_mask = ~np.isnan(pvals)
        adj = np.full(len(pvals), np.nan)
        if valid_mask.any():
            adj[valid_mask] = holm(pvals[valid_mask])
        for r, p_adj in zip(per_metric, adj, strict=True):
            r["p_value_holm"] = float(p_adj) if not np.isnan(p_adj) else float("nan")
            r["significant_05_holm"] = (
                bool(p_adj < 0.05) if not np.isnan(p_adj) else False
            )
        rows.extend(per_metric)
    return pd.DataFrame(rows)


def fmt_value(value: object, column: str) -> str:
    if isinstance(value, float):
        if np.isnan(value):
            return "nan"
        if column in {"p_value", "p_value_holm"}:
            return f"{value:.4g}"
        if column in {"median_delta", "mean_delta"}:
            if abs(value) >= 1000 or value == 0:
                return f"{value:.1f}"
            return f"{value:.4f}"
        if column == "wilcoxon_W":
            return f"{value:.1f}"
        return f"{value:.4f}"
    return str(value)


def to_markdown(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join("---" for _ in cols) + " |",
    ]
    for row in df.to_dict(orient="records"):
        values = [fmt_value(row[c], c).replace("|", "\\|") for c in cols]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def plot_summary(results: pd.DataFrame, out_path: Path) -> None:
    """Six-panel grid: one bar chart per metric, four bars (conditions) each.

    Bar height = median delta (mean for count metrics where median is 0 to
    avoid uninformative flat bars). Color encodes direction; star annotation
    encodes Holm-adjusted significance.
    """
    fig, axes = plt.subplots(2, 3, figsize=(13.5, 7.5))
    axes = axes.flatten()
    bar_x = np.arange(len(CONDITIONS))
    tick_labels = [CONDITION_LABELS[c] for c in CONDITIONS]

    for ax, (metric_key, metric_label, unit) in zip(axes, METRICS, strict=True):
        sub = results[results["metric_key"] == metric_key].set_index("condition_key")
        sub = sub.reindex(CONDITIONS)

        use_mean = bool((sub["median_delta"].abs() < 1e-12).all())
        values = (sub["mean_delta"] if use_mean else sub["median_delta"]).astype(float).to_numpy()
        if metric_key == "token_delta_pct":
            values = values * 100  # show as percent

        colors = []
        for value, sig in zip(values, sub["significant_05_holm"], strict=True):
            if not sig:
                colors.append("#BBBBBB")
            elif value >= 0:
                colors.append("#D62728")
            else:
                colors.append("#1F77B4")

        bars = ax.bar(bar_x, values, color=colors, edgecolor="#333333", linewidth=0.6)
        ax.axhline(0, color="#333333", linewidth=0.8)

        y_min = min(values.min(), 0)
        y_max = max(values.max(), 0)
        span = y_max - y_min if y_max > y_min else max(abs(y_max), 1.0)
        pad = span * 0.18
        ax.set_ylim(y_min - pad, y_max + pad * 1.6)

        for bar, value, p_adj, n_nonzero in zip(
            bars,
            values,
            sub["p_value_holm"].astype(float),
            sub["n_nonzero"].astype(int),
            strict=True,
        ):
            label = stars(p_adj)
            if not label:
                label = "—"
            anchor = bar.get_height()
            offset = pad * 0.25
            if anchor >= 0:
                y = anchor + offset
                va = "bottom"
            else:
                y = anchor - offset
                va = "top"
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                y,
                label,
                ha="center",
                va=va,
                fontsize=10,
                fontweight="bold" if label not in {"ns", "—"} else "normal",
                color="#222222",
            )

        ax.set_xticks(bar_x, tick_labels, fontsize=9)
        suffix = " (mean)" if use_mean else " (median)"
        unit_label = "% of clean" if metric_key == "token_delta_pct" else unit
        ax.set_ylabel(f"Δ vs clean ({unit_label}){suffix}", fontsize=9)
        ax.set_title(metric_label, fontsize=10, fontweight="bold")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(axis="y", color="#E0E0E0", linewidth=0.7)
        ax.set_axisbelow(True)

    legend_elements = [
        plt.Rectangle((0, 0), 1, 1, color="#D62728", label="Sig. ↑ (Holm p<0.05)"),
        plt.Rectangle((0, 0), 1, 1, color="#1F77B4", label="Sig. ↓ (Holm p<0.05)"),
        plt.Rectangle((0, 0), 1, 1, color="#BBBBBB", label="Not significant"),
    ]
    fig.legend(
        handles=legend_elements,
        loc="lower center",
        ncol=3,
        frameon=False,
        bbox_to_anchor=(0.5, -0.02),
        fontsize=10,
    )
    fig.suptitle(
        "Wilcoxon signed-rank: paired clean-vs-degraded deltas (combined backends)\n"
        "Stars: *** p<0.001, ** p<0.01, * p<0.05; ns = not significant; — = test undefined",
        fontsize=11,
        y=0.995,
    )
    plt.tight_layout(rect=[0, 0.03, 1, 0.96])
    for suffix in ("png", "pdf"):
        fig.savefig(out_path.with_suffix(f".{suffix}"), dpi=220, bbox_inches="tight")
    plt.close(fig)


def write_stats_report(results: pd.DataFrame, total_pairs: int) -> None:
    sig = results[results["significant_05_holm"]].sort_values(
        ["metric", "p_value_holm"]
    )
    full = results[
        [
            "metric",
            "condition",
            "n_pairs",
            "n_nonzero",
            "n_positive",
            "n_negative",
            "median_delta",
            "wilcoxon_W",
            "p_value",
            "p_value_holm",
        ]
    ]
    sig_table_md = (
        to_markdown(
            sig[
                [
                    "metric",
                    "condition",
                    "n_pairs",
                    "n_nonzero",
                    "median_delta",
                    "p_value",
                    "p_value_holm",
                ]
            ]
        )
        if not sig.empty
        else "_None._\n"
    )

    report = f"""# Signed-Rank Test Results

Wilcoxon signed-rank tests on the paired clean-vs-degraded deltas in
`../data/combined_paired_matrix.csv`. Each test is two-sided with
`H0: median(delta) = 0`. Zero-valued pairs are dropped by `scipy.stats.wilcoxon`
(default `zero_method="wilcox"`). Holm-Bonferroni adjustment is applied within
each metric family (the four conditions tested for that metric).

See `signed_rank_tests.png` for the summary figure.

## Method

- Source: combined paired matrix ({total_pairs} pairs across both backends).
- Test: `scipy.stats.wilcoxon`, two-sided, default zero handling.
- Multiple-comparison correction: Holm step-down within each metric family.
- Significance threshold: Holm-adjusted p < 0.05.

## Significant Effects (Holm p < 0.05)

{sig_table_md}
## Full Results

{to_markdown(full)}
## Notes

- Sign of `median_delta` is informative: positive means the degraded run had a larger value than clean.
- For count metrics with many ties at zero (`hidden_bug_fix_failed_delta`, `regression_failed_delta`), `n_nonzero` is much smaller than `n_pairs`. The summary figure falls back to mean delta when median is exactly 0 so the bars are not flat. Treat marginal p-values cautiously.
- Tests are pooled across both backends. Per-backend and per-repo splits are intentionally out of scope here.
- These are paired marginal tests, not a multi-factor model: they tell you whether each degradation shifts a metric on average, not how degradations interact.
- `token_delta_pct` is per-pair (degraded - clean) / clean; rows where clean == 0 are dropped, so `n_pairs` may be smaller than for `token_delta`.
"""
    (HERE / "STATS.md").write_text(report, encoding="utf-8")


def main() -> None:
    df = pd.read_csv(DATA / "combined_paired_matrix.csv")
    results = run_tests(df)

    results.to_csv(HERE / "signed_rank_tests.csv", index=False)
    (HERE / "signed_rank_tests.md").write_text(to_markdown(results), encoding="utf-8")
    write_stats_report(results, total_pairs=len(df))
    plot_summary(results, HERE / "signed_rank_tests.png")

    print(f"Wrote {HERE / 'signed_rank_tests.csv'}")
    print(f"Wrote {HERE / 'signed_rank_tests.md'}")
    print(f"Wrote {HERE / 'STATS.md'}")
    print(f"Wrote {HERE / 'signed_rank_tests.png'}")


if __name__ == "__main__":
    main()
