#!/usr/bin/env python3
"""Build final RQ analysis tables, lightweight data extracts, and handoff docs."""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_DIR = ROOT / "final_rq_analysis"
DATA_DIR = ANALYSIS_DIR / "data"
MATRIX_CSV = DATA_DIR / "consolidated_matrix.csv"
MATRIX_JSON = DATA_DIR / "consolidated_matrix.json"
LEGACY_MATRIX_CSV = ROOT / "comparison_slices/rq1_initial_matrix_missing/rq1_3x3x5_matrix.csv"
LEGACY_MATRIX_JSON = ROOT / "comparison_slices/rq1_initial_matrix_missing/rq1_3x3x5_matrix.json"
ENRICHED_CSV = ANALYSIS_DIR / "data/enriched_matrix_with_process_metrics.csv"

CONDITION_ORDER = ["clean", "naming", "type_hints", "comments_docstrings", "remove_tests"]
DEGRADED_CONDITIONS = [condition for condition in CONDITION_ORDER if condition != "clean"]
HARD_REPOS = {"pip-tools", "pydantic-settings", "copier"}
FAILURE_MODE_LABELS = {
    "success": "success",
    "focal_failure": "hidden_bug_fix_only_failure",
    "regression_failure": "regression_only_failure",
    "focal_and_regression_failure": "hidden_bug_fix_and_regression_failure",
    "uncategorized_oracle_fail": "uncategorized_scoring_failure",
    "harness_error": "harness_error",
}

AUDIT_CASES = [
    # All clean failures.
    ("all_clean_failures", "cattrs", "cattrs_pr_142", "clean"),
    ("all_clean_failures", "click", "click_pr_2816", "clean"),
    ("all_clean_failures", "click", "click_pr_3004", "clean"),
    ("all_clean_failures", "copier", "copier_pr_2587", "clean"),
    ("all_clean_failures", "pip-tools", "pip-tools_pr_1893", "clean"),
    ("all_clean_failures", "pip-tools", "pip-tools_pr_2087", "clean"),
    ("all_clean_failures", "pydantic-settings", "pydantic-settings_pr_730", "clean"),
    ("all_clean_failures", "pydantic-settings", "pydantic-settings_pr_773", "clean"),
    ("all_clean_failures", "starlette", "starlette_pr_2422", "clean"),
    # Naming failures split by failure shape.
    ("naming_regression_only", "httpx", "httpx_pr_2423", "naming"),
    ("naming_regression_only", "marshmallow", "marshmallow_pr_2772", "naming"),
    ("naming_regression_only", "starlette", "starlette_pr_2400", "naming"),
    ("naming_hidden_bug_fix_only", "uvicorn", "uvicorn_pr_2183", "naming"),
    ("naming_hidden_bug_fix_only", "pip-tools", "pip-tools_pr_1893", "naming"),
    ("naming_hidden_bug_fix_only", "pydantic-settings", "pydantic-settings_pr_730", "naming"),
    ("naming_hidden_bug_fix_and_regression", "copier", "copier_pr_2432", "naming"),
    ("naming_hidden_bug_fix_and_regression", "copier", "copier_pr_2605", "naming"),
    ("naming_hidden_bug_fix_and_regression", "pydantic-settings", "pydantic-settings_pr_780", "naming"),
    # Remove-tests successes and failures.
    ("remove_tests_success", "cattrs", "cattrs_pr_108", "remove_tests"),
    ("remove_tests_success", "pydantic-settings", "pydantic-settings_pr_780", "remove_tests"),
    ("remove_tests_failure", "httpx", "httpx_pr_2547", "remove_tests"),
    ("remove_tests_failure", "click", "click_pr_3004", "remove_tests"),
    ("remove_tests_failure", "pip-tools", "pip-tools_pr_2087", "remove_tests"),
    # Additional strong pass examples used as sanity checks in the handoff narrative.
    ("strong_pass", "click", "click_pr_2846", "type_hints"),
    ("strong_pass", "click", "click_pr_2846", "comments_docstrings"),
    ("strong_pass", "structlog", "structlog_pr_713", "comments_docstrings"),
]


@dataclass(frozen=True)
class FactorySource:
    title: str
    url: str
    note: str


FACTORY_SOURCES = [
    FactorySource(
        title="Factory Readiness Report Command",
        url="https://docs.factory.ai/cli/features/readiness-report",
        note=(
            "Documents `/readiness-report`, repository evaluation, five maturity levels, "
            "criteria scoring, persisted reports, and remediation plans."
        ),
    ),
    FactorySource(
        title="Factory Agent Readiness Overview",
        url="https://docs.factory.ai/web/agent-readiness/overview",
        note=(
            "Documents five readiness levels, 80% gated progression, repository vs "
            "application scopes, and technical pillars such as validation, testing, "
            "documentation, development environment, observability, security, task "
            "discovery, and product/experimentation."
        ),
    ),
    FactorySource(
        title="Factory Introducing Agent Readiness",
        url="https://factory.ai/news/agent-readiness",
        note=(
            "Product announcement describing readiness reports, technical pillars, "
            "binary criteria/file/config checks, and claimed variance reduction through "
            "grounding evaluations on prior reports."
        ),
    ),
]

TABLE_GROUPS = {
    "overview": {
        "title": "Overview Tables",
        "description": "Top-level condition, repository, PR, and paired-comparison summaries.",
    },
    "outcomes": {
        "title": "Outcome Tables",
        "description": "Paired clean/degraded outcomes, baseline-hard tasks, and condition transitions.",
    },
    "failure_modes": {
        "title": "Failure-Mode Tables",
        "description": "Tables that explain how failed runs failed.",
    },
    "process": {
        "title": "RQ2 Process Tables",
        "description": "Recovered Codex process metrics and correlations.",
    },
    "tokens_runtime": {
        "title": "Token And Runtime Tables",
        "description": "Duration and token-use summaries. Token totals include cached input where labeled.",
    },
    "audit_and_manifests": {
        "title": "Audit And Manifest Tables",
        "description": "Manual-audit sample manifests, validation checks, and raw-artifact references.",
    },
    "metadata": {
        "title": "Metadata Tables",
        "description": "PR metadata and source-artifact lookup tables.",
    },
    "sensitivity_and_validation": {
        "title": "Sensitivity And Validation Tables",
        "description": "Checks for per-repo influence and paired condition effects.",
    },
}

TABLE_TO_GROUP = {
    "condition_summary": "overview",
    "repo_summary": "overview",
    "pr_summary": "overview",
    "paired_clean_vs_degraded_summary": "outcomes",
    "paired_clean_vs_degraded_detail": "outcomes",
    "clean_baseline_failures": "outcomes",
    "clean_pass_degraded_failures": "outcomes",
    "token_runtime_summary": "tokens_runtime",
    "leave_one_repo_out_condition_effects": "sensitivity_and_validation",
    "validation_summary": "sensitivity_and_validation",
    "failure_mode_summary": "failure_modes",
    "rq2_process_metric_summary": "process",
    "rq2_process_correlations": "process",
    "audited_run_table": "audit_and_manifests",
    "per_pr_metadata_summary": "metadata",
}


def rel(path: Path | str) -> str:
    path_obj = Path(path)
    if not path_obj.is_absolute():
        path_obj = ROOT / path_obj
    try:
        return str(path_obj.relative_to(ROOT))
    except ValueError:
        return str(path_obj)


