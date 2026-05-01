#!/usr/bin/env python3
"""RQ2: cross-correlation between bootstrap and execution phase deltas.

Computes Spearman (rank-based, primary) and Pearson (linear, secondary)
correlations for every (bootstrap_delta, execution_delta) pair on the
SWE-bench paired comparison matrix. Outputs CSVs, a markdown narrative,
and a heatmap PNG.

Phase definitions (from LLM-J/docs/experimental_pipeline.md Stage 6):
- Bootstrap = events before the first meaningful code edit.
- Execution = events from the first edit onward.

Only the SWE-bench backend exposes the phase split. LLM-J runs are excluded
because the enriched matrix does not carry bootstrap_*/execution_* columns.

All outputs land in this script's own directory.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = (
    ROOT
    / "swebench-agent-readiness"
    / "final_analysis"
    / "data"
    / "rq2_phase_delta_matrix.csv"
)

BOOTSTRAP_METRICS = [
    ("bootstrap_event_count_delta", "Bootstrap events"),
    ("bootstrap_command_count_delta", "Bootstrap commands"),
    ("bootstrap_failed_command_count_delta", "Bootstrap failed cmds"),
    ("bootstrap_test_command_count_delta", "Bootstrap test cmds"),
    ("bootstrap_failed_test_command_count_delta", "Bootstrap failed test cmds"),
]
EXECUTION_METRICS = [
    ("execution_event_count_delta", "Execution events"),
    ("execution_command_count_delta", "Execution commands"),
    ("execution_failed_command_count_delta", "Execution failed cmds"),
    ("execution_test_command_count_delta", "Execution test cmds"),
    ("execution_failed_test_command_count_delta", "Execution failed test cmds"),
]

# Conditions are degradation types. Order is fixed for stable column ordering.
CONDITIONS = [
    ("naming", "Naming"),
    ("type_hints", "Type hints"),
    ("comments_docstrings", "Comments/\ndocstrings"),
    ("remove_tests", "Remove\ntests"),
]

# Effect-size heatmap stacks bootstrap rows on top of execution rows.
EFFECT_SIZE_METRICS = [
    *[(k, label, "bootstrap") for k, label in BOOTSTRAP_METRICS],
    *[(k, label, "execution") for k, label in EXECUTION_METRICS],
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
    return ""


def correlate(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for x_key, x_label in BOOTSTRAP_METRICS:
        for y_key, y_label in EXECUTION_METRICS:
            pair = df[[x_key, y_key]].dropna()
            n = len(pair)
            if n < 3:
                rows.append(
                    {
                        "bootstrap_metric": x_label,
                        "execution_metric": y_label,
                        "bootstrap_key": x_key,
                        "execution_key": y_key,
                        "n": n,
                        "spearman_rho": float("nan"),
                        "spearman_p": float("nan"),
                        "pearson_r": float("nan"),
                        "pearson_p": float("nan"),
                    }
                )
                continue
            x = pair[x_key].to_numpy(dtype=float)
            y = pair[y_key].to_numpy(dtype=float)
            try:
                sp = stats.spearmanr(x, y)
                spearman_rho, spearman_p = float(sp.statistic), float(sp.pvalue)
            except Exception:
                spearman_rho, spearman_p = float("nan"), float("nan")
            try:
                pr = stats.pearsonr(x, y)
                pearson_r, pearson_p = float(pr.statistic), float(pr.pvalue)
            except Exception:
                pearson_r, pearson_p = float("nan"), float("nan")
            rows.append(
                {
                    "bootstrap_metric": x_label,
                    "execution_metric": y_label,
                    "bootstrap_key": x_key,
                    "execution_key": y_key,
                    "n": n,
                    "spearman_rho": spearman_rho,
                    "spearman_p": spearman_p,
                    "pearson_r": pearson_r,
                    "pearson_p": pearson_p,
                }
            )
    out = pd.DataFrame(rows)
    for p_col, adj_col in [
        ("spearman_p", "spearman_p_holm"),
        ("pearson_p", "pearson_p_holm"),
    ]:
        pvals = out[p_col].to_numpy(dtype=float)
        valid = ~np.isnan(pvals)
        adj = np.full(len(pvals), np.nan)
        if valid.any():
            adj[valid] = holm(pvals[valid])
        out[adj_col] = adj
    return out


def fmt(value: object, column: str) -> str:
    if isinstance(value, float):
        if np.isnan(value):
            return "nan"
        if column.endswith("_p") or column.endswith("_p_holm"):
            return f"{value:.4g}"
        if column in {"spearman_rho", "pearson_r"}:
            return f"{value:.3f}"
        return f"{value:.4f}"
    return str(value)


def to_markdown(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join("---" for _ in cols) + " |",
    ]
    for row in df.to_dict(orient="records"):
        values = [fmt(row[c], c).replace("|", "\\|") for c in cols]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def plot_heatmap(df: pd.DataFrame, out_path: Path) -> None:
    """Two-panel heatmap: Spearman (left) and Pearson (right)."""
    boot_labels = [label for _, label in BOOTSTRAP_METRICS]
    exec_labels = [label for _, label in EXECUTION_METRICS]

    def grid_for(value_col: str, p_col: str) -> tuple[np.ndarray, np.ndarray]:
        values = np.full((len(boot_labels), len(exec_labels)), np.nan)
        pvals = np.full_like(values, np.nan)
        for i, (b_key, _) in enumerate(BOOTSTRAP_METRICS):
            for j, (e_key, _) in enumerate(EXECUTION_METRICS):
                row = df[
                    (df["bootstrap_key"] == b_key) & (df["execution_key"] == e_key)
                ].iloc[0]
                values[i, j] = float(row[value_col])
                pvals[i, j] = float(row[p_col])
        return values, pvals

    spearman_vals, spearman_p = grid_for("spearman_rho", "spearman_p_holm")
    pearson_vals, pearson_p = grid_for("pearson_r", "pearson_p_holm")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.4))

    for ax, vals, pvals, title in zip(
        axes,
        [spearman_vals, pearson_vals],
        [spearman_p, pearson_p],
        ["Spearman ρ (rank-based)", "Pearson r (linear)"],
        strict=True,
    ):
        im = ax.imshow(vals, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
        ax.set_xticks(np.arange(len(exec_labels)), exec_labels, rotation=30, ha="right", fontsize=9)
        ax.set_yticks(np.arange(len(boot_labels)), boot_labels, fontsize=9)
        ax.set_xlabel("Execution-phase delta", fontsize=10)
        ax.set_ylabel("Bootstrap-phase delta", fontsize=10)
        ax.set_title(title, fontsize=11, fontweight="bold")

        for i in range(vals.shape[0]):
            for j in range(vals.shape[1]):
                v = vals[i, j]
                if np.isnan(v):
                    continue
                star = stars(pvals[i, j])
                text_color = "white" if abs(v) > 0.55 else "#1a1a1a"
                ax.text(
                    j,
                    i,
                    f"{v:.2f}{star}",
                    ha="center",
                    va="center",
                    fontsize=8.5,
                    color=text_color,
                )

        cbar = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.04)
        cbar.set_label("Correlation", fontsize=9)
        cbar.ax.tick_params(labelsize=8)

    n_used = int(df["n"].max())
    fig.suptitle(
        f"RQ2: Bootstrap × Execution delta correlations (SWE-bench paired comparisons, n≤{n_used})\n"
        f"Stars use Holm-adjusted p-values: *** p<0.001, ** p<0.01, * p<0.05",
        fontsize=11,
        y=1.02,
    )
    plt.tight_layout()
    for suffix in ("png", "pdf"):
        fig.savefig(out_path.with_suffix(f".{suffix}"), dpi=220, bbox_inches="tight")
    plt.close(fig)


def rank_biserial(deltas: np.ndarray) -> tuple[float, float, int]:
    """Paired rank-biserial correlation from Wilcoxon signed-rank.

    Returns (r_rb, p_value, n_nonzero). Bounded [-1, +1]:
    +1 means every nonzero pair moved in the positive direction,
    -1 means every nonzero pair moved negative, 0 means balanced.
    """
    nonzero = deltas[deltas != 0]
    n_nonzero = int(len(nonzero))
    if n_nonzero < 1:
        return float("nan"), float("nan"), n_nonzero
    abs_ranks = stats.rankdata(np.abs(nonzero))
    signs = np.sign(nonzero)
    w_plus = float(np.sum(abs_ranks[signs > 0]))
    w_minus = float(np.sum(abs_ranks[signs < 0]))
    total = w_plus + w_minus
    r_rb = (w_plus - w_minus) / total if total > 0 else float("nan")
    try:
        result = stats.wilcoxon(
            deltas, zero_method="wilcox", alternative="two-sided", nan_policy="omit"
        )
        p = float(result.pvalue)
    except ValueError:
        p = float("nan")
    return r_rb, p, n_nonzero


def effect_sizes_by_condition(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for metric_key, metric_label, phase in EFFECT_SIZE_METRICS:
        for cond_key, cond_label in CONDITIONS:
            sub = df[df["condition"] == cond_key]
            deltas = pd.to_numeric(sub[metric_key], errors="coerce").dropna().to_numpy()
            r_rb, pval, n_nonzero = rank_biserial(deltas)
            rows.append(
                {
                    "phase": phase,
                    "metric": metric_label,
                    "metric_key": metric_key,
                    "condition": cond_label.replace("\n", " "),
                    "condition_key": cond_key,
                    "n_pairs": int(len(deltas)),
                    "n_nonzero": n_nonzero,
                    "rank_biserial_r": r_rb,
                    "p_value": pval,
                }
            )
    out = pd.DataFrame(rows)
    pvals = out["p_value"].to_numpy(dtype=float)
    valid = ~np.isnan(pvals)
    adj = np.full(len(pvals), np.nan)
    if valid.any():
        adj[valid] = holm(pvals[valid])
    out["p_value_holm"] = adj
    return out


def plot_effect_size_heatmap(df: pd.DataFrame, out_path: Path) -> None:
    metric_keys = [k for k, _, _ in EFFECT_SIZE_METRICS]
    metric_labels = [label for _, label, _ in EFFECT_SIZE_METRICS]
    metric_phases = [phase for _, _, phase in EFFECT_SIZE_METRICS]
    cond_keys = [k for k, _ in CONDITIONS]
    cond_labels = [label for _, label in CONDITIONS]

    values = np.full((len(metric_keys), len(cond_keys)), np.nan)
    pvals = np.full_like(values, np.nan)
    for i, m_key in enumerate(metric_keys):
        for j, c_key in enumerate(cond_keys):
            row = df[(df["metric_key"] == m_key) & (df["condition_key"] == c_key)].iloc[0]
            values[i, j] = float(row["rank_biserial_r"])
            pvals[i, j] = float(row["p_value_holm"])

    fig, ax = plt.subplots(figsize=(8.4, 7.0))
    im = ax.imshow(values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(np.arange(len(cond_labels)), cond_labels, fontsize=10)
    ax.set_yticks(np.arange(len(metric_labels)), metric_labels, fontsize=10)
    ax.set_xlabel("Degradation", fontsize=11)

    # Phase divider between bootstrap and execution rows.
    boundary = next(i for i, p in enumerate(metric_phases) if p == "execution") - 0.5
    ax.axhline(boundary, color="#222222", linewidth=2.0)

    # Phase labels on the right edge.
    ax.text(
        len(cond_labels) - 0.4,
        boundary / 2,
        "Bootstrap",
        rotation=270,
        va="center",
        ha="left",
        fontsize=10,
        fontweight="bold",
        color="#444444",
    )
    ax.text(
        len(cond_labels) - 0.4,
        (boundary + len(metric_keys)) / 2,
        "Execution",
        rotation=270,
        va="center",
        ha="left",
        fontsize=10,
        fontweight="bold",
        color="#444444",
    )

    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            v = values[i, j]
            if np.isnan(v):
                continue
            star = stars(pvals[i, j])
            text_color = "white" if abs(v) > 0.55 else "#1a1a1a"
            ax.text(
                j,
                i,
                f"{v:+.2f}{star}",
                ha="center",
                va="center",
                fontsize=9,
                color=text_color,
            )

    cbar = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.06)
    cbar.set_label("Rank-biserial r (paired effect size)", fontsize=10)
    cbar.ax.tick_params(labelsize=9)

    ax.set_title(
        "RQ2 effect size: each degradation × each phase metric\n"
        "Rank-biserial r from paired Wilcoxon (SWE-bench, 30–34 pairs/cond)\n"
        "Stars: Holm-adjusted *** p<0.001, ** p<0.01, * p<0.05",
        fontsize=11,
        fontweight="bold",
        pad=12,
    )
    plt.tight_layout()
    for suffix in ("png", "pdf"):
        fig.savefig(out_path.with_suffix(f".{suffix}"), dpi=220, bbox_inches="tight")
    plt.close(fig)


def write_report(df: pd.DataFrame, n_pairs: int) -> None:
    sig_spearman = df[df["spearman_p_holm"] < 0.05].sort_values("spearman_p_holm")
    sig_table = (
        to_markdown(
            sig_spearman[
                [
                    "bootstrap_metric",
                    "execution_metric",
                    "n",
                    "spearman_rho",
                    "spearman_p",
                    "spearman_p_holm",
                ]
            ]
        )
        if not sig_spearman.empty
        else "_None._\n"
    )
    full = df[
        [
            "bootstrap_metric",
            "execution_metric",
            "n",
            "spearman_rho",
            "spearman_p",
            "spearman_p_holm",
            "pearson_r",
            "pearson_p",
            "pearson_p_holm",
        ]
    ]

    report = f"""# RQ2: Bootstrap × Execution Correlation

