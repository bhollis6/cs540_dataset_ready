from __future__ import annotations

import textwrap

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from build_analysis_tables import rq2_delta_table
from common import (
    CONDITION_LABELS,
    CONDITION_ORDER,
    FIGURE_DIR,
    TABLE_DIR,
    enriched_rq1,
    ensure_dirs,
    load_rq2,
    wilson_interval,
    write_csv,
)


COLORS = {
    "naming": "#4C78A8",
    "type_hints": "#59A14F",
    "comments_docstrings": "#F28E2B",
    "remove_tests": "#E15759",
    "neutral": "#6B7280",
    "baseline": "#B8B8B8",
}


def save_all(fig: plt.Figure, group: str, stem: str) -> None:
    target = FIGURE_DIR / group
    target.mkdir(parents=True, exist_ok=True)
    for ext in ["png", "pdf", "svg"]:
        fig.savefig(target / f"{stem}.{ext}", bbox_inches="tight", dpi=220)
    plt.close(fig)


def condition_ordered(df: pd.DataFrame) -> pd.DataFrame:
    return df.set_index("condition").loc[CONDITION_ORDER].reset_index()


def readable_condition(condition: str) -> str:
    return CONDITION_LABELS.get(condition, condition).replace("/", "/\n")


def setup() -> None:
    ensure_dirs()
    plt.rcParams.update(
        {
            "font.size": 9,
            "axes.titlesize": 11,
            "axes.labelsize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 8,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#333333",
            "axes.grid": True,
            "grid.color": "#E6E6E6",
            "grid.linewidth": 0.7,
        }
    )


def fig_success_rate(df: pd.DataFrame) -> None:
    rows = []
    for condition, group in df.groupby("condition"):
        ci = wilson_interval(int(group["degraded_success"].sum()), len(group))
        rows.append(
            {
                "condition": condition,
                "n": len(group),
                "degraded_success_rate": ci.rate,
                "ci_low": ci.low,
                "ci_high": ci.high,
                "clean_success_rate": group["clean_success"].mean(),
            }
        )
    data = condition_ordered(pd.DataFrame(rows))
    write_csv(data, TABLE_DIR / "figure_data_target_success_rate_by_condition.csv")
    fig, ax = plt.subplots(figsize=(6.4, 3.7))
    x = np.arange(len(data))
    y = data["degraded_success_rate"].to_numpy()
    low = y - data["ci_low"].to_numpy()
    high = data["ci_high"].to_numpy() - y
    ax.bar(x, y * 100, color=[COLORS[c] for c in data["condition"]], width=0.65)
    ax.errorbar(x, y * 100, yerr=[low * 100, high * 100], fmt="none", color="#222222", capsize=4)
    ax.scatter(x, data["clean_success_rate"] * 100, marker="D", color="#111111", s=28, label="Clean rate")
    ax.set_xticks(
        x,
        [f"{readable_condition(row.condition)}\n(n={int(row.n)})" for row in data.itertuples()],
    )
    ax.set_ylim(0, 105)
    ax.set_ylabel("Bug-fix task success rate (%)")
    ax.set_title("How Often Codex Solved the Task After Each Degradation")
    ax.legend(frameon=False, loc="lower left")
    save_all(fig, "outcomes", "task_success_rate_by_condition_ci")


def fig_counts_by_condition(df: pd.DataFrame) -> None:
    data = condition_ordered(
        df.groupby("condition")
        .agg(
            clean_success_to_degraded_failure=("clean_success_degraded_failure", "sum"),
            fail_to_pass_delta_sum=("fail_to_pass_failed_count_delta", "sum"),
            pass_to_pass_delta_sum=("pass_to_pass_failed_count_delta", "sum"),
            pass_to_pass_damage_rows=("pass_to_pass_damage", "sum"),
        )
        .reset_index()
    )
    write_csv(data, TABLE_DIR / "figure_data_outcome_burdens_by_condition.csv")
    for metric, title, ylabel, stem in [
        (
            "clean_success_to_degraded_failure",
            "Cases Where Clean Passed but Degraded Failed",
            "Number of paired comparisons",
            "clean_success_to_degraded_failure_counts",
        ),
        (
            "fail_to_pass_delta_sum",
            "Net Change in Failed Bug-Fix Target Tests",
            "Degraded minus clean failed target tests",
            "target_test_failure_burden_by_condition",
        ),
        (
            "pass_to_pass_delta_sum",
            "Additional Failed Previously-Passing Tests",
            "Additional failed regression tests",
            "regression_test_failure_burden_by_condition",
        ),
    ]:
        fig, ax = plt.subplots(figsize=(6.2, 3.5))
        x = np.arange(len(data))
        ax.bar(x, data[metric], color=[COLORS[c] for c in data["condition"]], width=0.65)
        ax.set_xticks(x, [readable_condition(c) for c in data["condition"]])
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        for idx, value in enumerate(data[metric]):
            ax.text(idx, value + max(0.2, data[metric].max() * 0.02), str(int(value)), ha="center")
        save_all(fig, "outcomes", stem)


