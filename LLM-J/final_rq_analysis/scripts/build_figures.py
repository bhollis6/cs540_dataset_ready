#!/usr/bin/env python3
"""Build publication-friendly figures for the final RQ analysis."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_DIR = ROOT / "final_rq_analysis"
FIG_DIR = ANALYSIS_DIR / "figures"
TABLE_DIR = ANALYSIS_DIR / "tables"
FIGURE_DATA_DIR = TABLE_DIR / "figure_data"
DATA_PATH = ANALYSIS_DIR / "data/enriched_matrix_with_process_metrics.csv"
FALLBACK_DATA_PATH = ANALYSIS_DIR / "data/consolidated_matrix.csv"

CONDITION_ORDER = ["clean", "naming", "type_hints", "comments_docstrings", "remove_tests"]
COLORS = {
    "clean": "#4C78A8",
    "naming": "#D62728",
    "type_hints": "#59A14F",
    "comments_docstrings": "#B07AA1",
    "remove_tests": "#F28E2B",
    "success": "#4C78A8",
    "focal_failure": "#F28E2B",
    "regression_failure": "#D62728",
    "focal_and_regression_failure": "#7F3C8D",
    "uncategorized_oracle_fail": "#8C8C8C",
}

MODE_LABELS = {
    "focal_failure": "Hidden bug-fix tests failed",
    "regression_failure": "Previously passing tests regressed",
    "focal_and_regression_failure": "Both",
    "uncategorized_oracle_fail": "Uncategorized scoring failure",
}

MODE_DATA_COLUMNS = {
    "focal_failure": "hidden_bug_fix_only_failure",
    "regression_failure": "regression_only_failure",
    "focal_and_regression_failure": "hidden_bug_fix_and_regression_failure",
    "uncategorized_oracle_fail": "uncategorized_scoring_failure",
}

PROCESS_METRIC_LABELS = {
    "command_count_before_first_edit": "Commands\nbefore first edit",
    "command_count_after_first_edit": "Commands\nafter first edit",
    "validation_test_command_count": "Validation\ncommands",
    "failed_validation_test_command_count": "Failed validation\ncommands",
    "edit_test_edit_loop_proxy_count": "Edit-test-edit\nloops",
}

FIGURE_GROUPS = {
    "outcomes": {
        "title": "Outcome Figures",
        "description": "Figures about whether the agent solved each historical task under each codebase condition.",
    },
    "failure_modes": {
        "title": "Failure-Mode Figures",
        "description": (
            "Figures splitting failures into missed hidden bug-fix tests and regressions in previously passing tests."
        ),
    },
    "repo_task_detail": {
        "title": "Repo And PR Detail Figures",
        "description": "Figures showing how outcomes vary by repository and historical pull request.",
    },
    "tokens_runtime": {
        "title": "Runtime And Token Figures",
        "description": "Figures showing run-time and token-use burden by condition.",
    },
    "process": {
        "title": "Process Figures",
        "description": "Figures from recovered Codex event-log metrics such as command and validation counts.",
    },
}

FIGURE_CAPTIONS: dict[str, tuple[str, str, str]] = {}


def load_data() -> pd.DataFrame:
    path = DATA_PATH if DATA_PATH.exists() else FALLBACK_DATA_PATH
    df = pd.read_csv(path)
    df["success"] = df["status"].eq("SUCCESS")
    df["condition"] = pd.Categorical(df["condition"], CONDITION_ORDER, ordered=True)
    if "failure_category" not in df.columns:
        df["failure_category"] = df.apply(classify_failure, axis=1)
    df = df.sort_values(["repo", "candidate_id", "condition"]).reset_index(drop=True)
    validate_data(df)
    return df


def validate_data(df: pd.DataFrame) -> None:
    if len(df) != 150:
        raise SystemExit(f"Expected 150 matrix rows, found {len(df)}")
    duplicates = df.duplicated(["repo", "candidate_id", "condition"]).sum()
    if duplicates:
        raise SystemExit(f"Duplicate (repo, candidate_id, condition) rows: {duplicates}")
    errors = int(df["status"].eq("ERROR").sum())
    if errors:
        raise SystemExit(f"Expected 0 harness ERROR rows, found {errors}")
    token_coverage = int(df["total_tokens_including_cache"].notna().sum())
    if token_coverage != len(df):
        raise SystemExit(f"Expected token coverage {len(df)}/{len(df)}, found {token_coverage}/{len(df)}")


def classify_failure(row: pd.Series) -> str:
    if row["status"] == "SUCCESS":
        return "success"
    ftp_failed = int(row.get("fail_to_pass_failed", 0) or 0)
    ptp_failed = int(row.get("pass_to_pass_failed", 0) or 0)
    if ftp_failed and ptp_failed:
        return "focal_and_regression_failure"
    if ftp_failed:
        return "focal_failure"
    if ptp_failed:
        return "regression_failure"
    return "uncategorized_oracle_fail"


def register_caption(group: str, name: str, title: str, caption: str) -> None:
    FIGURE_CAPTIONS[name] = (group, title, caption)


def savefig(group: str, name: str, title: str, caption: str) -> None:
    group_dir = FIG_DIR / group / name
    group_dir.mkdir(parents=True, exist_ok=True)
    for suffix in ["png", "pdf", "svg"]:
        plt.savefig(group_dir / f"{name}.{suffix}", dpi=220, bbox_inches="tight")
    register_caption(group, name, title, caption)
    plt.close()


def write_figure_data(name: str, df: pd.DataFrame, index: bool = False) -> None:
    target = FIGURE_DATA_DIR / name
    target.mkdir(parents=True, exist_ok=True)
    df.to_csv(target / f"{name}_data.csv", index=index)


def wilson(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (np.nan, np.nan)
    p = successes / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half_width = z * np.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denom
    return float(center - half_width), float(center + half_width)


def style_axes(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#D9D9D9", linewidth=0.8, alpha=0.7)
    ax.set_axisbelow(True)


def success_rate_by_condition(df: pd.DataFrame) -> None:
    rows = []
    for condition in CONDITION_ORDER:
        subset = df[df["condition"].astype(str) == condition]
        successes = int(subset["success"].sum())
        n = len(subset)
        low, high = wilson(successes, n)
        rate = successes / n
        rows.append((condition, successes, n, rate, low, high))
    plot = pd.DataFrame(rows, columns=["condition", "success", "n", "rate", "low", "high"])
    write_figure_data("success_rate_by_condition", plot)

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    x = np.arange(len(plot))
    yerr = np.vstack([plot["rate"] - plot["low"], plot["high"] - plot["rate"]])
    ax.bar(x, plot["rate"], color=[COLORS[c] for c in plot["condition"]], width=0.68)
    ax.errorbar(x, plot["rate"], yerr=yerr, fmt="none", ecolor="#222222", capsize=4, linewidth=1.2)
    ax.set_xticks(x, plot["condition"], rotation=20, ha="right")
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Success rate (share of runs solved)")
    ax.set_xlabel("Codebase condition")
    ax.set_title("Agent Solve Rate By Codebase Condition")
    for idx, row in plot.iterrows():
        ax.text(idx, row["rate"] + 0.035, f"{int(row['success'])}/{int(row['n'])}", ha="center", fontsize=9)
    style_axes(ax)
    savefig(
        "outcomes",
        "success_rate_by_condition",
        "Agent Solve Rate By Codebase Condition",
        (
            "Each bar is the share of 30 runs solved under one condition. Error bars are Wilson 95% "
            "confidence intervals. Naming is visibly lower than clean; removing visible tests is not."
        ),
    )


def success_failure_counts(df: pd.DataFrame) -> None:
    rows = []
    for condition in CONDITION_ORDER:
        subset = df[df["condition"].astype(str) == condition]
        rows.append(
            {
                "condition": condition,
                "success": int(subset["success"].sum()),
                "fail": int((~subset["success"]).sum()),
            }
        )
    plot = pd.DataFrame(rows)
    write_figure_data("success_failure_counts_by_condition", plot)

    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    x = np.arange(len(plot))
    ax.bar(x, plot["success"], label="SUCCESS", color="#4C78A8")
    ax.bar(x, plot["fail"], bottom=plot["success"], label="FAIL", color="#D62728")
    ax.set_xticks(x, plot["condition"], rotation=20, ha="right")
    ax.set_ylabel("Runs")
    ax.set_xlabel("Codebase condition")
    ax.set_title("Solved And Failed Runs By Condition")
    ax.legend(frameon=False)
    style_axes(ax)
    savefig(
        "outcomes",
        "success_failure_counts_by_condition",
        "Solved And Failed Runs By Condition",
        "Counts of the 30 runs in each condition. A run is one agent attempt on one historical PR under one condition.",
    )


def repo_heatmap(df: pd.DataFrame) -> None:
    pivot = df.pivot_table(index="repo", columns="condition", values="success", aggfunc="mean", observed=False)
    pivot = pivot[CONDITION_ORDER].sort_values("clean", ascending=False)
    write_figure_data("per_repo_success_heatmap", pivot, index=True)

    fig, ax = plt.subplots(figsize=(7.0, 5.2))
    image = ax.imshow(pivot.values, vmin=0, vmax=1, cmap="RdYlGn", aspect="auto")
    ax.set_xticks(np.arange(len(CONDITION_ORDER)), CONDITION_ORDER, rotation=25, ha="right")
    ax.set_yticks(np.arange(len(pivot.index)), pivot.index)
    ax.set_xlabel("Codebase condition")
    ax.set_ylabel("Repository")
    ax.set_title("Solve Rate By Repository And Condition")
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            ax.text(j, i, f"{pivot.values[i, j]:.2f}", ha="center", va="center", fontsize=8)
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04, label="Success rate")
    savefig(
        "repo_task_detail",
        "per_repo_success_heatmap",
        "Solve Rate By Repository And Condition",
        "Each heatmap entry is the solved-run share for a repository and condition across its three historical PR tasks.",
    )


def pr_condition_matrix(df: pd.DataFrame) -> None:
    plot_df = df.copy()
    plot_df["row"] = plot_df["repo"] + "/" + plot_df["candidate_id"]
    pivot = plot_df.pivot_table(index="row", columns="condition", values="success", aggfunc="first", observed=False)
    pivot = pivot[CONDITION_ORDER].sort_index()
    write_figure_data("pr_condition_outcome_matrix", pivot, index=True)

    fig, ax = plt.subplots(figsize=(7.4, 8.6))
    values = pivot.astype(float).values
    ax.imshow(values, vmin=0, vmax=1, cmap="RdYlGn", aspect="auto")
    ax.set_xticks(np.arange(len(CONDITION_ORDER)), CONDITION_ORDER, rotation=25, ha="right")
    ax.set_yticks(np.arange(len(pivot.index)), pivot.index, fontsize=7)
    ax.set_xlabel("Codebase condition")
    ax.set_ylabel("Repository / historical PR")
    ax.set_title("Pass/Fail Outcome For Every Historical PR")
    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            ax.text(j, i, "P" if values[i, j] == 1 else "F", ha="center", va="center", fontsize=7)
    savefig(
        "repo_task_detail",
        "pr_condition_outcome_matrix",
        "Pass/Fail Outcome For Every Historical PR",
        "P means the agent solved the run; F means final scoring failed. This makes clean-baseline failures visible.",
    )


def failure_mode_stacked(df: pd.DataFrame) -> None:
    modes = ["focal_failure", "regression_failure", "focal_and_regression_failure", "uncategorized_oracle_fail"]
    plot = (
        df[df["failure_category"] != "success"]
        .groupby(["condition", "failure_category"], observed=False)
        .size()
        .unstack(fill_value=0)
        .reindex(CONDITION_ORDER)
    )
    for mode in modes:
        if mode not in plot.columns:
            plot[mode] = 0
    plot = plot[modes]
    write_figure_data("failure_mode_stacked_bars", plot.rename(columns=MODE_DATA_COLUMNS), index=True)

    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    bottom = np.zeros(len(plot))
    x = np.arange(len(plot))
    for mode in modes:
        ax.bar(x, plot[mode], bottom=bottom, label=MODE_LABELS[mode], color=COLORS[mode])
        bottom += plot[mode].values
    ax.set_xticks(x, plot.index, rotation=20, ha="right")
    ax.set_ylabel("Failed runs")
    ax.set_xlabel("Codebase condition")
    ax.set_title("Why Failed Runs Failed")
    ax.legend(frameon=False, fontsize=8)
    style_axes(ax)
    savefig(
        "failure_modes",
        "failure_mode_stacked_bars",
        "Why Failed Runs Failed",
        (
            "Failures are split into missed hidden bug-fix tests, regressions in previously passing tests, "
            "or both. Naming has the broadest failure shape."
        ),
    )


def burden_bars(df: pd.DataFrame, metric: str, title: str, name: str) -> None:
    plot = df.groupby("condition", observed=False)[metric].sum().reindex(CONDITION_ORDER).reset_index()
    write_figure_data(name, plot)
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    x = np.arange(len(plot))
    ax.bar(x, plot[metric], color=[COLORS[c] for c in plot["condition"].astype(str)])
    ax.set_xticks(x, plot["condition"].astype(str), rotation=20, ha="right")
    label = (
        "Previously passing tests that now fail"
        if metric == "pass_to_pass_failed"
        else "Hidden bug-fix tests still failing"
    )
    ax.set_ylabel(label)
    ax.set_xlabel("Codebase condition")
    ax.set_title(title)
    style_axes(ax)
    caption = (
        "Total number of previously passing tests that failed after the agent patch. This is regression burden."
        if metric == "pass_to_pass_failed"
        else "Total number of hidden bug-fix tests still failing after the agent patch."
    )
    savefig("failure_modes", name, title, caption)


def boxplot_metric(
    df: pd.DataFrame,
    metric: str,
    title: str,
    name: str,
    ylabel: str,
    scale: float = 1.0,
    caption: str = "",
) -> None:
    groups = [
        (df[df["condition"].astype(str) == condition][metric].dropna().values / scale)
        for condition in CONDITION_ORDER
    ]
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    bp = ax.boxplot(groups, patch_artist=True, tick_labels=CONDITION_ORDER, showfliers=False)
    for patch, condition in zip(bp["boxes"], CONDITION_ORDER):
        patch.set_facecolor(COLORS[condition])
        patch.set_alpha(0.75)
    ax.set_xticklabels(CONDITION_ORDER, rotation=20, ha="right")
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Codebase condition")
    style_axes(ax)
    savefig("tokens_runtime", name, title, caption)


def paired_shifts(df: pd.DataFrame) -> None:
    rows = []
    clean = df[df["condition"].astype(str) == "clean"][["repo", "candidate_id", "success"]].rename(
        columns={"success": "clean_success"}
    )
    for condition in CONDITION_ORDER[1:]:
        degraded = df[df["condition"].astype(str) == condition][["repo", "candidate_id", "success"]].rename(
            columns={"success": "degraded_success"}
        )
        merged = clean.merge(degraded, on=["repo", "candidate_id"])
        rows.append(
            {
                "condition": condition,
                "clean_success_degraded_fail": int((merged["clean_success"] & ~merged["degraded_success"]).sum()),
                "clean_fail_degraded_success": int((~merged["clean_success"] & merged["degraded_success"]).sum()),
            }
        )
    plot = pd.DataFrame(rows)
    write_figure_data("paired_degraded_vs_clean_outcome_shifts", plot)

    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    x = np.arange(len(plot))
    width = 0.36
    ax.bar(x - width / 2, plot["clean_success_degraded_fail"], width, label="Clean pass -> degraded fail", color="#D62728")
    ax.bar(x + width / 2, plot["clean_fail_degraded_success"], width, label="Clean fail -> degraded pass", color="#4C78A8")
    ax.set_xticks(x, plot["condition"], rotation=20, ha="right")
    ax.set_ylabel("Historical PR tasks")
    ax.set_xlabel("Degraded condition")
    ax.set_title("Same-Task Outcome Shifts Compared With Clean")
    ax.legend(frameon=False, fontsize=8)
    style_axes(ax)
    savefig(
        "outcomes",
        "paired_degraded_vs_clean_outcome_shifts",
        "Same-Task Outcome Shifts Compared With Clean",
        (
            "For each degraded condition, this compares the same historical PR against its clean run. "
            "Red bars are the strongest evidence that the degradation hurt the agent."
        ),
    )


def process_metrics(df: pd.DataFrame) -> None:
    metrics = [
        "command_count_before_first_edit",
        "command_count_after_first_edit",
        "validation_test_command_count",
        "failed_validation_test_command_count",
        "edit_test_edit_loop_proxy_count",
    ]
    available = [metric for metric in metrics if metric in df.columns]
    if not available:
        return
    plot = df.groupby("condition", observed=False)[available].mean().reindex(CONDITION_ORDER)
    write_figure_data("process_metrics_by_condition", plot, index=True)

    fig, axes = plt.subplots(len(available), 1, figsize=(7.4, 2.25 * len(available)), sharex=True)
    if len(available) == 1:
        axes = [axes]
    x = np.arange(len(plot))
    for ax, metric in zip(axes, available):
        ax.bar(x, plot[metric], color=[COLORS[c] for c in CONDITION_ORDER])
        ax.set_ylabel(PROCESS_METRIC_LABELS.get(metric, metric.replace("_", "\n")), fontsize=8)
        style_axes(ax)
    axes[-1].set_xticks(x, CONDITION_ORDER, rotation=20, ha="right")
    axes[0].set_title("Recovered Process Metrics By Condition")
    savefig(
        "process",
        "process_metrics_by_condition",
        "Recovered Process Metrics By Condition",
        (
            "Means from Codex event logs. These are proxy counts, not timestamps: commands before/after first edit, "
            "validation commands, failed validation commands, and edit-test-edit loops."
        ),
    )


def repo_difficulty_distribution(df: pd.DataFrame) -> None:
    plot = df.groupby("repo", observed=False)["success"].mean().sort_values().reset_index()
    write_figure_data("repo_difficulty_distribution", plot)
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.barh(plot["repo"], plot["success"], color="#4C78A8")
    ax.set_xlim(0, 1)
    ax.set_xlabel("Success rate (share of runs solved)")
    ax.set_ylabel("Repository")
    ax.set_title("Repository Difficulty Distribution")
    style_axes(ax)
    savefig(
        "outcomes",
        "repo_difficulty_distribution",
        "Repository Difficulty Distribution",
        "Overall solved-run share by repository. This shows why paired and per-repo sensitivity analyses matter.",
    )


def write_readmes() -> None:
    root_lines = [
        "# Figures",
        "",
        "This directory is grouped by analysis question. Each figure is exported as `.png`, `.pdf`, and `.svg`.",
        "",
        "Plain-language terms used here:",
        "- `Run`: one agent attempt on one historical PR under one condition.",
        "- `Condition`: the codebase version shown to the agent, such as clean or naming-degraded.",
        "- `Hidden bug-fix tests`: tests added by the original PR that should fail before the fix and pass after the fix.",
        "- `Previously passing tests`: existing tests that passed before the agent changed code; failures here are regressions.",
        "- `Tokens`: Codex token usage including cached input tokens unless the label says otherwise.",
        "",
    ]
    for group, meta in FIGURE_GROUPS.items():
        root_lines.append(f"- `{group}/`: {meta['description']}")
    (FIG_DIR / "README.md").write_text("\n".join(root_lines) + "\n", encoding="utf-8")

    captions_by_group: dict[str, list[tuple[str, str, str]]] = {group: [] for group in FIGURE_GROUPS}
    for name, (group, title, caption) in sorted(FIGURE_CAPTIONS.items()):
        captions_by_group[group].append((name, title, caption))

    for group, meta in FIGURE_GROUPS.items():
        lines = [f"# {meta['title']}", "", meta["description"], ""]
        for name, title, caption in captions_by_group[group]:
            lines.extend(
                [
                    f"## {title}",
                    "",
                    f"Folder: `{name}/`",
                    "",
                    f"Files: `{name}/{name}.png`, `{name}/{name}.pdf`, `{name}/{name}.svg`",
                    "",
                    caption,
                    "",
                ]
            )
        (FIG_DIR / group / "README.md").write_text("\n".join(lines), encoding="utf-8")

    figure_data_lines = [
        "# Figure Data",
        "",
        "These CSV files contain the exact aggregated data used to draw the figures.",
        "They are useful for checking values before moving a figure into a report or slide deck.",
        "",
    ]
    for path in sorted(FIGURE_DATA_DIR.glob("*/*.csv")):
        figure_data_lines.append(f"- `{path.relative_to(FIGURE_DATA_DIR)}`")
    (FIGURE_DATA_DIR / "README.md").write_text("\n".join(figure_data_lines) + "\n", encoding="utf-8")


def validate_outputs() -> None:
    pngs = sorted(FIG_DIR.glob("*/*/*.png"))
    if len(pngs) < 10:
        raise SystemExit(f"Expected at least 10 PNG figures, found {len(pngs)}")
    missing = [path for path in pngs if path.stat().st_size == 0]
    if missing:
        raise SystemExit(f"Empty figure files: {missing}")


def build_all() -> None:
    if FIG_DIR.exists():
        shutil.rmtree(FIG_DIR)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    if FIGURE_DATA_DIR.exists():
        shutil.rmtree(FIGURE_DATA_DIR)
    FIGURE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "legend.fontsize": 9,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )
    df = load_data()
    success_rate_by_condition(df)
    success_failure_counts(df)
    repo_heatmap(df)
    pr_condition_matrix(df)
    failure_mode_stacked(df)
    burden_bars(
        df,
        "pass_to_pass_failed",
        "Regression Burden: Previously Passing Tests That Failed",
        "regression_burden_previously_passing_tests",
    )
    burden_bars(
        df,
        "fail_to_pass_failed",
        "Hidden Bug-Fix Miss Burden",
        "hidden_bug_fix_test_miss_burden",
    )
    boxplot_metric(
        df,
        "total_tokens_including_cache",
        "Token Use By Condition",
        "token_usage_by_condition",
        "Total tokens including cache (millions)",
        scale=1_000_000,
        caption=(
            "Distribution of total Codex token usage per run, shown in millions of tokens and including cached input."
        ),
    )
    boxplot_metric(
        df,
        "total_duration_seconds",
        "Runtime By Condition",
        "runtime_by_condition",
        "Total runtime (minutes)",
        scale=60,
        caption="Distribution of total run duration in minutes, including agent time and final scoring time.",
    )
    paired_shifts(df)
    process_metrics(df)
    repo_difficulty_distribution(df)
    write_readmes()
    validate_outputs()
    print(f"Wrote figures under {FIG_DIR}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    build_all()


if __name__ == "__main__":
    main()