This folder tests whether bootstrap-phase deltas (orientation) covary with
execution-phase deltas (task completion) on the same paired clean-vs-degraded
SWE-bench runs.

See `rq2_correlation_heatmap.png` for the summary figure.

## Scope

- **Source:** `swebench-agent-readiness/final_analysis/data/rq2_phase_delta_matrix.csv`
- **Unit of analysis:** paired comparison (clean vs. degraded) — {n_pairs} pairs.
- **Backend:** SWE-bench only. The LLM-J enriched matrix does not expose `bootstrap_*` / `execution_*` columns, so this analysis cannot be pooled across both backends.
- **Bootstrap metrics tested:** event count, command count, failed commands, test commands, failed test commands (all `_delta` versions).
- **Execution metrics tested:** same five families on the post-first-edit phase.

## Method

- **Spearman rank correlation** as the headline. It is robust to count-data skew and to a few high-leverage runs.
- **Pearson** reported alongside as a linearity sanity check.
- **Holm-Bonferroni** correction applied across the full 5×5 = 25-cell grid for each correlation type independently.
- Significance threshold for highlighting: Holm-adjusted p < 0.05.

## Significant Spearman Correlations (Holm p < 0.05)

{sig_table}
## Full Results

{to_markdown(full)}
## Reading the heatmap