def fig_repo_heatmap(df: pd.DataFrame) -> None:
    data = (
        df.groupby(["repo", "condition"])["clean_success_degraded_failure"]
        .sum()
        .unstack(fill_value=0)
        .reindex(columns=CONDITION_ORDER)
        .sort_index()
    )
    write_csv(data.reset_index(), TABLE_DIR / "figure_data_per_repo_transition_heatmap.csv")
    fig, ax = plt.subplots(figsize=(6.8, 5.2))
    im = ax.imshow(data.to_numpy(), cmap="Blues", aspect="auto", vmin=0)
    ax.set_xticks(np.arange(len(CONDITION_ORDER)), [readable_condition(c) for c in CONDITION_ORDER])
    ax.set_yticks(np.arange(len(data.index)), data.index)
    ax.set_title("Where Clean-Pass to Degraded-Fail Cases Occurred")
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            value = int(data.iloc[i, j])
            ax.text(j, i, str(value), ha="center", va="center", color="#111111")
    fig.colorbar(im, ax=ax, label="Number of paired comparisons")
    save_all(fig, "outcomes", "per_repo_clean_pass_to_degraded_fail_heatmap")


def fig_task_condition_matrix(df: pd.DataFrame) -> None:
    status_rows = []
    task_order = sorted(df["instance_id"].unique())
    for task in task_order:
        task_group = df[df["instance_id"] == task]
        row = {"instance_id": task, "repo": task_group["repo"].iloc[0]}
        for condition in CONDITION_ORDER:
            subset = task_group[task_group["condition"] == condition]
            if subset.empty:
                row[condition] = np.nan
            elif subset["clean_success_degraded_failure"].any():
                row[condition] = -2
            elif subset["pass_to_pass_damage"].any():
                row[condition] = -1
            elif subset["baseline_hard"].all():
                row[condition] = 0
            elif subset["degraded_success"].all():
                row[condition] = 1
            else:
                row[condition] = -0.5
        status_rows.append(row)
    data = pd.DataFrame(status_rows)
    write_csv(data, TABLE_DIR / "figure_data_task_condition_outcome_matrix.csv")
    matrix = data[CONDITION_ORDER].to_numpy(dtype=float)
    cmap = plt.matplotlib.colors.ListedColormap(["#B2182B", "#EF8A62", "#BDBDBD", "#67A9CF"])
    cmap.set_bad("#FFFFFF")
    norm = plt.matplotlib.colors.BoundaryNorm([-2.5, -1.5, -0.5, 0.5, 1.5], cmap.N)
    fig, ax = plt.subplots(figsize=(6.6, max(7.0, len(data) * 0.22)))
    ax.imshow(np.ma.masked_invalid(matrix), cmap=cmap, norm=norm, aspect="auto")
    ax.set_xticks(np.arange(len(CONDITION_ORDER)), [readable_condition(c) for c in CONDITION_ORDER])
    labels = [f"{row.repo}: {row.instance_id.split('__')[-1]}" for row in data.itertuples()]
    ax.set_yticks(np.arange(len(data)), labels)
    ax.set_title("Task by Condition Outcome Matrix")
    legend_items = [
        ("#B2182B", "Clean pass, degraded fail"),
        ("#EF8A62", "Regression tests failed only"),
        ("#BDBDBD", "Clean already failed"),
        ("#67A9CF", "Outcome stable pass"),
        ("#FFFFFF", "Not run / not eligible"),
    ]
    handles = [
        plt.Rectangle((0, 0), 1, 1, facecolor=color, edgecolor="#999999")
        for color, _ in legend_items
    ]
    ax.legend(handles, [label for _, label in legend_items], frameon=False, loc="upper left", bbox_to_anchor=(1.02, 1))
    ax.set_title("Task Outcomes by Degradation")
    save_all(fig, "outcomes", "task_by_degradation_outcome_matrix")


def fig_distribution_by_condition(
    df: pd.DataFrame,
    metric: str,
    ylabel: str,
    title: str,
    group: str,
    stem: str,
    scale: float = 1.0,
) -> None:
    data = [df[df["condition"] == condition][metric].to_numpy() / scale for condition in CONDITION_ORDER]
    export = df[["repo", "instance_id", "condition", metric]].copy()
    write_csv(export, TABLE_DIR / f"figure_data_{stem}.csv")
    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    box = ax.boxplot(
        data,
        patch_artist=True,
        tick_labels=[readable_condition(c) for c in CONDITION_ORDER],
    )
    for patch, condition in zip(box["boxes"], CONDITION_ORDER):
        patch.set_facecolor(COLORS[condition])
        patch.set_alpha(0.75)
    ax.axhline(0, color="#333333", linewidth=0.9)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    save_all(fig, group, stem)


