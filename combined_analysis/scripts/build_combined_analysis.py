#!/usr/bin/env python3
"""Build the small cross-backend analysis bundle.

The two backend studies have different raw shapes:

- LLM-J custom-repo exports one row per run, including the clean condition.
- SWE-bench exports paired clean-vs-degraded rows.

The common unit for the combined analysis is therefore the paired comparison:
one task, one degradation, and the matched clean outcome.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "combined_analysis"
DATA = OUT / "data"
TABLES = OUT / "tables"
FIGURES = OUT / "figures"

LLMJ_DIR = ROOT / "LLM-J/final_rq_analysis"
LLMJ_MATRIX = LLMJ_DIR / "data/enriched_matrix_with_process_metrics.csv"

SWEBENCH_DIR = ROOT / "swebench-agent-readiness/final_analysis"
SWEBENCH_MATRIX = SWEBENCH_DIR / "data/rq1_enriched_analysis_matrix.csv"

CONDITIONS = ["naming", "type_hints", "comments_docstrings", "remove_tests"]
CONDITION_LABELS = {
    "naming": "Naming",
    "type_hints": "Type hints",
    "comments_docstrings": "Comments/docstrings",
    "remove_tests": "Remove tests",
}
BACKEND_LABELS = {
    "custom_repo": "Custom repos",
    "swebench": "SWE-bench",
    "combined": "Combined",
}
COMPLETE_SWEBENCH_REPOS = {
    "astropy/astropy",
    "django/django",
    "matplotlib/matplotlib",
    "psf/requests",
    "pydata/xarray",
    "pylint-dev/pylint",
    "pytest-dev/pytest",
    "scikit-learn/scikit-learn",
    "sphinx-doc/sphinx",
    "sympy/sympy",
}

COLORS = {
    "custom_repo": "#4C78A8",
    "swebench": "#F28E2B",
    "combined": "#59A14F",
    "clean": "#B8B8B8",
    "degraded": "#D62728",
}


def ensure_clean_dirs() -> None:
    for directory in [DATA, TABLES, FIGURES]:
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir(parents=True, exist_ok=True)


def bool_series(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series
    return series.astype(str).str.lower().isin({"true", "1", "yes"})


def custom_pairs() -> pd.DataFrame:
    df = pd.read_csv(LLMJ_MATRIX)
    df["success"] = df["status"].eq("SUCCESS")
    clean = df[df["condition"] == "clean"].copy()
    degraded = df[df["condition"].isin(CONDITIONS)].copy()
    merged = degraded.merge(
        clean,
        on=["repo", "candidate_id"],
        suffixes=("_degraded", "_clean"),
        validate="many_to_one",
    )
    rows: list[dict[str, object]] = []
    for row in merged.to_dict(orient="records"):
        rows.append(
            {
                "backend": "custom_repo",
                "backend_label": BACKEND_LABELS["custom_repo"],
                "repo": row["repo_full_clean"],
                "task_id": row["candidate_id"],
                "condition": row["condition_degraded"],
                "replication_index": 1,
                "condition_label": CONDITION_LABELS[row["condition_degraded"]],
                "clean_success": bool(row["success_clean"]),
                "degraded_success": bool(row["success_degraded"]),
                "clean_hidden_bug_fix_failed": int(row["fail_to_pass_failed_clean"]),
                "degraded_hidden_bug_fix_failed": int(row["fail_to_pass_failed_degraded"]),
                "hidden_bug_fix_failed_delta": int(row["fail_to_pass_failed_degraded"])
                - int(row["fail_to_pass_failed_clean"]),
                "clean_regression_failed": int(row["pass_to_pass_failed_clean"]),
                "degraded_regression_failed": int(row["pass_to_pass_failed_degraded"]),
                "regression_failed_delta": int(row["pass_to_pass_failed_degraded"])
                - int(row["pass_to_pass_failed_clean"]),
                "clean_tokens_corrected": float(row["uncached_input_plus_output_tokens_clean"]),
                "degraded_tokens_corrected": float(row["uncached_input_plus_output_tokens_degraded"]),
                "token_delta": float(row["uncached_input_plus_output_tokens_degraded"])
                - float(row["uncached_input_plus_output_tokens_clean"]),
                "token_definition": "input_plus_output_tokens_excludes_cached_input",
                "total_token_delta_including_cache": float(row["total_tokens_including_cache_degraded"])
                - float(row["total_tokens_including_cache_clean"]),
                "runtime_delta_seconds": float(row["total_duration_seconds_degraded"])
                - float(row["total_duration_seconds_clean"]),
                "changed_file_delta": np.nan,
                "files_opened_delta": float(row["files_opened_before_first_edit_degraded"])
                - float(row["files_opened_before_first_edit_clean"]),
                "exploration_efficiency_delta": float(row["exploration_efficiency_degraded"])
                - float(row["exploration_efficiency_clean"]),
                "validation_command_delta": float(row["validation_test_command_count_degraded"])
                - float(row["validation_test_command_count_clean"]),
                "failed_validation_command_delta": float(row["failed_validation_test_command_count_degraded"])
                - float(row["failed_validation_test_command_count_clean"]),
            }
        )
    return pd.DataFrame(rows)


def swebench_pairs() -> pd.DataFrame:
    df = pd.read_csv(SWEBENCH_MATRIX)
    df = df[df["repo"].isin(COMPLETE_SWEBENCH_REPOS)].copy()
    df = df[df["condition"].isin(CONDITIONS)].copy()
    rows: list[dict[str, object]] = []
    for row in df.to_dict(orient="records"):
        rows.append(
            {
                "backend": "swebench",
                "backend_label": BACKEND_LABELS["swebench"],
                "repo": row["repo"],
                "task_id": row["instance_id"],
                "condition": row["condition"],
                "replication_index": int(row["replication_index"]),
                "condition_label": CONDITION_LABELS[row["condition"]],
                "clean_success": bool(row["clean_success"]),
                "degraded_success": bool(row["degraded_success"]),
                "clean_hidden_bug_fix_failed": int(row["clean_fail_to_pass_failed_count"]),
                "degraded_hidden_bug_fix_failed": int(row["degraded_fail_to_pass_failed_count"]),
                "hidden_bug_fix_failed_delta": int(row["fail_to_pass_failed_count_delta"]),
                "clean_regression_failed": int(row["clean_pass_to_pass_failed_count"]),
                "degraded_regression_failed": int(row["degraded_pass_to_pass_failed_count"]),
                "regression_failed_delta": int(row["pass_to_pass_failed_count_delta"]),
                "clean_tokens_corrected": float(row["clean_total_tokens_corrected"]),
                "degraded_tokens_corrected": float(row["degraded_total_tokens_corrected"]),
                "token_delta": float(row["total_tokens_corrected_delta"]),
                "token_definition": "input_plus_output_tokens_excludes_cached_input",
                "total_token_delta_including_cache": np.nan,
                "runtime_delta_seconds": np.nan,
                "changed_file_delta": float(row["changed_file_count_delta"]),
                "files_opened_delta": float(row["files_opened_before_first_edit_delta"]),
                "exploration_efficiency_delta": float(row["exploration_efficiency_delta"]),
                "validation_command_delta": np.nan,
                "failed_validation_command_delta": np.nan,
            }
        )
    return pd.DataFrame(rows)


def add_pair_flags(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["clean_success"] = bool_series(result["clean_success"])
    result["degraded_success"] = bool_series(result["degraded_success"])
    result["both_success"] = result["clean_success"] & result["degraded_success"]
    result["clean_success_degraded_failure"] = result["clean_success"] & ~result["degraded_success"]
    result["clean_failure_degraded_success"] = ~result["clean_success"] & result["degraded_success"]
    result["both_fail"] = ~result["clean_success"] & ~result["degraded_success"]
    result["baseline_hard"] = ~result["clean_success"]
    result["regression_damage"] = result["regression_failed_delta"] > 0
    result["hidden_bug_fix_damage"] = result["hidden_bug_fix_failed_delta"] > 0
    result["token_delta_pct"] = np.where(
        result["clean_tokens_corrected"] > 0,
        result["token_delta"] / result["clean_tokens_corrected"],
        np.nan,
    )
    result["token_higher"] = result["token_delta"] > 0
    return result


def summarize_backend(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for backend, group in df.groupby("backend", sort=False):
        rows.append(
            {
                "backend": BACKEND_LABELS[backend],
                "repos": group["repo"].nunique(),
                "tasks": group["task_id"].nunique(),
                "paired_comparisons": len(group),
                "clean_success_to_degraded_failure": int(group["clean_success_degraded_failure"].sum()),
                "conditions": ", ".join(CONDITION_LABELS[c] for c in CONDITIONS),
                "notes": (
                    "150 individual scored runs in the source matrix."
                    if backend == "custom_repo"
                    else "10 fully complete SWE-bench repos; Flask provenance rows excluded from this combined slice."
                ),
            }
        )
    rows.append(
        {
            "backend": "Combined",
            "repos": df[["backend", "repo"]].drop_duplicates().shape[0],
            "tasks": df[["backend", "task_id"]].drop_duplicates().shape[0],
            "paired_comparisons": len(df),
            "clean_success_to_degraded_failure": int(df["clean_success_degraded_failure"].sum()),
            "conditions": ", ".join(CONDITION_LABELS[c] for c in CONDITIONS),
            "notes": "Use paired comparisons for cross-backend RQ1 because the raw backend matrices differ.",
        }
    )
    return pd.DataFrame(rows)


def condition_summary(df: pd.DataFrame, by_backend: bool) -> pd.DataFrame:
    group_cols = ["backend", "condition"] if by_backend else ["condition"]
    rows = []
    for keys, group in df.groupby(group_cols, sort=False):
        if by_backend:
            backend, condition = keys
        else:
            condition = keys[0] if isinstance(keys, tuple) else keys
            backend = "combined"
        clean_successes = int(group["clean_success"].sum())
        degraded_successes = int(group["degraded_success"].sum())
        n = len(group)
        record: dict[str, object] = {
            "backend": BACKEND_LABELS[backend],
            "condition": CONDITION_LABELS[condition],
            "paired_comparisons": n,
            "clean_success": clean_successes,
            "degraded_success": degraded_successes,
            "clean_success_rate": round(clean_successes / n, 4),
            "degraded_success_rate": round(degraded_successes / n, 4),
            "success_rate_delta_degraded_minus_clean": round((degraded_successes - clean_successes) / n, 4),
            "clean_success_to_degraded_failure": int(group["clean_success_degraded_failure"].sum()),
            "clean_failure_to_degraded_success": int(group["clean_failure_degraded_success"].sum()),
            "baseline_hard_pairs": int(group["baseline_hard"].sum()),
            "hidden_bug_fix_failed_delta_sum": int(group["hidden_bug_fix_failed_delta"].sum()),
            "regression_failed_delta_sum": int(group["regression_failed_delta"].sum()),
            "regression_damage_pairs": int(group["regression_damage"].sum()),
        }
        if by_backend:
            record["mean_token_delta"] = round(float(group["token_delta"].mean()), 1)
            record["median_token_delta"] = round(float(group["token_delta"].median()), 1)
            record["token_delta_definition"] = str(group["token_definition"].iloc[0])
        rows.append(record)
    order = {label: index for index, label in enumerate(CONDITION_LABELS.values())}
    out = pd.DataFrame(rows)
    out["_order"] = out["condition"].map(order)
    sort_cols = ["backend", "_order"] if by_backend else ["_order"]
    return out.sort_values(sort_cols).drop(columns="_order").reset_index(drop=True)


def repo_backend_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (backend, repo), group in df.groupby(["backend", "repo"], sort=False):
        rows.append(
            {
                "backend": BACKEND_LABELS[backend],
                "repo": repo,
                "tasks": group["task_id"].nunique(),
                "paired_comparisons": len(group),
                "clean_success_to_degraded_failure": int(group["clean_success_degraded_failure"].sum()),
                "regression_damage_pairs": int(group["regression_damage"].sum()),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["backend", "clean_success_to_degraded_failure", "regression_damage_pairs", "repo"],
        ascending=[True, False, False, True],
    )


def metric_summary(df: pd.DataFrame, by_backend: bool) -> pd.DataFrame:
    group_cols = ["backend", "condition"] if by_backend else ["condition"]
    rows = []
    for keys, group in df.groupby(group_cols, sort=False):
        if by_backend:
            backend, condition = keys
        else:
            condition = keys[0] if isinstance(keys, tuple) else keys
            backend = "combined"
        record: dict[str, object] = {
            "backend": BACKEND_LABELS[backend],
            "condition": CONDITION_LABELS[condition],
            "paired_comparisons": len(group),
            "mean_corrected_token_delta": round(float(group["token_delta"].mean()), 1),
            "median_corrected_token_delta": round(float(group["token_delta"].median()), 1),
            "mean_corrected_token_delta_pct": round(float(group["token_delta_pct"].mean()), 4),
            "median_corrected_token_delta_pct": round(float(group["token_delta_pct"].median()), 4),
            "token_higher_pairs": int(group["token_higher"].sum()),
            "mean_files_opened_delta": round(float(group["files_opened_delta"].mean()), 3),
            "median_files_opened_delta": round(float(group["files_opened_delta"].median()), 3),
            "mean_exploration_efficiency_delta": round(float(group["exploration_efficiency_delta"].mean()), 4),
            "median_exploration_efficiency_delta": round(float(group["exploration_efficiency_delta"].median()), 4),
        }
        if by_backend:
            record["mean_runtime_delta_seconds"] = (
                round(float(group["runtime_delta_seconds"].mean()), 1)
                if group["runtime_delta_seconds"].notna().any()
                else np.nan
            )
            record["mean_total_token_delta_including_cache"] = (
                round(float(group["total_token_delta_including_cache"].mean()), 1)
                if group["total_token_delta_including_cache"].notna().any()
                else np.nan
            )
            record["mean_validation_command_delta"] = (
                round(float(group["validation_command_delta"].mean()), 3)
                if group["validation_command_delta"].notna().any()
                else np.nan
            )
            record["mean_failed_validation_command_delta"] = (
                round(float(group["failed_validation_command_delta"].mean()), 3)
                if group["failed_validation_command_delta"].notna().any()
                else np.nan
            )
            record["mean_changed_file_delta"] = (
                round(float(group["changed_file_delta"].mean()), 3)
                if group["changed_file_delta"].notna().any()
                else np.nan
            )
        rows.append(record)
    order = {label: index for index, label in enumerate(CONDITION_LABELS.values())}
    out = pd.DataFrame(rows)
    out["_order"] = out["condition"].map(order)
    sort_cols = ["backend", "_order"] if by_backend else ["_order"]
    return out.sort_values(sort_cols).drop(columns="_order").reset_index(drop=True)


def write_table(df: pd.DataFrame, name: str) -> None:
    df.to_csv(TABLES / f"{name}.csv", index=False)
    (TABLES / f"{name}.md").write_text(to_markdown(df), encoding="utf-8")


def to_markdown(df: pd.DataFrame) -> str:
    columns = list(df.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in df.to_dict(orient="records"):
        values = [str(row[column]).replace("|", "\\|") for column in columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def save_figure(name: str) -> None:
    for suffix in ["png", "pdf", "svg"]:
        plt.savefig(FIGURES / f"{name}.{suffix}", dpi=220, bbox_inches="tight")
    plt.close()


def style_axis(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#E0E0E0", linewidth=0.8)
    ax.set_axisbelow(True)


def plot_clean_pass_fail_counts(by_backend: pd.DataFrame, combined: pd.DataFrame) -> None:
    plot = by_backend[["backend", "condition", "clean_success_to_degraded_failure"]].copy()
    plot = pd.concat(
        [
            plot,
            combined[["backend", "condition", "clean_success_to_degraded_failure"]],
        ],
        ignore_index=True,
    )
    write_table(plot, "figure_clean_pass_to_degraded_fail_counts_data")
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    x = np.arange(len(CONDITIONS))
    width = 0.24
    for offset, backend in zip([-width, 0, width], ["Custom repos", "SWE-bench", "Combined"], strict=True):
        vals = []
        for condition in [CONDITION_LABELS[c] for c in CONDITIONS]:
            match = plot[(plot["backend"] == backend) & (plot["condition"] == condition)]
            vals.append(int(match["clean_success_to_degraded_failure"].iloc[0]))
        ax.bar(x + offset, vals, width=width, label=backend, color=COLORS["custom_repo" if backend == "Custom repos" else "swebench" if backend == "SWE-bench" else "combined"])
        for xpos, value in zip(x + offset, vals, strict=True):
            ax.text(xpos, value + 0.25, str(value), ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x, [CONDITION_LABELS[c] for c in CONDITIONS], rotation=18, ha="right")
    ax.set_ylabel("Clean-pass / degraded-fail pairs")
    ax.set_xlabel("Degradation")
    ax.set_title("Naming Dominates Clean-Pass To Degraded-Fail Transitions")
    ax.legend(frameon=False)
    style_axis(ax)
    save_figure("clean_pass_to_degraded_fail_counts")


def plot_success_rate_shift(combined: pd.DataFrame) -> None:
    plot = combined.copy()
    write_table(plot, "figure_combined_success_rate_shift_data")
    x = np.arange(len(plot))
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    ax.plot(x, plot["clean_success_rate"], marker="o", color=COLORS["clean"], label="Clean")
    ax.plot(x, plot["degraded_success_rate"], marker="o", color=COLORS["degraded"], label="Degraded")
    for index, row in plot.iterrows():
        ax.plot([index, index], [row["clean_success_rate"], row["degraded_success_rate"]], color="#AAAAAA", linewidth=1)
    ax.set_xticks(x, plot["condition"], rotation=18, ha="right")
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Paired success rate")
    ax.set_xlabel("Degradation")
    ax.set_title("Combined Paired Success Rate: Clean Vs Degraded")
    ax.legend(frameon=False)
    style_axis(ax)
    save_figure("combined_success_rate_shift")


def plot_regression_burden(by_backend: pd.DataFrame, combined: pd.DataFrame) -> None:
    plot = by_backend[["backend", "condition", "regression_failed_delta_sum"]].copy()
    plot = pd.concat(
        [plot, combined[["backend", "condition", "regression_failed_delta_sum"]]],
        ignore_index=True,
    )
    write_table(plot, "figure_regression_failure_delta_data")
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    x = np.arange(len(CONDITIONS))
    width = 0.24
    for offset, backend in zip([-width, 0, width], ["Custom repos", "SWE-bench", "Combined"], strict=True):
        vals = []
        for condition in [CONDITION_LABELS[c] for c in CONDITIONS]:
            match = plot[(plot["backend"] == backend) & (plot["condition"] == condition)]
            vals.append(int(match["regression_failed_delta_sum"].iloc[0]))
        ax.bar(x + offset, vals, width=width, label=backend, color=COLORS["custom_repo" if backend == "Custom repos" else "swebench" if backend == "SWE-bench" else "combined"])
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_xticks(x, [CONDITION_LABELS[c] for c in CONDITIONS], rotation=18, ha="right")
    ax.set_ylabel("Additional previously passing test failures vs clean")
    ax.set_xlabel("Degradation")
    ax.set_title("Naming Carries The Largest Regression Burden")
    ax.legend(frameon=False)
    style_axis(ax)
    save_figure("regression_failure_delta")


def plot_backend_heatmap(by_backend: pd.DataFrame) -> None:
    pivot = by_backend.pivot(index="backend", columns="condition", values="clean_success_to_degraded_failure")
    pivot = pivot[[CONDITION_LABELS[c] for c in CONDITIONS]]
    write_table(pivot.reset_index(), "figure_backend_transition_heatmap_data")
    fig, ax = plt.subplots(figsize=(7.2, 2.8))
    values = pivot.values.astype(float)
    im = ax.imshow(values, cmap="Reds", vmin=0, vmax=max(1, values.max()))
    ax.set_xticks(np.arange(len(pivot.columns)), pivot.columns, rotation=18, ha="right")
    ax.set_yticks(np.arange(len(pivot.index)), pivot.index)
    ax.set_title("Clean-Pass / Degraded-Fail Count By Backend")
    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            ax.text(j, i, str(int(values[i, j])), ha="center", va="center", color="#222222")
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.03, label="Pairs")
    save_figure("backend_transition_heatmap")


def plot_token_delta_pct(combined_metrics: pd.DataFrame) -> None:
    plot = combined_metrics.copy()
    write_table(plot[["condition", "mean_corrected_token_delta_pct", "median_corrected_token_delta_pct", "token_higher_pairs"]], "figure_corrected_token_delta_pct_data")
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    x = np.arange(len(plot))
    vals = plot["mean_corrected_token_delta_pct"].astype(float) * 100
    bars = ax.bar(x, vals, color=["#D62728" if value > 0 else "#4C78A8" for value in vals])
    for bar, value in zip(bars, vals, strict=True):
        va = "bottom" if value >= 0 else "top"
        offset = 1.2 if value >= 0 else -1.2
        ax.text(bar.get_x() + bar.get_width() / 2, value + offset, f"{value:.1f}%", ha="center", va=va, fontsize=8)
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_xticks(x, plot["condition"], rotation=18, ha="right")
    ax.set_ylabel("Mean corrected token delta vs clean (%)")
    ax.set_xlabel("Degradation")
    ax.set_title("Corrected Token Use Usually Increased Under Naming")
    style_axis(ax)
    save_figure("corrected_token_delta_pct")


def plot_files_opened_delta(combined_metrics: pd.DataFrame) -> None:
    plot = combined_metrics.copy()
    write_table(plot[["condition", "mean_files_opened_delta", "median_files_opened_delta"]], "figure_files_opened_delta_data")
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    x = np.arange(len(plot))
    vals = plot["mean_files_opened_delta"].astype(float)
    bars = ax.bar(x, vals, color=["#D62728" if value > 0 else "#4C78A8" for value in vals])
    for bar, value in zip(bars, vals, strict=True):
        va = "bottom" if value >= 0 else "top"
        offset = 0.04 if value >= 0 else -0.04
        ax.text(bar.get_x() + bar.get_width() / 2, value + offset, f"{value:.2f}", ha="center", va=va, fontsize=8)
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_xticks(x, plot["condition"], rotation=18, ha="right")
    ax.set_ylabel("Mean files-opened delta vs clean")
    ax.set_xlabel("Degradation")
    ax.set_title("Search Breadth Shifted Modestly Across Conditions")
    style_axis(ax)
    save_figure("files_opened_delta")


def plot_exploration_efficiency_delta(combined_metrics: pd.DataFrame) -> None:
    plot = combined_metrics.copy()
    write_table(plot[["condition", "mean_exploration_efficiency_delta", "median_exploration_efficiency_delta"]], "figure_exploration_efficiency_delta_data")
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    x = np.arange(len(plot))
    vals = plot["mean_exploration_efficiency_delta"].astype(float) * 100
    bars = ax.bar(x, vals, color=["#D62728" if value < 0 else "#4C78A8" for value in vals])
    for bar, value in zip(bars, vals, strict=True):
        va = "bottom" if value >= 0 else "top"
        offset = 0.8 if value >= 0 else -0.8
        ax.text(bar.get_x() + bar.get_width() / 2, value + offset, f"{value:.1f} pp", ha="center", va=va, fontsize=8)
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_xticks(x, plot["condition"], rotation=18, ha="right")
    ax.set_ylabel("Mean exploration-efficiency delta (percentage points)")
    ax.set_xlabel("Degradation")
    ax.set_title("Remove-Tests And Naming Reduced Search Focus")
    style_axis(ax)
    save_figure("exploration_efficiency_delta")


def plot_backend_metric_heatmap(metrics_by_backend: pd.DataFrame) -> None:
    plot = metrics_by_backend.copy()
    pivot = plot.pivot(index="backend", columns="condition", values="mean_corrected_token_delta_pct")
    pivot = pivot[[CONDITION_LABELS[c] for c in CONDITIONS]]
    write_table(pivot.reset_index(), "figure_backend_token_delta_pct_heatmap_data")
    fig, ax = plt.subplots(figsize=(7.2, 2.8))
    values = pivot.values.astype(float) * 100
    vmax = max(abs(np.nanmin(values)), abs(np.nanmax(values)), 1)
    im = ax.imshow(values, cmap="RdBu_r", vmin=-vmax, vmax=vmax)
    ax.set_xticks(np.arange(len(pivot.columns)), pivot.columns, rotation=18, ha="right")
    ax.set_yticks(np.arange(len(pivot.index)), pivot.index)
    ax.set_title("Mean Corrected Token Delta By Backend")
    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            ax.text(j, i, f"{values[i, j]:.0f}%", ha="center", va="center", color="#222222", fontsize=8)
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.03, label="% vs clean")
    save_figure("backend_token_delta_pct_heatmap")


def write_report(
    backend: pd.DataFrame,
    combined: pd.DataFrame,
    by_backend: pd.DataFrame,
    combined_metrics: pd.DataFrame,
    metrics_by_backend: pd.DataFrame,
) -> None:
    naming = combined[combined["condition"] == "Naming"].iloc[0]
    type_hints = combined[combined["condition"] == "Type hints"].iloc[0]
    comments = combined[combined["condition"] == "Comments/docstrings"].iloc[0]
    remove_tests = combined[combined["condition"] == "Remove tests"].iloc[0]
    custom_backend = backend[backend["backend"] == "Custom repos"].iloc[0]
    swe_backend = backend[backend["backend"] == "SWE-bench"].iloc[0]
    total_backend = backend[backend["backend"] == "Combined"].iloc[0]
    metric_by_condition = {row["condition"]: row for _, row in combined_metrics.iterrows()}
    naming_metric = metric_by_condition["Naming"]
    type_metric = metric_by_condition["Type hints"]
    comments_metric = metric_by_condition["Comments/docstrings"]
    remove_metric = metric_by_condition["Remove tests"]

    def cpf_cell(backend_label: str, condition_label: str) -> str:
        row = by_backend[(by_backend["backend"] == backend_label) & (by_backend["condition"] == condition_label)].iloc[0]
        return f"{int(row['clean_success_to_degraded_failure'])}/{int(row['paired_comparisons'])}"

    def combined_cell(row: pd.Series) -> str:
        return f"{int(row['clean_success_to_degraded_failure'])}/{int(row['paired_comparisons'])}"

    report = f"""# Combined Agent Readiness Analysis

