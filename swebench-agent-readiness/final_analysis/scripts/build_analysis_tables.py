from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from common import (
    CONDITION_ORDER,
    DATA_DIR,
    RQ1_CSV,
    RQ1_JSON,
    RQ2_CSV,
    RQ2_JSON,
    TABLE_DIR,
    as_rate_pct,
    condition_sort_key,
    enriched_rq1,
    ensure_dirs,
    load_rq2,
    load_task_profiles,
    odds_ratio,
    safe_ratio,
    wilson_interval,
    write_csv,
    write_latex_table,
    write_markdown_table,
)


def ordered_conditions(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(_condition_order=df["condition"].map(condition_sort_key)).sort_values(
        ["_condition_order", "condition"]
    ).drop(columns=["_condition_order"])


def condition_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for condition, group in df.groupby("condition", sort=False):
        n = len(group)
        clean_successes = int(group["clean_success"].sum())
        degraded_successes = int(group["degraded_success"].sum())
        ci = wilson_interval(degraded_successes, n)
        clean_rate = clean_successes / n
        degraded_rate = degraded_successes / n
        rows.append(
            {
                "condition": condition,
                "n": n,
                "unique_tasks": group["instance_id"].nunique(),
                "repos": group["repo"].nunique(),
                "clean_success_rate_pct": as_rate_pct(clean_rate),
                "degraded_success_rate_pct": as_rate_pct(degraded_rate),
                "degraded_success_ci95_low_pct": as_rate_pct(ci.low),
                "degraded_success_ci95_high_pct": as_rate_pct(ci.high),
                "paired_success_rate_delta_pct": as_rate_pct(degraded_rate - clean_rate),
                "risk_ratio_degraded_vs_clean": round(safe_ratio(degraded_rate, clean_rate), 3),
                "odds_ratio_degraded_vs_clean": round(
                    odds_ratio(
                        degraded_successes,
                        n - degraded_successes,
                        clean_successes,
                        n - clean_successes,
                    ),
                    3,
                ),
                "clean_success_to_degraded_failure": int(
                    group["clean_success_degraded_failure"].sum()
                ),
                "clean_failure_to_degraded_success": int(group["clean_failure_degraded_success"].sum()),
                "baseline_hard_rows": int(group["baseline_hard"].sum()),
                "fail_to_pass_delta_sum": int(group["fail_to_pass_failed_count_delta"].sum()),
                "pass_to_pass_delta_sum": int(group["pass_to_pass_failed_count_delta"].sum()),
                "pass_to_pass_damage_rows": int(group["pass_to_pass_damage"].sum()),
                "mean_token_delta": round(group["total_tokens_corrected_delta"].mean(), 1),
                "median_token_delta": round(group["total_tokens_corrected_delta"].median(), 1),
                "degraded_tokens_higher_rows": int((group["total_tokens_corrected_delta"] > 0).sum()),
                "degraded_tokens_lower_rows": int((group["total_tokens_corrected_delta"] < 0).sum()),
                "mean_changed_file_delta": round(group["changed_file_count_delta"].mean(), 2),
                "median_changed_file_delta": round(group["changed_file_count_delta"].median(), 2),
                "mean_files_opened_delta": round(
                    group["files_opened_before_first_edit_delta"].mean(), 2
                ),
                "mean_exploration_efficiency_delta": round(
                    group["exploration_efficiency_delta"].mean(), 3
                ),
                "mean_dead_end_file_opens_delta": round(
                    group["dead_end_file_opens_delta"].mean(), 2
                ),
            }
        )
    return ordered_conditions(pd.DataFrame(rows))


def repo_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    complete_tasks = (
        df.groupby(["repo", "instance_id"])["condition"]
        .agg(lambda values: set(values))
        .reset_index(name="conditions")
    )
    complete_tasks["has_all_four_conditions"] = complete_tasks["conditions"].map(
        lambda values: set(CONDITION_ORDER).issubset(values)
    )
    complete_counts = complete_tasks.groupby("repo")["has_all_four_conditions"].sum()
    for repo, group in df.groupby("repo", sort=True):
        rows.append(
            {
                "repo": repo,
                "rows": len(group),
                "unique_tasks": group["instance_id"].nunique(),
                "complete_all_four_tasks": int(complete_counts.get(repo, 0)),
                "fully_complete_repo": bool(complete_counts.get(repo, 0) >= 3),
                "clean_success_rate_pct": as_rate_pct(group["clean_success"].mean()),
                "degraded_success_rate_pct": as_rate_pct(group["degraded_success"].mean()),
                "clean_success_to_degraded_failure": int(
                    group["clean_success_degraded_failure"].sum()
                ),
                "baseline_hard_rows": int(group["baseline_hard"].sum()),
                "fail_to_pass_delta_sum": int(group["fail_to_pass_failed_count_delta"].sum()),
                "pass_to_pass_delta_sum": int(group["pass_to_pass_failed_count_delta"].sum()),
                "pass_to_pass_damage_rows": int(group["pass_to_pass_damage"].sum()),
                "mean_token_delta": round(group["total_tokens_corrected_delta"].mean(), 1),
                "median_token_delta": round(group["total_tokens_corrected_delta"].median(), 1),
            }
        )
    return pd.DataFrame(rows)


def task_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (repo, instance_id), group in df.groupby(["repo", "instance_id"], sort=True):
        rows.append(
            {
                "repo": repo,
                "instance_id": instance_id,
                "conditions_observed": "|".join(sorted(group["condition"].unique())),
                "has_all_four_conditions": set(CONDITION_ORDER).issubset(set(group["condition"])),
                "rows": len(group),
                "clean_success_any": bool(group["clean_success"].any()),
                "clean_success_all_rows": bool(group["clean_success"].all()),
                "baseline_hard_any": bool((~group["clean_success"]).any()),
                "degraded_success_all_rows": bool(group["degraded_success"].all()),
                "clean_success_to_degraded_failure": int(
                    group["clean_success_degraded_failure"].sum()
                ),
                "pass_to_pass_damage_rows": int(group["pass_to_pass_damage"].sum()),
                "fail_to_pass_delta_sum": int(group["fail_to_pass_failed_count_delta"].sum()),
                "pass_to_pass_delta_sum": int(group["pass_to_pass_failed_count_delta"].sum()),
                "mean_token_delta": round(group["total_tokens_corrected_delta"].mean(), 1),
                "annotation_nodes": group["annotation_nodes"].dropna().iloc[0]
                if group["annotation_nodes"].notna().any()
                else np.nan,
                "type_hints_zero_or_low_signal": bool(
                    (group["annotation_nodes"].fillna(0).iloc[0] <= 1)
                ),
            }
        )
    return pd.DataFrame(rows)


def paired_summary(df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "repo",
        "instance_id",
        "condition",
        "replication_index",
        "clean_success",
        "degraded_success",
        "clean_success_degraded_failure",
        "baseline_hard",
        "fail_to_pass_failed_count_delta",
        "pass_to_pass_failed_count_delta",
        "total_tokens_corrected_delta",
        "changed_file_count_delta",
        "files_opened_before_first_edit_delta",
        "exploration_efficiency_delta",
        "comparison_path",
    ]
    return ordered_conditions(df[columns]).sort_values(["repo", "instance_id", "condition"])


def token_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for condition, group in df.groupby("condition"):
        rows.append(
            {
                "condition": condition,
                "n": len(group),
                "clean_total_tokens_mean": round(group["clean_total_tokens_corrected"].mean(), 1),
                "degraded_total_tokens_mean": round(
                    group["degraded_total_tokens_corrected"].mean(), 1
                ),
                "delta_mean": round(group["total_tokens_corrected_delta"].mean(), 1),
                "delta_median": round(group["total_tokens_corrected_delta"].median(), 1),
                "delta_min": int(group["total_tokens_corrected_delta"].min()),
                "delta_max": int(group["total_tokens_corrected_delta"].max()),
                "degraded_higher_count": int((group["total_tokens_corrected_delta"] > 0).sum()),
                "degraded_lower_count": int((group["total_tokens_corrected_delta"] < 0).sum()),
            }
        )
    return ordered_conditions(pd.DataFrame(rows))


def exploration_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for condition, group in df.groupby("condition"):
        rows.append(
            {
                "condition": condition,
                "n": len(group),
                "clean_files_opened_mean": round(
                    group["clean_files_opened_before_first_edit"].mean(), 2
                ),
                "degraded_files_opened_mean": round(
                    group["degraded_files_opened_before_first_edit"].mean(), 2
                ),
                "files_opened_delta_mean": round(
                    group["files_opened_before_first_edit_delta"].mean(), 2
                ),
                "clean_efficiency_mean": round(group["clean_exploration_efficiency"].mean(), 3),
                "degraded_efficiency_mean": round(
                    group["degraded_exploration_efficiency"].mean(), 3
                ),
                "efficiency_delta_mean": round(group["exploration_efficiency_delta"].mean(), 3),
                "dead_end_file_opens_delta_mean": round(
                    group["dead_end_file_opens_delta"].mean(), 2
                ),
                "changed_file_delta_mean": round(group["changed_file_count_delta"].mean(), 2),
            }
        )
    return ordered_conditions(pd.DataFrame(rows))


def rq2_delta_table(rq2: pd.DataFrame, rq1: pd.DataFrame) -> pd.DataFrame:
    keys = ["comparison_file", "instance_id", "repo", "chosen_condition", "replication_index"]
    metric_cols = [
        "event_count",
        "first_edit_event_index",
        "bootstrap_event_count",
        "bootstrap_command_count",
        "bootstrap_failed_command_count",
        "bootstrap_test_command_count",
        "bootstrap_failed_test_command_count",
        "execution_event_count",
        "execution_command_count",
        "execution_failed_command_count",
        "execution_test_command_count",
        "execution_failed_test_command_count",
        "total_command_count",
        "total_test_command_count",
        "total_failed_test_command_count",
    ]
    clean = rq2[rq2["side"] == "clean"][keys + metric_cols].copy()
    degraded = rq2[rq2["side"] == "degraded"][keys + metric_cols].copy()
    merged = clean.merge(
        degraded,
        on=keys,
        suffixes=("_clean", "_degraded"),
        validate="one_to_one",
    )
    for col in metric_cols:
        merged[f"{col}_delta"] = merged[f"{col}_degraded"] - merged[f"{col}_clean"]
    merged = merged.rename(columns={"chosen_condition": "condition"})
    flags = rq1[
        [
            "comparison_file",
            "clean_success_degraded_failure",
            "pass_to_pass_damage",
            "baseline_hard",
            "total_tokens_corrected_delta",
            "changed_file_count_delta",
        ]
    ]
    return merged.merge(flags, on="comparison_file", how="left", validate="one_to_one")


def rq2_phase_summary(rq2_delta: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for condition, group in rq2_delta.groupby("condition"):
        rows.append(
            {
                "condition": condition,
                "n": len(group),
                "first_edit_event_index_delta_mean": round(
                    group["first_edit_event_index_delta"].mean(), 2
                ),
                "bootstrap_command_delta_mean": round(
                    group["bootstrap_command_count_delta"].mean(), 2
                ),
                "execution_command_delta_mean": round(
                    group["execution_command_count_delta"].mean(), 2
                ),
                "bootstrap_test_command_delta_mean": round(
                    group["bootstrap_test_command_count_delta"].mean(), 2
                ),
                "execution_test_command_delta_mean": round(
                    group["execution_test_command_count_delta"].mean(), 2
                ),
                "failed_test_command_delta_mean": round(
                    group["total_failed_test_command_count_delta"].mean(), 2
                ),
                "total_command_delta_mean": round(group["total_command_count_delta"].mean(), 2),
                "bootstrap_command_delta_positive_rows": int(
                    (group["bootstrap_command_count_delta"] > 0).sum()
                ),
                "execution_command_delta_positive_rows": int(
                    (group["execution_command_count_delta"] > 0).sum()
                ),
            }
        )
    return ordered_conditions(pd.DataFrame(rows))


def rq2_correlations(rq2_delta: pd.DataFrame) -> pd.DataFrame:
    pairs = [
        ("bootstrap_command_count_delta", "execution_command_count_delta"),
        ("first_edit_event_index_delta", "total_tokens_corrected_delta"),
        ("bootstrap_command_count_delta", "total_tokens_corrected_delta"),
        ("execution_test_command_count_delta", "total_failed_test_command_count_delta"),
        ("changed_file_count_delta", "total_tokens_corrected_delta"),
    ]
    rows: list[dict[str, object]] = []
    for left, right in pairs:
        ranked = rq2_delta[[left, right]].rank()
        rows.append(
            {
                "metric_x": left,
                "metric_y": right,
                "pearson_r": round(rq2_delta[left].corr(rq2_delta[right], method="pearson"), 3),
                "spearman_r": round(ranked[left].corr(ranked[right], method="pearson"), 3),
                "n": int(rq2_delta[[left, right]].dropna().shape[0]),
            }
        )
    return pd.DataFrame(rows)


def leave_one_repo_out(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    repos = sorted(df["repo"].unique())
    for condition, condition_group in df.groupby("condition"):
        for omitted_repo in repos:
            group = condition_group[condition_group["repo"] != omitted_repo]
            if group.empty:
                continue
            rows.append(
                {
                    "condition": condition,
                    "omitted_repo": omitted_repo,
                    "n": len(group),
                    "clean_success_to_degraded_failure": int(
                        group["clean_success_degraded_failure"].sum()
                    ),
                    "pass_to_pass_damage_rows": int(group["pass_to_pass_damage"].sum()),
                    "pass_to_pass_delta_sum": int(group["pass_to_pass_failed_count_delta"].sum()),
                    "degraded_success_rate_pct": as_rate_pct(group["degraded_success"].mean()),
                    "mean_token_delta": round(group["total_tokens_corrected_delta"].mean(), 1),
                }
            )
    return ordered_conditions(pd.DataFrame(rows))


def write_all_formats(name: str, df: pd.DataFrame, latex: bool = True) -> None:
    write_csv(df, TABLE_DIR / f"{name}.csv")
    write_markdown_table(df, TABLE_DIR / f"{name}.md")
    if latex:
        write_latex_table(df, TABLE_DIR / f"{name}.tex")


def public_path_text(value: object) -> object:
    if not isinstance(value, str):
        return value
    text = value
    legacy_pivot_marker = "LLM-J/" + "swebench_" + "pivot/"
    for marker in [legacy_pivot_marker, "swebench-agent-readiness/"]:
        marker_index = text.find(marker)
        if marker_index >= 0:
            text = text[marker_index + len(marker) :]
    return text


def sanitize_record(value: object) -> object:
    if isinstance(value, dict):
        return {key: sanitize_record(item) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_record(item) for item in value]
    return public_path_text(value)


def copy_public_source_export(source: Path, target: Path) -> None:
    if source.suffix == ".csv":
        df = pd.read_csv(source)
        for column in df.columns:
            if df[column].dtype == object:
                df[column] = df[column].map(public_path_text)
        write_csv(df, target)
        return
    if source.suffix == ".json":
        payload = sanitize_record(json.loads(source.read_text()))
        target.write_text(json.dumps(payload, indent=2) + "\n")
        return
    raise ValueError(f"Unsupported source export type: {source}")


def main() -> None:
    ensure_dirs()
    df = enriched_rq1()
    rq2 = load_rq2()
    rq2_delta = rq2_delta_table(rq2, df)
    profiles = load_task_profiles(df["instance_id"])

    for source in [RQ1_CSV, RQ1_JSON, RQ2_CSV, RQ2_JSON]:
        copy_public_source_export(source, DATA_DIR / source.name)

    write_csv(df, DATA_DIR / "rq1_enriched_analysis_matrix.csv")
    write_csv(rq2_delta, DATA_DIR / "rq2_phase_delta_matrix.csv")
    write_csv(profiles, DATA_DIR / "selected_task_repo_summary.csv")

    tables = {
        "condition_summary": condition_summary(df),
        "repo_summary": repo_summary(df),
        "task_summary": task_summary(df),
        "paired_clean_degraded_summary": paired_summary(df),
        "transition_table": df[df["clean_success_degraded_failure"]]
        .sort_values(["repo", "instance_id"])[
            [
                "repo",
                "instance_id",
                "condition",
                "replication_index",
                "fail_to_pass_failed_count_delta",
                "pass_to_pass_failed_count_delta",
                "total_tokens_corrected_delta",
                "changed_file_count_delta",
                "files_opened_before_first_edit_delta",
                "exploration_efficiency_delta",
                "comparison_path",
            ]
        ],
        "pass_to_pass_damage_table": df[df["pass_to_pass_damage"]]
        .sort_values(["condition", "repo", "instance_id"])[
            [
                "repo",
                "instance_id",
                "condition",
                "clean_success",
                "degraded_success",
                "fail_to_pass_failed_count_delta",
                "pass_to_pass_failed_count_delta",
                "total_tokens_corrected_delta",
                "changed_file_count_delta",
                "comparison_path",
            ]
        ],
        "token_summary": token_summary(df),
        "exploration_process_summary": exploration_summary(df),
        "rq2_phase_metric_summary": rq2_phase_summary(rq2_delta),
        "rq2_phase_correlations": rq2_correlations(rq2_delta),
        "leave_one_repo_out_condition_effects": leave_one_repo_out(df),
        "baseline_hard_tasks": df[df["baseline_hard"]]
        .sort_values(["repo", "instance_id", "condition"])[
            [
                "repo",
                "instance_id",
                "condition",
                "clean_fail_to_pass_failed_count",
                "degraded_fail_to_pass_failed_count",
                "clean_pass_to_pass_failed_count",
                "degraded_pass_to_pass_failed_count",
                "degraded_success",
                "total_tokens_corrected_delta",
                "comparison_path",
            ]
        ],
        "type_hints_surface_summary": df[df["condition"] == "type_hints"]
        .sort_values(["annotation_nodes", "repo", "instance_id"])[
            [
                "repo",
                "instance_id",
                "annotation_nodes",
                "type_hints_signal_level",
                "type_hints_rationale",
                "clean_success",
                "degraded_success",
                "total_tokens_corrected_delta",
                "comparison_path",
            ]
        ],
        "high_token_delta_cases": df.reindex(
            df["total_tokens_corrected_delta"].abs().sort_values(ascending=False).index
        )
        .head(20)[
            [
                "repo",
                "instance_id",
                "condition",
                "clean_success",
                "degraded_success",
                "total_tokens_corrected_delta",
                "clean_total_tokens_corrected",
                "degraded_total_tokens_corrected",
                "changed_file_count_delta",
                "comparison_path",
            ]
        ],
        "degraded_cheaper_cases": df[df["total_tokens_corrected_delta"] < 0]
        .sort_values("total_tokens_corrected_delta")
        .head(25)[
            [
                "repo",
                "instance_id",
                "condition",
                "clean_success",
                "degraded_success",
                "total_tokens_corrected_delta",
                "changed_file_count_delta",
                "files_opened_before_first_edit_delta",
                "comparison_path",
            ]
        ],
        "remove_tests_patch_target_shifts": df[
            (df["condition"] == "remove_tests") & (df["degraded_only_changed_file_count"] > 0)
        ]
        .sort_values(["repo", "instance_id"])[
            [
                "repo",
                "instance_id",
                "condition",
                "clean_changed_files",
                "degraded_changed_files",
                "changed_file_count_delta",
                "degraded_only_changed_file_count",
                "clean_success",
                "degraded_success",
                "comparison_path",
            ]
        ],
    }
    for name, table in tables.items():
        write_all_formats(name, table)

    print(f"Wrote {len(tables)} table groups to {TABLE_DIR}")
    print(f"Wrote enriched matrices to {DATA_DIR}")


if __name__ == "__main__":
    main()