def load_matrix() -> pd.DataFrame:
    if ENRICHED_CSV.exists():
        path = ENRICHED_CSV
    elif MATRIX_CSV.exists():
        path = MATRIX_CSV
    elif LEGACY_MATRIX_CSV.exists():
        path = LEGACY_MATRIX_CSV
    else:
        raise SystemExit(f"No matrix found at {MATRIX_CSV} or {LEGACY_MATRIX_CSV}")
    df = pd.read_csv(path)
    df["success"] = df["status"].eq("SUCCESS")
    df["failure_category"] = df.apply(classify_failure, axis=1)
    df["condition"] = pd.Categorical(df["condition"], CONDITION_ORDER, ordered=True)
    return df.sort_values(["repo", "candidate_id", "condition"]).reset_index(drop=True)


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
    if row["status"] == "ERROR":
        return "harness_error"
    return "uncategorized_oracle_fail"


def validate_matrix(df: pd.DataFrame) -> None:
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


def wilson(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = successes / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half_width = z * math.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denom
    return center - half_width, center + half_width


def safe_ratio(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else float("nan")


def odds_ratio(a_success: int, a_total: int, b_success: int, b_total: int) -> float:
    a_fail = a_total - a_success
    b_fail = b_total - b_success
    return ((a_success + 0.5) * (b_fail + 0.5)) / ((a_fail + 0.5) * (b_success + 0.5))


def markdown_table(df: pd.DataFrame, max_rows: int | None = None) -> str:
    view = df.head(max_rows).copy() if max_rows else df.copy()
    if view.empty:
        return "_No rows._"
    view = view.fillna("")
    columns = list(view.columns)
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in view.iterrows():
        values = [str(row[col]).replace("\n", " ") for col in columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def plain_failure_mode(value: str) -> str:
    return FAILURE_MODE_LABELS.get(str(value), str(value))


def write_table(df: pd.DataFrame, name: str) -> None:
    tables_dir = ANALYSIS_DIR / "tables"
    group = TABLE_TO_GROUP.get(name, "metadata")
    tables_dir = tables_dir / group / name
    tables_dir.mkdir(parents=True, exist_ok=True)
    csv_path = tables_dir / f"{name}.csv"
    md_path = tables_dir / f"{name}.md"
    tex_path = tables_dir / f"{name}.tex"
    df.to_csv(csv_path, index=False)
    md_path.write_text(markdown_table(df), encoding="utf-8")
    try:
        tex_path.write_text(df.to_latex(index=False, escape=True), encoding="utf-8")
    except Exception as exc:  # pragma: no cover - optional presentation artifact
        tex_path.write_text(f"% LaTeX export failed: {exc}\n", encoding="utf-8")


def condition_summary(df: pd.DataFrame) -> pd.DataFrame:
    clean = df[df["condition"].astype(str) == "clean"]
    clean_success = int(clean["success"].sum())
    clean_total = len(clean)
    clean_rate = clean_success / clean_total
    records: list[dict[str, Any]] = []
    for condition in CONDITION_ORDER:
        subset = df[df["condition"].astype(str) == condition]
        successes = int(subset["success"].sum())
        total = len(subset)
        ci_low, ci_high = wilson(successes, total)
        rate = successes / total
        records.append(
            {
                "condition": condition,
                "n": total,
                "success": successes,
                "fail": total - successes,
                "success_rate": round(rate, 4),
                "wilson_ci_low": round(ci_low, 4),
                "wilson_ci_high": round(ci_high, 4),
                "risk_difference_vs_clean": round(rate - clean_rate, 4),
                "risk_ratio_vs_clean": round(safe_ratio(rate, clean_rate), 4),
                "odds_ratio_vs_clean": round(odds_ratio(successes, total, clean_success, clean_total), 4),
                "hidden_bug_fix_only_failures": int((subset["failure_category"] == "focal_failure").sum()),
                "regression_only_failures": int((subset["failure_category"] == "regression_failure").sum()),
                "hidden_bug_fix_and_regression_failures": int(
                    (subset["failure_category"] == "focal_and_regression_failure").sum()
                ),
                "uncategorized_scoring_failures": int(
                    (subset["failure_category"] == "uncategorized_oracle_fail").sum()
                ),
                "hidden_bug_fix_test_failures_total": int(subset["fail_to_pass_failed"].sum()),
                "previously_passing_test_failures_total": int(subset["pass_to_pass_failed"].sum()),
                "mean_total_duration_seconds": round(float(subset["total_duration_seconds"].mean()), 2),
                "median_total_duration_seconds": round(float(subset["total_duration_seconds"].median()), 2),
                "mean_total_tokens_including_cache": round(float(subset["total_tokens_including_cache"].mean()), 2),
                "median_total_tokens_including_cache": round(float(subset["total_tokens_including_cache"].median()), 2),
                "mean_edits_applied": round(float(subset["edits_applied"].mean()), 2),
                "mean_files_opened_before_first_edit": round(
                    float(subset["files_opened_before_first_edit"].mean()), 2
                ),
                "mean_exploration_efficiency": round(float(subset["exploration_efficiency"].mean()), 4),
            }
        )
    return pd.DataFrame(records)


def repo_summary(df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df.groupby(["repo", "repo_full"], observed=False)
        .agg(
            n=("success", "size"),
            success=("success", "sum"),
            fail=("success", lambda s: int((~s).sum())),
            hidden_bug_fix_test_failures_total=("fail_to_pass_failed", "sum"),
            previously_passing_test_failures_total=("pass_to_pass_failed", "sum"),
            mean_total_duration_seconds=("total_duration_seconds", "mean"),
            mean_total_tokens_including_cache=("total_tokens_including_cache", "mean"),
        )
        .reset_index()
    )
    grouped["success_rate"] = (grouped["success"] / grouped["n"]).round(4)
    for condition in CONDITION_ORDER:
        rates = (
            df[df["condition"].astype(str) == condition]
            .groupby("repo", observed=False)["success"]
            .mean()
            .rename(f"{condition}_success_rate")
        )
        grouped = grouped.merge(rates, on="repo", how="left")
    return grouped.round(4).sort_values(["success_rate", "repo"]).reset_index(drop=True)


def pr_summary(df: pd.DataFrame) -> pd.DataFrame:
    meta = load_candidate_metadata(df["candidate_id"].unique())
    grouped = (
        df.groupby(["repo", "repo_full", "candidate_id"], observed=False)
        .agg(
            n=("success", "size"),
            success=("success", "sum"),
            fail=("success", lambda s: int((~s).sum())),
            hidden_bug_fix_test_failures_total=("fail_to_pass_failed", "sum"),
            previously_passing_test_failures_total=("pass_to_pass_failed", "sum"),
            mean_total_duration_seconds=("total_duration_seconds", "mean"),
            mean_total_tokens_including_cache=("total_tokens_including_cache", "mean"),
        )
        .reset_index()
    )
    grouped["success_rate"] = (grouped["success"] / grouped["n"]).round(4)
    grouped = grouped.merge(meta, on="candidate_id", how="left")
    return grouped.round(4).sort_values(["success_rate", "repo", "candidate_id"]).reset_index(drop=True)


def load_candidate_metadata(candidate_ids: Iterable[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for candidate_id in sorted(set(candidate_ids)):
        path = ROOT / "candidates" / f"{candidate_id}.json"
        row: dict[str, Any] = {"candidate_id": candidate_id, "candidate_path": rel(path)}
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            row.update(
                {
                    "pr_number": data.get("pr_number"),
                    "title": data.get("title"),
                    "created_at": data.get("created_at") or data.get("merged_at"),
                    "files_changed": len(data.get("files_changed") or []),
                    "source_files": "; ".join(data.get("source_files") or []),
                    "test_files": "; ".join(data.get("test_files") or []),
                }
            )
        rows.append(row)
    return pd.DataFrame(rows)


def paired_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    clean = df[df["condition"].astype(str) == "clean"][
        ["repo", "repo_full", "candidate_id", "success", "failure_category"]
    ].rename(columns={"success": "clean_success", "failure_category": "clean_failure_category"})
    for condition in DEGRADED_CONDITIONS:
        degraded = df[df["condition"].astype(str) == condition][
            ["repo", "repo_full", "candidate_id", "success", "failure_category"]
        ].rename(columns={"success": "degraded_success", "failure_category": "degraded_failure_category"})
        merged = clean.merge(degraded, on=["repo", "repo_full", "candidate_id"], how="inner")
        rows.append(
            {
                "condition": condition,
                "pairs": len(merged),
                "both_success": int((merged["clean_success"] & merged["degraded_success"]).sum()),
                "clean_success_degraded_fail": int((merged["clean_success"] & ~merged["degraded_success"]).sum()),
                "clean_fail_degraded_success": int((~merged["clean_success"] & merged["degraded_success"]).sum()),
                "both_fail": int((~merged["clean_success"] & ~merged["degraded_success"]).sum()),
                "clean_pass_degraded_fail_rate": round(
                    float((merged["clean_success"] & ~merged["degraded_success"]).mean()), 4
                ),
                "net_success_shift_vs_clean": int(
                    (~merged["clean_success"] & merged["degraded_success"]).sum()
                    - (merged["clean_success"] & ~merged["degraded_success"]).sum()
                ),
            }
        )
    return pd.DataFrame(rows)


def paired_detail(df: pd.DataFrame) -> pd.DataFrame:
    clean = df[df["condition"].astype(str) == "clean"][
        ["repo", "repo_full", "candidate_id", "success", "failure_category"]
    ].rename(columns={"success": "clean_success", "failure_category": "clean_failure_category"})
    rows: list[pd.DataFrame] = []
    for condition in DEGRADED_CONDITIONS:
        degraded = df[df["condition"].astype(str) == condition][
            [
                "repo",
                "repo_full",
                "candidate_id",
                "success",
                "failure_category",
                "fail_to_pass_failed",
                "pass_to_pass_failed",
                "total_duration_seconds",
                "total_tokens_including_cache",
            ]
        ].rename(columns={"success": "degraded_success", "failure_category": "degraded_failure_category"})
        merged = clean.merge(degraded, on=["repo", "repo_full", "candidate_id"], how="inner")
        merged.insert(3, "condition", condition)
        merged = merged.rename(
            columns={
                "clean_failure_category": "clean_failure_mode",
                "degraded_failure_category": "degraded_failure_mode",
                "fail_to_pass_failed": "hidden_bug_fix_tests_failed",
                "pass_to_pass_failed": "previously_passing_tests_failed",
            }
        )
        merged["clean_failure_mode"] = merged["clean_failure_mode"].map(plain_failure_mode)
        merged["degraded_failure_mode"] = merged["degraded_failure_mode"].map(plain_failure_mode)
        rows.append(merged)
    return pd.concat(rows, ignore_index=True)


def clean_baseline_failures(df: pd.DataFrame) -> pd.DataFrame:
    rows = df[(df["condition"].astype(str) == "clean") & ~df["success"]][
        ["repo", "candidate_id", "failure_category", "fail_to_pass_failed", "pass_to_pass_failed"]
    ].rename(
        columns={
            "failure_category": "failure_mode",
            "fail_to_pass_failed": "hidden_bug_fix_tests_failed",
            "pass_to_pass_failed": "previously_passing_tests_failed",
        }
    )
    rows["failure_mode"] = rows["failure_mode"].map(plain_failure_mode)
    return rows.reset_index(drop=True)


def clean_pass_degraded_failures(paired: pd.DataFrame) -> pd.DataFrame:
    rows = paired[paired["clean_success"] & ~paired["degraded_success"]][
        [
            "repo",
            "candidate_id",
            "condition",
            "degraded_failure_mode",
            "hidden_bug_fix_tests_failed",
            "previously_passing_tests_failed",
            "total_duration_seconds",
            "total_tokens_including_cache",
        ]
    ].copy()
    return rows.reset_index(drop=True)


def failure_mode_summary(df: pd.DataFrame) -> pd.DataFrame:
    pivot = (
        df.groupby(["condition", "failure_category"], observed=False)
        .size()
        .reset_index(name="count")
        .sort_values(["condition", "failure_category"])
    )
    pivot["condition"] = pivot["condition"].astype(str)
    pivot["failure_category"] = pivot["failure_category"].map(plain_failure_mode)
    return pivot


def token_runtime_summary(df: pd.DataFrame) -> pd.DataFrame:
    metrics = [
        "total_duration_seconds",
        "agent_duration_seconds",
        "oracle_duration_seconds",
        "total_tokens_including_cache",
        "uncached_input_plus_output_tokens",
        "codex_input_tokens",
        "codex_cached_input_tokens",
        "codex_output_tokens",
    ]
    rows: list[dict[str, Any]] = []
    for condition, subset in df.groupby("condition", observed=False):
        row: dict[str, Any] = {"condition": str(condition), "n": len(subset)}
        for metric in metrics:
            row[f"{metric}_mean"] = round(float(subset[metric].mean()), 2)
            row[f"{metric}_median"] = round(float(subset[metric].median()), 2)
            row[f"{metric}_p75"] = round(float(subset[metric].quantile(0.75)), 2)
        rows.append(row)
    return pd.DataFrame(rows)


def leave_one_repo_out(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for omitted_repo in sorted(df["repo"].unique()):
        subset = df[df["repo"] != omitted_repo]
        clean = subset[subset["condition"].astype(str) == "clean"]
        clean_rate = float(clean["success"].mean())
        for condition in DEGRADED_CONDITIONS:
            degraded = subset[subset["condition"].astype(str) == condition]
            degraded_rate = float(degraded["success"].mean())
            rows.append(
                {
                    "omitted_repo": omitted_repo,
                    "condition": condition,
                    "clean_success_rate": round(clean_rate, 4),
                    "degraded_success_rate": round(degraded_rate, 4),
                    "risk_difference_vs_clean": round(degraded_rate - clean_rate, 4),
                }
            )
    return pd.DataFrame(rows)


def process_metric_summary(df: pd.DataFrame) -> pd.DataFrame:
    metrics = [
        "command_count_before_first_edit",
        "command_count_after_first_edit",
        "agent_message_count_before_first_edit",
        "agent_message_count_after_first_edit",
        "edit_event_count_after_first_edit",
        "validation_test_command_count",
        "validation_test_command_count_after_first_edit",
        "failed_validation_test_command_count",
        "failed_command_count",
        "edit_test_edit_loop_proxy_count",
        "failed_validation_followed_by_edit_count",
    ]
    available = [metric for metric in metrics if metric in df.columns]
    rows: list[dict[str, Any]] = []
    for condition, subset in df.groupby("condition", observed=False):
        row: dict[str, Any] = {"condition": str(condition), "n": len(subset)}
        for metric in available:
            row[f"{metric}_mean"] = round(float(subset[metric].mean()), 3)
            row[f"{metric}_median"] = round(float(subset[metric].median()), 3)
        rows.append(row)
    return pd.DataFrame(rows)


def process_correlations(df: pd.DataFrame) -> pd.DataFrame:
    metrics = [
        "files_opened_before_first_edit",
        "exploration_efficiency",
        "total_duration_seconds",
        "total_tokens_including_cache",
        "command_count_before_first_edit",
        "command_count_after_first_edit",
        "validation_test_command_count",
        "failed_validation_test_command_count",
        "failed_command_count",
        "edit_test_edit_loop_proxy_count",
    ]
    rows: list[dict[str, Any]] = []
    y = df["success"].astype(int)
    for metric in [m for m in metrics if m in df.columns]:
        x = pd.to_numeric(df[metric], errors="coerce")
        if x.notna().sum() < 3 or x.nunique(dropna=True) < 2:
            corr = float("nan")
        else:
            corr = float(x.corr(y))
        rows.append({"metric": metric, "pearson_corr_with_success": round(corr, 4)})
    return pd.DataFrame(rows)


def validation_summary(df: pd.DataFrame) -> pd.DataFrame:
    checks = [
        {
            "check": "Matrix row count",
            "expected": "150",
            "observed": str(len(df)),
            "passed": len(df) == 150,
            "notes": "One run per repo/candidate/condition.",
        },
        {
            "check": "Unique repositories",
            "expected": "10",
            "observed": str(df["repo"].nunique()),
            "passed": df["repo"].nunique() == 10,
            "notes": "",
        },
        {
            "check": "Unique historical PR tasks",
            "expected": "30",
            "observed": str(df["candidate_id"].nunique()),
            "passed": df["candidate_id"].nunique() == 30,
            "notes": "",
        },
        {
            "check": "Duplicate repo/candidate/condition rows",
            "expected": "0",
            "observed": str(int(df.duplicated(["repo", "candidate_id", "condition"]).sum())),
            "passed": int(df.duplicated(["repo", "candidate_id", "condition"]).sum()) == 0,
            "notes": "",
        },
        {
            "check": "Harness ERROR rows",
            "expected": "0",
            "observed": str(int(df["status"].eq("ERROR").sum())),
            "passed": int(df["status"].eq("ERROR").sum()) == 0,
            "notes": "Known invalid artifacts are excluded from the final matrix.",
        },
        {
            "check": "Token coverage",
            "expected": f"{len(df)}/{len(df)}",
            "observed": f"{int(df['total_tokens_including_cache'].notna().sum())}/{len(df)}",
            "passed": int(df["total_tokens_including_cache"].notna().sum()) == len(df),
            "notes": "Totals include cached input tokens where labeled.",
        },
        {
            "check": "Success/failure count",
            "expected": "101 SUCCESS / 49 FAIL",
            "observed": f"{int(df['success'].sum())} SUCCESS / {int((~df['success']).sum())} FAIL",
            "passed": int(df["success"].sum()) == 101 and int((~df["success"]).sum()) == 49,
            "notes": "",
        },
    ]
    if "agent_stdout_present" in df.columns:
        checks.append(
            {
                "check": "Process-log coverage",
                "expected": f"{len(df)}/{len(df)}",
                "observed": f"{int(df['agent_stdout_present'].sum())}/{len(df)}",
                "passed": int(df["agent_stdout_present"].sum()) == len(df),
                "notes": "Required for enriched process metrics.",
            }
        )
    return pd.DataFrame(checks)


def copy_source_data(df: pd.DataFrame) -> None:
    data_dir = ANALYSIS_DIR / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    source_csv = MATRIX_CSV if MATRIX_CSV.exists() else LEGACY_MATRIX_CSV
    source_json = MATRIX_JSON if MATRIX_JSON.exists() else LEGACY_MATRIX_JSON
    if source_csv.exists() and source_csv.resolve() != MATRIX_CSV.resolve():
        shutil.copy2(source_csv, MATRIX_CSV)
    if source_json.exists() and source_json.resolve() != MATRIX_JSON.resolve():
        shutil.copy2(source_json, MATRIX_JSON)
    df.to_csv(data_dir / "per_run_summary.csv", index=False)
    df.to_json(data_dir / "per_run_summary.json", orient="records", indent=2)


def clean_generated_tables() -> None:
    tables_dir = ANALYSIS_DIR / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)
    for group_dir in tables_dir.iterdir():
        if group_dir.is_dir():
            shutil.rmtree(group_dir)
    for pattern in ("*.csv", "*.md", "*.tex"):
        for path in tables_dir.glob(pattern):
            path.unlink()


def write_table_readmes() -> None:
    tables_dir = ANALYSIS_DIR / "tables"
    root_lines = [
        "# Tables",
        "",
        "Tables are grouped by purpose. Core tables are exported as `.csv`, `.md`, and `.tex`.",
        "",
        "Plain-language terms used here:",
        "- `Run`: one agent attempt on one historical PR under one codebase condition.",
        "- `Success`: hidden bug-fix tests passed and previously passing tests did not regress after applying the agent's non-test code changes.",
        "- `Hidden bug-fix tests`: tests added by the original PR that should pass after a correct repair.",
        "- `Previously passing tests`: existing tests that should keep passing. Failures here are regressions.",
        "- `Condition`: the codebase version shown to the agent, such as clean, naming-degraded, or tests-removed.",
        "",
    ]
    for group, meta in TABLE_GROUPS.items():
        root_lines.append(f"- `{group}/`: {meta['description']}")
    root_lines.append("- `figure_data/`: CSV data behind the generated figures.")
    (tables_dir / "README.md").write_text("\n".join(root_lines) + "\n", encoding="utf-8")

    for group, meta in TABLE_GROUPS.items():
        group_dir = tables_dir / group
        group_dir.mkdir(parents=True, exist_ok=True)
        table_names = sorted(path.name for path in group_dir.iterdir() if path.is_dir())
        lines = [f"# {meta['title']}", "", meta["description"], ""]
        for name in table_names:
            lines.append(f"- `{name}/`: `{name}.csv`, `{name}.md`, `{name}.tex`")
        (group_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def extract_changed_files(metrics_path: Path) -> list[str]:
    if not metrics_path.exists():
        return []
    data = json.loads(metrics_path.read_text(encoding="utf-8"))
    changed = data.get("changed_files")
    return changed if isinstance(changed, list) else []


def patch_stats(patch_path: Path) -> tuple[int, int, list[str]]:
    if not patch_path.exists():
        return 0, 0, []
    text = patch_path.read_text(encoding="utf-8", errors="replace")
    files = re.findall(r"^diff --git a/(.*?) b/", text, flags=re.MULTILINE)
    additions = sum(1 for line in text.splitlines() if line.startswith("+") and not line.startswith("+++"))
    deletions = sum(1 for line in text.splitlines() if line.startswith("-") and not line.startswith("---"))
    return additions, deletions, files


def output_tail(output_path: Path, max_lines: int = 6) -> str:
    if not output_path.exists():
        return ""
    lines = output_path.read_text(encoding="utf-8", errors="replace").splitlines()
    useful = [line.strip() for line in lines if line.strip()]
    text = " / ".join(useful[-max_lines:])
    for prefix in [str(ROOT.parent) + "/", str(ROOT) + "/"]:
        text = text.replace(prefix, "")
    return text[:600]


def first_commands(stdout_path: Path, max_commands: int = 4) -> str:
    if not stdout_path.exists():
        return ""
    commands: list[str] = []
    with stdout_path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            item = event.get("item") or {}
            if (
                event.get("type") == "item.completed"
                and isinstance(item, dict)
                and item.get("type") == "command_execution"
            ):
                command = item.get("command")
                command_text = " ".join(command) if isinstance(command, list) else str(command)
                commands.append(command_text.replace("\n", " ")[:140])
                if len(commands) >= max_commands:
                    break
    return " | ".join(commands)


def choose_audit_rows(df: pd.DataFrame) -> pd.DataFrame:
    keyed = {
        (record["repo"], record["candidate_id"], str(record["condition"])): record
        for record in df.to_dict(orient="records")
    }
    audit_records: list[dict[str, Any]] = []
    missing: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for audit_reason, repo, candidate_id, condition in AUDIT_CASES:
        key = (repo, candidate_id, condition)
        if key in seen:
            continue
        seen.add(key)
        record = keyed.get(key)
        if record is None:
            missing.append(key)
            continue
        record = dict(record)
        record["audit_reason"] = audit_reason
        audit_records.append(record)
    if missing:
        raise SystemExit(f"Configured audit rows missing from matrix: {missing}")

    rows: list[dict[str, Any]] = []
    for record in audit_records:
        result_path = ROOT / str(record["result_path"])
        metrics_path = ROOT / str(record["metrics_path"])
        run_root = result_path.parent
        patch_path = run_root / "logs/final_repo_diff.patch"
        oracle_path = run_root / "logs/post_run_test_output.txt"
        stdout_path = run_root / "logs/agent_stdout.log"
        additions, deletions, patch_files = patch_stats(patch_path)
        rows.append(
            {
                "audit_reason": record["audit_reason"],
                "repo": record["repo"],
                "candidate_id": record["candidate_id"],
                "condition": str(record["condition"]),
                "status": record["status"],
                "failure_mode": plain_failure_mode(str(record["failure_category"])),
                "hidden_bug_fix_tests_passed": f"{record['fail_to_pass_passed']}/{record['fail_to_pass_total']}",
                "previously_passing_tests_passed": f"{record['pass_to_pass_passed']}/{record['pass_to_pass_total']}",
                "changed_files_from_metrics": "; ".join(extract_changed_files(metrics_path)),
                "patch_files": "; ".join(patch_files[:8]),
                "patch_additions": additions,
                "patch_deletions": deletions,
                "result_path": rel(result_path),
                "metrics_path": rel(metrics_path),
                "patch_path": rel(patch_path),
                "oracle_output_path": rel(oracle_path),
                "agent_stdout_path": rel(stdout_path),
                "first_agent_commands": first_commands(stdout_path),
                "oracle_output_tail": output_tail(oracle_path),
                "fairness_read": fairness_read(record),
            }
        )
    return pd.DataFrame(rows)


def fairness_read(record: dict[str, Any]) -> str:
    condition = str(record["condition"])
    category = str(record["failure_category"])
    if record["status"] == "SUCCESS":
        return "Scoring-confirmed pass; hidden tests restored before scoring."
    if condition == "clean":
        return "Clean baseline failure; degraded-condition failures for this PR should not be attributed to degradation without paired comparison."
    if category == "regression_failure":
        return "Hidden bug-fix tests passed but previously passing tests regressed; fair signal for collateral-damage risk."
    if category == "focal_failure":
        return "Hidden bug-fix tests still failed; fair repair miss, but paired clean outcome must be checked before attributing it to the condition."
    if category == "focal_and_regression_failure":
        return "Both hidden bug-fix tests and previously passing tests failed; inspect patch/output before using as a causal example."
    return "Final scoring failed without hidden-bug-fix/regression counts; inspect manually before citing."


def write_docs(tables: dict[str, pd.DataFrame], df: pd.DataFrame) -> None:
    appendices_dir = ANALYSIS_DIR / "appendices"
    appendices_dir.mkdir(parents=True, exist_ok=True)

    condition = tables["condition_summary"]
    paired = tables["paired_clean_vs_degraded_summary"]
    repo = tables["repo_summary"]
    process = tables["rq2_process_metric_summary"]
    correlations = tables["rq2_process_correlations"]
    audit = tables["audited_run_table"]
    clean_failures = tables["clean_baseline_failures"]
    clean_pass_degraded_failures = tables["clean_pass_degraded_failures"]
    validation = tables["validation_summary"]
    failure_modes = tables["failure_mode_summary"]

    generated_figures = sorted(
        str(path.relative_to(ANALYSIS_DIR)) for path in (ANALYSIS_DIR / "figures").glob("*/*/*.png")
    )
    generated_tables = sorted(
        str(path.relative_to(ANALYSIS_DIR)) for path in (ANALYSIS_DIR / "tables").glob("*/*/*.csv")
    )

    clean_success = int(condition.loc[condition["condition"] == "clean", "success"].iloc[0])
    naming_success = int(condition.loc[condition["condition"] == "naming", "success"].iloc[0])
    remove_tests_success = int(condition.loc[condition["condition"] == "remove_tests", "success"].iloc[0])
    naming_regressions = int(
        condition.loc[condition["condition"] == "naming", "previously_passing_test_failures_total"].iloc[0]
    )
    process_brief = process[
        [
            "condition",
            "command_count_before_first_edit_mean",
            "command_count_after_first_edit_mean",
            "validation_test_command_count_mean",
            "failed_validation_test_command_count_mean",
            "edit_test_edit_loop_proxy_count_mean",
        ]
    ]

    readme = f"""# Final RQ Analysis

This folder is the final analysis bundle for the custom-repo LLM-J agent-readiness study.

## Read Order

1. `REPORT.md`: main result narrative for teammates.
2. `threats_to_validity.md`: limitations to keep attached to the result.
3. `claim_ledger.md`: claim boundaries and safer wording.
4. `appendices/README.md`: backup material for methods, audit details, and artifact locations.

The report is the main entry point. The appendices are for verification and detail.

## One-Minute Result

We ran Codex on 30 historical PR tasks across 10 Python repositories under five workspace conditions: clean, naming-degraded, type-hints removed, comments/docstrings removed, and visible tests removed.

The clearest result is naming. Naming solved `{naming_success}/30` runs, compared with clean at `{clean_success}/30`, and produced the largest regression burden in previously passing tests.

Removing visible tests had the weakest final-outcome impact in this matrix: `{remove_tests_success}/30` runs succeeded. That does not mean tests are unimportant; it means this experiment did not show a large final solve-rate drop from hiding visible tests while restoring hidden tests for scoring.

The readiness-tool conclusion is cautious: these data support empirically calibrated, narrower signals better than a broad checklist-style readiness score.

## Key Counts

- `{len(df)}` scored runs.
- `{df['repo'].nunique()}` repositories.
- `{df['candidate_id'].nunique()}` historical PR tasks.
- `{int(df['success'].sum())}` successes and `{int((~df['success']).sum())}` failures.
- `{int(df['status'].eq('ERROR').sum())}` harness errors in the final matrix.
- `{int(df['total_tokens_including_cache'].notna().sum())}/{len(df)}` token coverage.
- Manual audit manifest: `{len(audit)}` runs.

## Reproduce The Final Analysis

Run from the repository root:

```bash
python final_rq_analysis/scripts/enrich_rq2_metrics.py
python final_rq_analysis/scripts/build_analysis_tables.py
python final_rq_analysis/scripts/build_figures.py
python -m py_compile final_rq_analysis/scripts/*.py
```

These commands rebuild analysis outputs only. They do not collect new data or run new Stage 5 agent tasks.

## Folder Map

- `data/`: committed source matrix copy and generated analysis matrices.
- `tables/`: exact values behind the report, grouped by purpose.
- `figures/`: PNG/PDF/SVG exports, one folder per figure.
- `scripts/`: reproducible analysis builders.
- `appendices/`: methods, detailed results, audit notes, and data manifest.

Raw run directories and worktrees are intentionally not copied here.
"""
    (ANALYSIS_DIR / "README.md").write_text(readme, encoding="utf-8")

    report = f"""# Custom-Repo Agent Readiness Report

This is the main report for the custom-repo LLM-J readiness study.

## Short Answer

We tested whether changing specific codebase properties changed Codex's ability to solve real historical Python PR tasks.

The clearest result is naming. When meaningful names were replaced with generic names, Codex was much more likely to fail tasks it could solve cleanly. Naming solved `{naming_success}/30` runs, compared with clean at `{clean_success}/30`, and it produced `{naming_regressions}` failed previously passing tests.

The other conditions were weaker as final-outcome signals. Type hints and comments/docstrings had the same aggregate success count as clean, but their failures were shaped differently. Removing visible tests had the weakest final-outcome impact here.

The process evidence is useful but should stay modest: different degradations changed failure shape, validation behavior, token/runtime burden, and regression risk in different ways. That supports a multi-dimensional view, but it does not prove a complete readiness model.

The readiness-tool result is cautious: these data do not justify a broad all-purpose readiness score. A readiness checklist needs calibration against actual agent outcomes.

## Experiment Setup

Each run used one historical pull request from one of 10 Python repositories. We checked out the code before the PR and asked Codex to recreate the fix under one workspace condition:

| Condition | What Codex saw |
| --- | --- |
| `clean` | Original historical codebase. |
| `naming` | Meaningful names were replaced with generic names. |
| `type_hints` | Python type annotations were removed. |
| `comments_docstrings` | Comments and docstrings were removed. |
| `remove_tests` | Visible tests were removed while Codex worked. Hidden scoring tests were restored for evaluation. |

The remove-tests condition is easy to misread. It changed what Codex could see while working; it did not remove the final scoring tests.

## Dataset

- `{len(df)}` total runs.
- `{df['candidate_id'].nunique()}` historical PR tasks.
- `{df['repo'].nunique()}` repositories.
- 5 conditions per task.
- `{int(df['success'].sum())}` successes and `{int((~df['success']).sum())}` failures.
- `0` harness errors in the final matrix.

## How Scoring Worked

After Codex finished, the harness replayed only the agent's non-test code changes into a fresh scoring workspace. It then restored the hidden tests from the original PR and ran both:

- **Hidden bug-fix tests**: tests added by the original PR that should pass after a correct fix.
- **Previously passing tests**: tests that should keep passing. Failures here are regressions.

A run succeeded only if it fixed the intended behavior and did not break previously passing tests.

## Terms You Need

- **Run**: one Codex attempt on one historical PR under one condition.
- **Same-task comparison**: compare the same PR under clean and degraded conditions.
- **Clean-pass / degraded-fail**: clean passed but degraded failed. This is the strongest evidence that the degradation hurt Codex.
- **Clean baseline failure**: clean failed too. If degraded also failed, treat the task as hard before attributing the failure to the degradation.
- **Regression**: previously passing tests failed after the agent patch.
- **Process metrics**: recoverable Codex log counts such as command count, validation command count, and edit/test/edit loops. They are not timing measurements.

## RQ1: What Hurt Final Repair Success?

Naming quality was the strongest final-outcome signal.

{markdown_table(condition[['condition', 'n', 'success', 'fail', 'success_rate', 'hidden_bug_fix_only_failures', 'regression_only_failures', 'hidden_bug_fix_and_regression_failures', 'previously_passing_test_failures_total']])}

The paired same-task view is the safest way to interpret causality:

{markdown_table(paired)}

Naming has the largest clean-pass / degraded-fail count: 8 of 30 same-task comparisons. Type hints had 2, comments/docstrings had 3, and remove-tests had 1.

Clean baseline failures matter. There were 9 clean failures:

{markdown_table(clean_failures)}

Do not count degraded failures on those same PRs as strong degradation-caused evidence unless the paired clean/degraded pattern supports that read.

## RQ2: Did Degradations Change How Codex Worked?

Yes, but this is supporting evidence rather than the headline result.

Naming combined lower solve rate, higher token/runtime burden, and regression risk. Type-hints and comments/docstrings mostly looked like hidden-bug-fix repair misses rather than broad regressions. Remove-tests had weak final-outcome impact, but it still changed validation and rework proxies.

Compact process-metric summary:

{markdown_table(process_brief)}

The full process table and correlations are in `appendices/detailed_results.md`. The best simple takeaway is: final pass/fail parity does not mean process parity. A degraded run can still pass while being more expensive, more scattered, or more validation-heavy.

Important caveat: current Codex logs do not support reliable timing claims, time-to-first-edit claims, or token-before-first-edit claims.

## RQ3: Should We Build A Broad Readiness Tool?

Not from these results alone.

The evidence challenges broad checklist-style readiness claims unless the checklist is calibrated against actual agent outcomes. Naming was the clearest repeated final-outcome signal. Other dimensions were weaker or visible mainly through process and failure shape.

This does not mean Factory-style readiness or engineering hygiene is wrong. It means this study does not show that a broad checklist reliably predicts Codex repair success on these tasks.

The better takeaway is:

> A calibrated, evidence-backed readiness signal is safer than a broad unvalidated readiness score.

## Best Evidence To Use

- `tables/overview/condition_summary/condition_summary.csv`: best single numeric summary.
- `tables/outcomes/paired_clean_vs_degraded_summary/paired_clean_vs_degraded_summary.csv`: safest same-task comparison.
- `tables/outcomes/clean_pass_degraded_failures/clean_pass_degraded_failures.csv`: strongest degradation-associated examples.
- `tables/failure_modes/failure_mode_summary/failure_mode_summary.csv`: failure-shape split.
- `figures/outcomes/success_rate_by_condition/success_rate_by_condition.png`: headline success-rate figure.
- `figures/outcomes/paired_degraded_vs_clean_outcome_shifts/paired_degraded_vs_clean_outcome_shifts.png`: paired outcome shifts.
- `claim_ledger.md`: wording guardrails.
- `threats_to_validity.md`: limitations.

## Safer Wording

| Avoid saying | Safer wording |
| --- | --- |
| "Naming causes all failures." | "Naming is the strongest measured negative condition in this matrix." |
| "Type hints do not matter." | "Type-hints removal did not reduce aggregate success here; this does not prove type hints never matter." |
| "Tests do not matter." | "Removing visible tests had weak final-outcome impact here, while hidden tests were still restored for scoring." |
| "RQ2 proves readiness is multi-dimensional." | "RQ2 provides process and failure-shape evidence that degradations affect agents differently." |
| "Factory is wrong." | "Checklist-style readiness needs empirical calibration against agent outcomes." |

## Bottom Line

For these custom historical PR tasks, naming quality was the clearest harmful codebase property for Codex. Other tested dimensions changed failure shape and process behavior more than final solve rate. The result supports careful, outcome-calibrated readiness claims, not a broad readiness score yet.
"""
    (ANALYSIS_DIR / "REPORT.md").write_text(report, encoding="utf-8")

    claim_ledger = """# Claim Ledger

This is the wording guardrail for the final analysis. Use it when writing slides, report prose, or discussion notes.

## Strong Evidence

| Claim | Evidence | Safer wording |
| --- | --- | --- |
| Naming is the strongest negative condition in the final matrix. | Naming has the lowest success rate (`14/30`), the largest clean-pass/degraded-fail count (`8/30`), and the largest regression burden. | Naming is the strongest measured negative condition in this corpus. |
| The final matrix is complete and internally valid. | 150 rows, no duplicate `(repo, candidate_id, condition)` rows, 0 harness errors, and 150/150 token coverage. | The final consolidated matrix passes deterministic integrity checks. |
| Clean baseline failures must be separated from degradation-associated failures. | 9 clean failures are present. Paired comparisons identify which degraded failures occurred after clean success. | A degraded failure is strongest evidence only when the same PR passed clean. |

## Suggestive Evidence

| Claim | Evidence | Safer wording |
| --- | --- | --- |
| Readiness appears multi-dimensional. | Conditions differ in failure shape, regression burden, process counts, runtime, and token use. | The process and failure-shape evidence supports a multi-dimensional framing. |
| Type hints and comments/docstrings affect comprehension/repair shape more than aggregate success. | Aggregate success matches clean, but hidden-bug-fix miss counts differ. | These conditions were more visible in failure shape than in final solve rate. |
| Remove-tests affects validation/rework more than final outcome. | Remove-tests has `24/30` successes but distinct process/rework proxies. | Removing visible tests had weak final-outcome impact here, but may still affect process. |

## Low-Confidence Or Caveated

| Claim | Why caveated | Safer wording |
| --- | --- | --- |
| Type hints do not matter. | One corpus, one agent/harness family, one run per task/condition, and selected Python task surfaces. | Type-hints removal was not an aggregate outcome-damaging condition in this matrix. |
| Comments/docstrings do not matter. | Same aggregate success as clean does not mean same process or same task difficulty. | Comments/docstrings removal was not aggregate outcome-damaging here, but changed failure shape. |
| Lower token/runtime means a condition helped. | Shorter failed paths can use fewer tokens. | Token/runtime shifts describe cost, not necessarily benefit. |

## Not Supported

| Claim to avoid | Why not supported |
| --- | --- |
| All degraded failures were caused by degradation. | Some tasks failed clean. |
| Factory-style readiness is wrong. | Static readiness tools were not run on these repos. |
| RQ2 proves a complete readiness model. | Process metrics are coarse event-count proxies with no reliable timestamps or phase-token split. |
| This generalizes to all coding agents. | The final matrix uses one Codex CLI harness family. |
"""
    (ANALYSIS_DIR / "claim_ledger.md").write_text(claim_ledger, encoding="utf-8")

    threats = """# Threats To Validity / Limitations

Keep this close to any report or slide deck that uses the custom-repo results. The strongest result is naming, but the experiment is still bounded.

## Experimental Scope

- **Single agent/harness family**: results are Codex-specific and should not be generalized to all coding agents without replication.
- **Limited replications**: the final matrix has one run per `(repo, historical PR, condition)`, so agent stochasticity is under-sampled.
- **Curated repos and PRs**: tasks were selected for feasibility, testability, and relevance. This is not a random sample of all software work.
- **Python-only corpus**: all final repos are Python projects.

## Scoring And Interpretation

- **Same-task comparison is required**: a degraded failure is strongest evidence when the clean run on the same PR passed.
- **Clean baseline failures**: 9 runs failed clean. Degraded failures on those PRs are not strong degradation-caused evidence by themselves.
- **Regression burden**: previously passing test failures are real damage, but they can appear alongside hidden-bug-fix misses or baseline-hard tasks.
- **Scoring replay assumptions**: hidden bug-fix and previously passing test counts are only as reliable as the historical test reconstruction and replay.
- **Remove-tests condition**: visible tests were removed while Codex worked, but hidden scoring tests were restored for evaluation.

## Condition-Specific Limits

- **Naming has the strongest evidence**: naming is supported by aggregate outcomes, paired outcomes, failure shape, and manual audit examples.
- **Type hints is not disproven**: type-hints removal did not hurt aggregate success here, but that does not prove type hints never matter.
- **Comments/docstrings is mostly failure-shape evidence**: it did not reduce aggregate success, but it changed the kind of misses observed.
- **Remove-tests is mostly process evidence**: it had weak final-outcome impact in this matrix, but it may still affect validation behavior.

## Process-Metric Limits

- **No reliable timing claims**: preserved Codex logs do not provide reliable per-event timestamps.
- **No phase-token claims**: logs do not expose tokens before versus after first edit.
- **Coarse metrics**: process metrics are recoverable action counts, not a full model of agent cognition.
- **Token interpretation**: total token usage includes cached input tokens where labeled; lower token use does not automatically mean a condition helped.

## Environment And Reproducibility Limits

- **Historical dependency reconstruction is hard**: repo profiles and container-backed probes reduce risk but cannot eliminate host/environment effects.
- **Some execution depended on host Codex subscription behavior**: invalid auth artifacts were excluded from the final matrix.
- **Known exclusions**: `pydantic-settings_pr_788 naming` and invalid `uvicorn` auth attempts were excluded for matrix integrity.
- **Raw artifacts remain local**: the GitHub-ready bundle contains lightweight exports and references, not copied worktrees or full run directories.

## RQ3 Limits

- **Static readiness tools were not run**: Factory-style comparison is documentary and conceptual, not an empirical head-to-head.
- **No broad readiness-score calibration yet**: these data support calibrated, outcome-backed claims better than a broad checklist score.
- **Engineering hygiene can still matter**: weak outcome signal for a tested dimension does not mean the dimension is unimportant in every workflow.
"""
    (ANALYSIS_DIR / "threats_to_validity.md").write_text(threats, encoding="utf-8")

    appendices_readme = """# Appendices

These files are backup material for verifying specific claims, inspecting row-level examples, or understanding the data/artifact layout.

Recommended order:

1. `detailed_results.md`: expanded RQ1/RQ2/RQ3 notes and key tables.
2. `evidence_and_audit.md`: manual-audit scope, validation checks, and artifact caveats.
3. `methods_data_manifest.md`: terminology, method details, data sources, generated tables, and generated figures.

The main story lives in `../REPORT.md`.
"""
    (appendices_dir / "README.md").write_text(appendices_readme, encoding="utf-8")

    detailed_results = f"""# Detailed Results Appendix

This appendix preserves the expanded RQ notes and row-level examples behind the main report.

## RQ1 Detailed Notes

RQ1 asks which codebase properties mattered most for Codex final performance.

Naming is the strongest measured outcome signal. It solved `{naming_success}/30` runs, compared with clean at `{clean_success}/30`, and has the largest regression burden.

{markdown_table(condition)}

## Paired Same-Task Read

{markdown_table(paired)}

The clean-pass / degraded-fail rows are the strongest degradation-associated examples:

{markdown_table(clean_pass_degraded_failures)}

## Repo And PR Heterogeneity

Repo difficulty is substantial. `pip-tools`, `pydantic-settings`, and `copier` contribute many hard runs, while `marshmallow` and `structlog` are mostly solved.

{markdown_table(repo[['repo', 'success', 'n', 'success_rate', 'clean_success_rate', 'naming_success_rate', 'type_hints_success_rate', 'comments_docstrings_success_rate', 'remove_tests_success_rate']])}

## Failure Modes

{markdown_table(failure_modes)}

Naming has the broadest failure shape: hidden-bug-fix-only failures, regression-only failures, and combined hidden-bug-fix + regression failures. Type hints and comments/docstrings mostly look like hidden-bug-fix repair misses. Remove-tests failures are fewer by final outcome.

## RQ2 Detailed Notes

RQ2 asks whether readiness appears multi-dimensional in process behavior. Treat this as supporting evidence, not the headline result.

{markdown_table(process)}

{markdown_table(correlations)}

Unavailable from current logs: exact timestamps, reliable time to first edit, tokens before first edit, post-edit token usage, and phase-specific token split.

## RQ3 Detailed Notes

The current custom-repo results do not justify a broad general-purpose readiness scoring tool. Naming was the dominant repeated outcome signal. Other dimensions were weaker or visible mainly in process/failure shape.

Future work should run static readiness criteria on these repos, test correlation with actual agent outcomes, add feedback-loop/build/CI/environment-doc degradations, and validate any score against held-out agent performance.
"""
    (appendices_dir / "detailed_results.md").write_text(detailed_results, encoding="utf-8")

    evidence = f"""# Evidence And Audit Appendix

This appendix explains what was checked and how much confidence to put in the exported scoring fields.

## Manual Audit Scope

This audit is not a full reread of all 150 runs. It is a stratified pass over high-risk and high-interpretation rows.

- All 9 clean failures.
- 9 naming failures split by regression-only, hidden-bug-fix-only, and combined failure shapes.
- 5 remove-tests examples across successes and failures.
- Strong interpretation examples from `copier`, `pydantic-settings`, `pip-tools`, and `httpx`, plus additional successful-run sanity checks from `click` and `structlog`.
- Excluded invalid artifacts: `pydantic-settings_pr_788 naming` and invalid `uvicorn` auth attempts.

The exact manifest is in `../tables/audit_and_manifests/audited_run_table/audited_run_table.csv`.

## What Was Checked

For each audited run, the manual pass inspected or summarized:

- `result.json`
- `metrics.json`
- `logs/final_repo_diff.patch`
- `logs/post_run_test_output.txt`
- the opening event sequence in `logs/agent_stdout.log`

## Audit Manifest

{markdown_table(audit[['audit_reason', 'repo', 'candidate_id', 'condition', 'status', 'failure_mode', 'result_path']], max_rows=30)}

## Validation Summary

{markdown_table(validation)}

## Audit Findings

The audited outcomes are fair scoring outcomes after excluding known invalid artifacts. The main interpretation guardrail is clean-baseline difficulty: do not count every degraded failure as degradation-caused.

The strongest examples are clean-pass / degraded-fail pairs, especially naming rows where hidden bug-fix tests passed but previously passing tests regressed.
"""
    (appendices_dir / "evidence_and_audit.md").write_text(evidence, encoding="utf-8")

    sources_md = "\n".join(f"- [{source.title}]({source.url}): {source.note}" for source in FACTORY_SOURCES)
    methods_manifest = f"""# Methods And Data Manifest Appendix

This appendix keeps terminology, method details, and artifact locations out of the main report.

## Glossary

| Term | Plain-language meaning |
| --- | --- |
| Run | One Codex attempt on one historical PR under one condition. |
| Condition | The codebase version shown to Codex: clean, naming-degraded, type-hints removed, comments/docstrings removed, or visible tests removed. |
| Historical PR | A real pull request from the repo history. We check out the code before the PR and ask Codex to recreate the fix. |
| Hidden bug-fix tests | Tests added by the original PR that should pass after a correct fix. Benchmark term: FAIL_TO_PASS. |
| Previously passing tests | Tests that should keep passing. Benchmark term: PASS_TO_PASS. |
| Same-task comparison | Compare clean and degraded outcomes for the same historical PR. |
| Clean-pass / degraded-fail | Clean passed but degraded failed. Strongest degradation-associated outcome evidence. |
| Clean baseline failure | Clean failed too. Do not treat degraded failure as degradation-caused without paired support. |
| Regression | Previously passing tests failed after the agent patch. |
| Process metrics | Recovered Codex event-log counts such as commands and validation commands. |

## Pipeline Summary

The custom-repo lane uses historical GitHub PRs as controlled agent tasks. Candidate scraping collects merged PR metadata, diffs, source files, and test files. Stage 1 uses an LLM judge to shortlist plausible tasks. Stage 2 verifies candidates mechanically with hidden bug-fix tests: base plus test patch should fail, and base plus test patch plus gold source patch should pass.

Stage 4 materializes one isolated workspace per task/condition and applies exactly one degradation. Stage 5 runs Codex CLI under a single-submission contract. Final scoring replay applies only non-test agent changes in a fresh workspace, restores hidden tests, and runs the repo-profile-shaped pytest command. Stage 6 parses preserved logs and metrics. Stage 7 builds the consolidated matrix used here.

## Source Of Truth

- Consolidated matrix CSV: `{rel(MATRIX_CSV)}`
- Consolidated matrix JSON: `{rel(MATRIX_JSON)}`
- Enriched process-metrics matrix: `data/enriched_matrix_with_process_metrics.csv`

`comparison_slices/` contains raw/provenance material locally, but it is intentionally excluded from the GitHub read path because it is large.

## Candidate And Admission Artifacts

- Candidate JSON files: `candidates/*_pr_*.json`
- Stage 1 selected manifests: `results/*_selected_prs.json`
- Stage 2 verified manifests: `deep_results/*_verified_manifest.json`
- Experiment packets: `packets/*_experiment_packet.json`
- Run plans: `run_plans/*_run_plan.json`
- Repo profiles: `repo_profiles/*.json`

## Raw Artifact Locations

Raw run directories are local/provenance artifacts and are not copied into `final_rq_analysis/`.

Valid runs follow:

```text
runs/{{repo}}/{{candidate_id}}/codex_cli/{{condition}}/rep_1/
comparison_slices/*/runs/{{repo}}/{{candidate_id}}/codex_cli/{{condition}}/rep_1/
```

Each run root should contain `result.json`, `metrics.json`, `logs/agent_stdout.log`, `logs/agent_stderr.log`, `logs/final_repo_diff.patch`, and `logs/post_run_test_output.txt`.

## Factory-Style Readiness Context

Sources accessed during analysis:

{sources_md}

This study does not show Factory-style readiness is wrong. It shows broad checklist-style readiness needs empirical calibration against actual repair outcomes.

## Generated Tables

{chr(10).join(f'- `{name}`' for name in generated_tables)}

## Generated Figures

{chr(10).join(f'- `{name}`' for name in generated_figures) if generated_figures else '- Run `build_figures.py` to generate figures.'}
"""
    (appendices_dir / "methods_data_manifest.md").write_text(methods_manifest, encoding="utf-8")


def build_all() -> None:
    df = load_matrix()
    validate_matrix(df)
    clean_generated_tables()
    copy_source_data(df)

    tables = {
        "condition_summary": condition_summary(df),
        "repo_summary": repo_summary(df),
        "pr_summary": pr_summary(df),
        "paired_clean_vs_degraded_summary": paired_summary(df),
        "paired_clean_vs_degraded_detail": paired_detail(df),
        "failure_mode_summary": failure_mode_summary(df),
        "token_runtime_summary": token_runtime_summary(df),
        "leave_one_repo_out_condition_effects": leave_one_repo_out(df),
        "rq2_process_metric_summary": process_metric_summary(df),
        "rq2_process_correlations": process_correlations(df),
        "audited_run_table": choose_audit_rows(df),
        "validation_summary": validation_summary(df),
    }
    tables["clean_baseline_failures"] = clean_baseline_failures(df)
    tables["clean_pass_degraded_failures"] = clean_pass_degraded_failures(
        tables["paired_clean_vs_degraded_detail"]
    )
    for name, table in tables.items():
        write_table(table, name)

    pr_meta = load_candidate_metadata(df["candidate_id"].unique())
    write_table(pr_meta, "per_pr_metadata_summary")
    pr_meta.to_csv(ANALYSIS_DIR / "data/per_pr_metadata_summary.csv", index=False)
    tables["per_pr_metadata_summary"] = pr_meta

    tables["audited_run_table"].to_csv(ANALYSIS_DIR / "data/audit_sample_manifest.csv", index=False)
    write_table_readmes()
    write_docs(tables, df)

    print("Validated final matrix: 150 rows, no duplicates, 0 harness errors, full token coverage")
    print(f"Wrote tables/docs under {ANALYSIS_DIR}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    build_all()


if __name__ == "__main__":
    main()