This folder is the small cross-backend handoff package. It combines the custom-repo backend in `LLM-J/` with the SWE-bench backend in `swebench-agent-readiness/`.

## Short Answer

Both backends point in the same direction: naming/semantic clarity is the strongest tested readiness signal for Codex repair success.

Across the paired comparison view, naming produced `{int(naming['clean_success_to_degraded_failure'])}` clean-pass / degraded-fail transitions out of `{int(naming['paired_comparisons'])}` naming comparisons. The other degradations together produced `{int(type_hints['clean_success_to_degraded_failure'] + comments['clean_success_to_degraded_failure'] + remove_tests['clean_success_to_degraded_failure'])}` such transitions across `{int(type_hints['paired_comparisons'] + comments['paired_comparisons'] + remove_tests['paired_comparisons'])}` comparisons.

The combined result does not support a broad checklist-style readiness score yet. It supports a narrower claim: naming and semantic navigation deserve special weight, while type hints, comments/docstrings, and visible tests showed weaker or more process-shaped evidence in these runs.

## What Is Combined

| Backend | Repos | Tasks | Paired comparisons | Clean-pass / degraded-fail |
| --- | ---: | ---: | ---: | ---: |
| Custom repos | {int(custom_backend['repos'])} | {int(custom_backend['tasks'])} | {int(custom_backend['paired_comparisons'])} | {int(custom_backend['clean_success_to_degraded_failure'])} |
| SWE-bench | {int(swe_backend['repos'])} | {int(swe_backend['tasks'])} | {int(swe_backend['paired_comparisons'])} | {int(swe_backend['clean_success_to_degraded_failure'])} |
| Combined | {int(total_backend['repos'])} | {int(total_backend['tasks'])} | {int(total_backend['paired_comparisons'])} | {int(total_backend['clean_success_to_degraded_failure'])} |