def fig_tokens(df: pd.DataFrame) -> None:
    fig_distribution_by_condition(
        df,
        "total_tokens_corrected_delta",
        "Degraded minus clean tokens (thousands)",
        "Extra or Fewer Tokens Used After Degradation",
        "tokens",
        "paired_token_delta_by_condition",
        scale=1000.0,
    )
    melted = df.melt(
        id_vars=["condition", "repo", "instance_id"],
        value_vars=["clean_total_tokens_corrected", "degraded_total_tokens_corrected"],
        var_name="side",
        value_name="corrected_tokens",
    )
    summary = (
        melted.groupby(["condition", "side"])["corrected_tokens"]
        .median()
        .reset_index()
        .pivot(index="condition", columns="side", values="corrected_tokens")
        .reindex(CONDITION_ORDER)
    )
    write_csv(summary.reset_index(), TABLE_DIR / "figure_data_corrected_token_usage_by_condition.csv")
    fig, ax = plt.subplots(figsize=(6.6, 3.8))
    x = np.arange(len(summary))
    width = 0.36
    ax.bar(x - width / 2, summary["clean_total_tokens_corrected"] / 1000, width, color="#A0AEC0", label="Clean")
    ax.bar(x + width / 2, summary["degraded_total_tokens_corrected"] / 1000, width, color="#2B6CB0", label="Degraded")
    ax.set_xticks(x, [readable_condition(c) for c in summary.index])
    ax.set_ylabel("Median corrected tokens (thousands)")
    ax.set_title("Typical Token Use in Clean vs Degraded Runs")
    ax.legend(frameon=False)
    save_all(fig, "tokens", "corrected_token_usage_by_condition")


def fig_rq2_phase(df: pd.DataFrame) -> None:
    rq2_delta = rq2_delta_table(load_rq2(), df)
    metrics = [
        "bootstrap_command_count_delta",
        "execution_command_count_delta",
        "bootstrap_test_command_count_delta",
        "execution_test_command_count_delta",
        "total_failed_test_command_count_delta",
    ]
    summary = (
        rq2_delta.groupby("condition")[metrics]
        .mean()
        .reindex(CONDITION_ORDER)
        .reset_index()
    )
    write_csv(summary, TABLE_DIR / "figure_data_rq2_phase_process_metric_summary.csv")
    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    x = np.arange(len(summary))
    width = 0.15
    for idx, metric in enumerate(metrics):
        ax.bar(x + (idx - 2) * width, summary[metric], width, label=metric.replace("_count_delta", "").replace("_", " "))
    ax.axhline(0, color="#333333", linewidth=0.9)
    ax.set_xticks(x, [readable_condition(c) for c in summary["condition"]])
    ax.set_ylabel("Mean degraded minus clean event count")
    ax.set_title("How Degradations Changed Agent Process Counts")
    ax.legend(frameon=False, ncol=2)
    save_all(fig, "rq2_process", "rq2_phase_process_metric_summaries")


def fig_baseline_split(df: pd.DataFrame) -> None:
    data = pd.DataFrame(
        {
            "category": [
                "Clean passed,\ndegraded failed",
                "Clean already\nfailed",
                "Outcome stable clean pass",
                "Clean failure, degraded success",
            ],
            "count": [
                int(df["clean_success_degraded_failure"].sum()),
                int(df["baseline_hard"].sum()),
                int((df["clean_success"] & df["degraded_success"]).sum()),
                int(df["clean_failure_degraded_success"].sum()),
            ],
        }
    )
    write_csv(data, TABLE_DIR / "figure_data_baseline_hard_vs_degradation_induced.csv")
    fig, ax = plt.subplots(figsize=(6.8, 3.5))
    colors = ["#B2182B", "#BDBDBD", "#67A9CF", "#59A14F"]
    ax.bar(np.arange(len(data)), data["count"], color=colors)
    labels = ["\n".join(textwrap.wrap(label, width=16)) for label in data["category"]]
    ax.set_xticks(np.arange(len(data)), labels)
    ax.set_ylabel("Number of paired comparisons")
    ax.set_title("Which Failures Are New vs Already Present in Clean Runs")
    for idx, value in enumerate(data["count"]):
        ax.text(idx, value + 0.8, str(int(value)), ha="center")
    save_all(fig, "outcomes", "baseline_hard_vs_degradation_induced_outcome_split")


def main() -> None:
    setup()
    df = enriched_rq1()
    fig_success_rate(df)
    fig_counts_by_condition(df)
    fig_repo_heatmap(df)
    fig_task_condition_matrix(df)
    fig_distribution_by_condition(
        df,
        "changed_file_count_delta",
        "Degraded minus clean changed files",
        "How Many More or Fewer Files Codex Changed",
        "process_and_patch_shape",
        "changed_file_delta_by_condition",
    )
    fig_distribution_by_condition(
        df,
        "files_opened_before_first_edit_delta",
        "Degraded minus clean files opened",
        "Early File Exploration Before the First Edit",
        "process_and_patch_shape",
        "files_opened_exploration_by_condition",
    )
    fig_distribution_by_condition(
        df,
        "exploration_efficiency_delta",
        "Degraded minus clean efficiency ratio",
        "Early Exploration Efficiency",
        "process_and_patch_shape",
        "exploration_efficiency_delta_by_condition",
    )
    fig_tokens(df)
    fig_rq2_phase(df)
    fig_baseline_split(df)
    print(f"Wrote figures to {FIGURE_DIR}")


if __name__ == "__main__":
    main()