- Cell shows Spearman ρ (left panel) or Pearson r (right panel).
- Color: red = positive, blue = negative, white = near zero.
- Stars use **Holm-adjusted** p, not raw p. A cell can have ρ ≈ 0.2 and still fail to reach significance after correction.

## Caveats

- A correlation between two deltas means: **when degradation perturbs bootstrap, it tends to perturb execution in the same (or opposite) direction.** It does *not* prove that bootstrap behavior causes execution behavior — both could share an upstream cause (the degradation itself, or task difficulty).
- Same-row "x event count" vs. "y event count" correlations are mechanically related: both phases of a longer-than-clean run will tend to be longer in absolute terms. The interesting cells are off-diagonal — e.g., does extra bootstrap *failed-command* activity predict more execution test failures?
- This is paired delta analysis, so repo and task identity are partialled out *within the paired structure*. Cross-task variation still drives a lot of the spread.
- LLM-J is omitted by data availability, not by design. Re-running this analysis after enriching the LLM-J matrix with phase-split metrics would let it pool across both backends.
"""
    (HERE / "RQ2_CORRELATION.md").write_text(report, encoding="utf-8")


def main() -> None:
    df = pd.read_csv(SOURCE)
    results = correlate(df)
    results.to_csv(HERE / "rq2_correlation.csv", index=False)
    (HERE / "rq2_correlation.md").write_text(to_markdown(results), encoding="utf-8")
    write_report(results, n_pairs=len(df))
    plot_heatmap(results, HERE / "rq2_correlation_heatmap.png")

    effects = effect_sizes_by_condition(df)
    effects.to_csv(HERE / "rq2_effect_size.csv", index=False)
    (HERE / "rq2_effect_size.md").write_text(to_markdown(effects), encoding="utf-8")
    plot_effect_size_heatmap(effects, HERE / "rq2_effect_size_heatmap.png")

    print(f"Wrote {HERE / 'rq2_correlation.csv'}")
    print(f"Wrote {HERE / 'rq2_correlation.md'}")
    print(f"Wrote {HERE / 'RQ2_CORRELATION.md'}")
    print(f"Wrote {HERE / 'rq2_correlation_heatmap.png'}")
    print(f"Wrote {HERE / 'rq2_effect_size.csv'}")
    print(f"Wrote {HERE / 'rq2_effect_size.md'}")
    print(f"Wrote {HERE / 'rq2_effect_size_heatmap.png'}")


if __name__ == "__main__":
    main()