The common unit is a same-task paired comparison: the same bug-fix task under clean and degraded conditions. This avoids pretending the two backend matrices have identical raw structure.

## Backend Results Side By Side

| Condition | Custom repos clean-pass / degraded-fail | SWE-bench clean-pass / degraded-fail | Combined |
| --- | ---: | ---: | ---: |
| Naming | {cpf_cell('Custom repos', 'Naming')} | {cpf_cell('SWE-bench', 'Naming')} | {combined_cell(naming)} |
| Type hints | {cpf_cell('Custom repos', 'Type hints')} | {cpf_cell('SWE-bench', 'Type hints')} | {combined_cell(type_hints)} |
| Comments/docstrings | {cpf_cell('Custom repos', 'Comments/docstrings')} | {cpf_cell('SWE-bench', 'Comments/docstrings')} | {combined_cell(comments)} |
| Remove tests | {cpf_cell('Custom repos', 'Remove tests')} | {cpf_cell('SWE-bench', 'Remove tests')} | {combined_cell(remove_tests)} |

The important pattern is not that every backend row is identical. It is that naming is the only condition with a strong negative final-outcome signal in both backends.

## RQ1: What Hurt Final Repair Success?

Naming is the only condition that is strongly negative in both backends.

| Condition | Paired comparisons | Clean success | Degraded success | Clean-pass / degraded-fail | Success-rate shift |
| --- | ---: | ---: | ---: | ---: | ---: |
| Naming | {int(naming['paired_comparisons'])} | {int(naming['clean_success'])} | {int(naming['degraded_success'])} | {int(naming['clean_success_to_degraded_failure'])} | {naming['success_rate_delta_degraded_minus_clean']:.3f} |
| Type hints | {int(type_hints['paired_comparisons'])} | {int(type_hints['clean_success'])} | {int(type_hints['degraded_success'])} | {int(type_hints['clean_success_to_degraded_failure'])} | {type_hints['success_rate_delta_degraded_minus_clean']:.3f} |
| Comments/docstrings | {int(comments['paired_comparisons'])} | {int(comments['clean_success'])} | {int(comments['degraded_success'])} | {int(comments['clean_success_to_degraded_failure'])} | {comments['success_rate_delta_degraded_minus_clean']:.3f} |
| Remove tests | {int(remove_tests['paired_comparisons'])} | {int(remove_tests['clean_success'])} | {int(remove_tests['degraded_success'])} | {int(remove_tests['clean_success_to_degraded_failure'])} | {remove_tests['success_rate_delta_degraded_minus_clean']:.3f} |

Use `figures/clean_pass_to_degraded_fail_counts.png` as the main presentation figure.

## RQ2: Did Degradations Change The Process?

Yes, but this remains supporting evidence. The clean/degraded outcome is still the headline; process metrics explain how the runs changed.

The shared combined metrics use corrected tokens: input plus output tokens, excluding cached input. That gives a more comparable token view across both backends.

| Condition | Median corrected token delta | Mean token delta % | Token-higher pairs | Mean files-opened delta | Mean exploration-efficiency delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| Naming | {naming_metric['median_corrected_token_delta']:.1f} | {100 * naming_metric['mean_corrected_token_delta_pct']:.1f}% | {int(naming_metric['token_higher_pairs'])}/{int(naming_metric['paired_comparisons'])} | {naming_metric['mean_files_opened_delta']:.2f} | {100 * naming_metric['mean_exploration_efficiency_delta']:.1f} pp |
| Type hints | {type_metric['median_corrected_token_delta']:.1f} | {100 * type_metric['mean_corrected_token_delta_pct']:.1f}% | {int(type_metric['token_higher_pairs'])}/{int(type_metric['paired_comparisons'])} | {type_metric['mean_files_opened_delta']:.2f} | {100 * type_metric['mean_exploration_efficiency_delta']:.1f} pp |
| Comments/docstrings | {comments_metric['median_corrected_token_delta']:.1f} | {100 * comments_metric['mean_corrected_token_delta_pct']:.1f}% | {int(comments_metric['token_higher_pairs'])}/{int(comments_metric['paired_comparisons'])} | {comments_metric['mean_files_opened_delta']:.2f} | {100 * comments_metric['mean_exploration_efficiency_delta']:.1f} pp |
| Remove tests | {remove_metric['median_corrected_token_delta']:.1f} | {100 * remove_metric['mean_corrected_token_delta_pct']:.1f}% | {int(remove_metric['token_higher_pairs'])}/{int(remove_metric['paired_comparisons'])} | {remove_metric['mean_files_opened_delta']:.2f} | {100 * remove_metric['mean_exploration_efficiency_delta']:.1f} pp |

Simple read:

- Naming is the clearest combined cost signal: it raised corrected token use by about `{100 * naming_metric['mean_corrected_token_delta_pct']:.1f}%` on average and had higher token use in `{int(naming_metric['token_higher_pairs'])}/{int(naming_metric['paired_comparisons'])}` pairs.
- Comments/docstrings and remove-tests also show token-cost movement, but without the same final-outcome damage.
- Remove-tests did not hurt final success much, but it reduced exploration efficiency the most: `{100 * remove_metric['mean_exploration_efficiency_delta']:.1f}` percentage points on average.
- Files-opened deltas are small in the pooled view, so they should be read as weak search-breadth evidence rather than a headline result.
- Backend-specific process metrics still matter: custom repos include runtime and validation-command deltas; SWE-bench includes changed-file deltas. See `tables/process_metric_summary_by_backend_condition.csv`.

## RQ3: Readiness Tool Takeaway

Do not build or claim a broad readiness score from these results alone.

The safer conclusion is:

> Across two backends, naming/semantic clarity is the best-supported readiness signal. Broader checklist-style readiness claims need empirical calibration against actual agent outcomes.

That is compatible with static readiness tooling, but it argues the tooling should be calibrated, outcome-backed, and honest about which dimensions are proven versus only plausible.

## Presentation Figures

- `figures/clean_pass_to_degraded_fail_counts.png`: main RQ1 result.
- `figures/combined_success_rate_shift.png`: clean versus degraded success rates in the combined paired view.
- `figures/regression_failure_delta.png`: additional previously passing test failures versus clean.
- `figures/backend_transition_heatmap.png`: backend-by-condition transition count.
- `figures/corrected_token_delta_pct.png`: combined corrected-token burden.
- `figures/files_opened_delta.png`: search breadth proxy.
- `figures/exploration_efficiency_delta.png`: search focus proxy.
- `figures/backend_token_delta_pct_heatmap.png`: backend-specific token shift.

## Backend-Specific Metric Tables

The combined tables keep only the shared, paper-level metrics. For backend-specific detail:

- Custom repos: `../LLM-J/final_rq_analysis/tables/process/rq2_process_metric_summary/rq2_process_metric_summary.csv`
- Custom repos token/runtime: `../LLM-J/final_rq_analysis/tables/tokens_runtime/token_runtime_summary/token_runtime_summary.csv`
- SWE-bench process: `../swebench-agent-readiness/final_analysis/tables/rq2_process/rq2_phase_metric_summary/rq2_phase_metric_summary.csv`
- SWE-bench patch/search shape: `../swebench-agent-readiness/final_analysis/tables/process_and_patch_shape/exploration_process_summary/exploration_process_summary.csv`
- SWE-bench tokens: `../swebench-agent-readiness/final_analysis/tables/tokens/token_summary/token_summary.csv`

## Caveats

- The custom backend and SWE-bench backend use different raw data layouts and scoring infrastructure.
- SWE-bench is restricted here to the 10 fully complete repos so the combined story is 10 custom repos plus 10 SWE-bench repos.
- Some SWE-bench complete repos have more than three represented tasks or replicated condition rows; this is why the paired-comparison count is not exactly `10 * 3 * 4`.
- This is a Codex-centered study, not a universal coding-agent benchmark.
- Same-task clean/degraded comparisons are the strongest evidence. Clean-baseline failures should not be over-attributed to degradation.
- Corrected token deltas exclude cached input. LLM-J backend-specific tables still also report total tokens including cached input.
"""
    (OUT / "REPORT.md").write_text(report, encoding="utf-8")

    readme = """# Combined Analysis

This is the small, presentation-oriented folder that brings together the two backend studies:

- `../LLM-J/`: custom-repo backend.
- `../swebench-agent-readiness/`: SWE-bench backend.

Start with `REPORT.md`. The `tables/` and `figures/` folders contain only the combined summaries most likely to be useful in a paper, deck, or project handoff.

Backend-specific process and token tables stay in each backend's own final-analysis folder. This package links to them from `REPORT.md` rather than copying every detailed table here.

## Rebuild

Run from the parent directory that contains `LLM-J/`, `swebench-agent-readiness/`, and `combined_analysis/`:

```bash
python combined_analysis/scripts/build_combined_analysis.py
```

Use whichever Python environment has `pandas`, `numpy`, and `matplotlib` installed.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")

    figures_readme = """# Figures

This folder intentionally contains only presentation-grade combined figures.

- `clean_pass_to_degraded_fail_counts.*`: headline RQ1 figure.
- `combined_success_rate_shift.*`: paired clean/degraded success-rate view.
- `regression_failure_delta.*`: regression burden measured as additional previously passing test failures versus clean.
- `backend_transition_heatmap.*`: quick backend-by-condition comparison.
- `corrected_token_delta_pct.*`: corrected input-plus-output token shift, excluding cached input.
- `files_opened_delta.*`: files-opened-before-first-edit shift.
- `exploration_efficiency_delta.*`: search-focus shift.
- `backend_token_delta_pct_heatmap.*`: backend-specific corrected-token shift.
"""
    (FIGURES / "README.md").write_text(figures_readme, encoding="utf-8")

    tables_readme = """# Tables

Combined tables are derived from the LLM-J and SWE-bench final-analysis exports.

- `combined_paired_matrix.csv`: common paired-comparison matrix.
- `backend_summary.csv`: backend-level counts.
- `combined_condition_summary.csv`: pooled paired-comparison summary by condition.
- `backend_condition_summary.csv`: same summary split by backend.
- `combined_process_metric_summary.csv`: pooled RQ2 metric summary using comparable fields.
- `process_metric_summary_by_backend_condition.csv`: backend-specific RQ2 metric summary.
- `repo_backend_summary.csv`: repo-level transition counts.
"""
    (TABLES / "README.md").write_text(tables_readme, encoding="utf-8")


def validate(df: pd.DataFrame) -> None:
    expected_backends = {"custom_repo", "swebench"}
    if set(df["backend"]) != expected_backends:
        raise SystemExit(f"Unexpected backends: {sorted(set(df['backend']))}")
    custom = df[df["backend"] == "custom_repo"]
    swe = df[df["backend"] == "swebench"]
    if custom["repo"].nunique() != 10:
        raise SystemExit(f"Expected 10 custom repos, found {custom['repo'].nunique()}")
    if swe["repo"].nunique() != 10:
        raise SystemExit(f"Expected 10 SWE-bench repos, found {swe['repo'].nunique()}")
    if custom["task_id"].nunique() != 30:
        raise SystemExit(f"Expected 30 custom tasks, found {custom['task_id'].nunique()}")
    if len(custom) != 120:
        raise SystemExit(f"Expected 120 custom paired comparisons, found {len(custom)}")
    if len(swe) != 125:
        raise SystemExit(f"Expected 125 SWE-bench paired comparisons in complete-repo slice, found {len(swe)}")
    duplicates = df.duplicated(["backend", "repo", "task_id", "condition", "replication_index"]).sum()
    if duplicates:
        raise SystemExit(f"Duplicate backend/repo/task/condition/replication rows: {duplicates}")
    if df["clean_tokens_corrected"].isna().any() or df["degraded_tokens_corrected"].isna().any():
        raise SystemExit("Corrected token coverage is incomplete")
    if df["files_opened_delta"].isna().any():
        raise SystemExit("Files-opened delta coverage is incomplete")
    if df["exploration_efficiency_delta"].isna().any():
        raise SystemExit("Exploration-efficiency delta coverage is incomplete")


def main() -> None:
    ensure_clean_dirs()
    paired = add_pair_flags(pd.concat([custom_pairs(), swebench_pairs()], ignore_index=True))
    validate(paired)

    paired.to_csv(DATA / "combined_paired_matrix.csv", index=False)
    paired.to_json(DATA / "combined_paired_matrix.json", orient="records", indent=2)

    backend = summarize_backend(paired)
    by_backend = condition_summary(paired, by_backend=True)
    combined = condition_summary(paired, by_backend=False)
    repo_summary = repo_backend_summary(paired)
    metrics_by_backend = metric_summary(paired, by_backend=True)
    combined_metrics = metric_summary(paired, by_backend=False)

    write_table(backend, "backend_summary")
    write_table(combined, "combined_condition_summary")
    write_table(by_backend, "backend_condition_summary")
    write_table(combined_metrics, "combined_process_metric_summary")
    write_table(metrics_by_backend, "process_metric_summary_by_backend_condition")
    write_table(repo_summary, "repo_backend_summary")

    plot_clean_pass_fail_counts(by_backend, combined)
    plot_success_rate_shift(combined)
    plot_regression_burden(by_backend, combined)
    plot_backend_heatmap(by_backend)
    plot_token_delta_pct(combined_metrics)
    plot_files_opened_delta(combined_metrics)
    plot_exploration_efficiency_delta(combined_metrics)
    plot_backend_metric_heatmap(metrics_by_backend)
    write_report(backend, combined, by_backend, combined_metrics, metrics_by_backend)

    print(f"Wrote combined analysis to {OUT}")
    print(f"Paired comparisons: {len(paired)}")
    print(f"Repos: {paired[['backend', 'repo']].drop_duplicates().shape[0]}")


if __name__ == "__main__":
    main()
