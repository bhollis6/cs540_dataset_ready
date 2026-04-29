from __future__ import annotations

from pathlib import Path

import pandas as pd

from common import (
    DATA_DIR,
    ROOT,
    TABLE_DIR,
    comparison_path,
    enriched_rq1,
    ensure_dirs,
    read_json,
    repo_relative,
    resolve_artifact_path,
    write_csv,
    write_markdown_table,
)


def category_map(df: pd.DataFrame) -> dict[str, set[str]]:
    return {
        "clean_pass_degraded_fail": set(df.loc[df["clean_success_degraded_failure"], "comparison_file"]),
        "regression_test_damage": set(df.loc[df["pass_to_pass_damage"], "comparison_file"]),
        "top_12_absolute_token_deltas": set(
            df.reindex(df["total_tokens_corrected_delta"].abs().sort_values(ascending=False).index)
            .head(12)["comparison_file"]
        ),
        "top_8_degraded_cheaper": set(
            df[df["total_tokens_corrected_delta"] < 0]
            .sort_values("total_tokens_corrected_delta")
            .head(8)["comparison_file"]
        ),
        "remove_tests_patch_target_shift": set(
            df[
                (df["condition"] == "remove_tests")
                & (df["degraded_only_changed_file_count"] > 0)
            ]["comparison_file"]
        ),
        "low_or_zero_type_hints_surface": set(
            df[(df["condition"] == "type_hints") & (df["annotation_nodes"].fillna(0) <= 1)][
                "comparison_file"
            ]
        ),
        "clean_already_failed": set(df.loc[df["baseline_hard"], "comparison_file"]),
        "astropy_build_compat_sensitive": set(
            df.loc[df["repo"] == "astropy/astropy", "comparison_file"]
        ),
    }


def agent_log_path(row: pd.Series, side: str) -> Path:
    condition = "clean" if side == "clean" else str(row["condition"])
    return (
        ROOT
        / "runs"
        / str(row["instance_id"])
        / "codex-cli"
        / condition
        / f"rep_{int(row['replication_index'])}"
        / "logs"
        / "agent_stdout.jsonl"
    )


def audit_verdict(row: pd.Series, categories: list[str]) -> tuple[str, str]:
    if row["clean_success_degraded_failure"]:
        return (
            "Valid paired outcome transition",
            "Clean solved the official task and degraded did not; count as degradation-associated outcome evidence.",
        )
    if row["pass_to_pass_damage"] and row["baseline_hard"]:
        return (
            "Valid regression damage, not target transition",
            "Clean already failed the bug-fix target; only the additional regression-test failures should be interpreted as damage.",
        )
    if row["pass_to_pass_damage"]:
        return (
            "Valid regression damage",
            "Target outcome may be stable or failed for another reason, but degraded introduced extra previously-passing test failures.",
        )
    if "low_or_zero_type_hints_surface" in categories:
        return (
            "Valid row with weak treatment",
            "The run is scoreable, but the type-hints degradation had little or no annotation surface to remove.",
        )
    if "clean_already_failed" in categories:
        return (
            "Clean already failed; do not count as degradation-caused target failure",
            "Clean already failed. Use this row for cost/process evidence only unless regression damage is present.",
        )
    if "remove_tests_patch_target_shift" in categories:
        return (
            "Valid process/patch-shape case",
            "Official oracle restored tests for scoring; changed visible patch target is a strategy/process signal.",
        )
    return (
        "Valid supporting process/cost case",
        "No official outcome damage; use for process, token, or patch-shape interpretation.",
    )


def main() -> None:
    ensure_dirs()
    df = enriched_rq1()
    categories = category_map(df)
    audit_files = sorted(set().union(*categories.values()))
    category_by_file = {
        comparison_file: sorted(
            category for category, files in categories.items() if comparison_file in files
        )
        for comparison_file in audit_files
    }
    audit_df = df[df["comparison_file"].isin(audit_files)].copy()
    rows: list[dict[str, object]] = []
    for _, row in audit_df.sort_values(["repo", "instance_id", "condition"]).iterrows():
        comparison = comparison_path(str(row["comparison_file"]))
        packet = read_json(comparison)
        assert isinstance(packet, dict)
        oracle_logs = packet.get("oracle_logs", {})
        clean_oracle = resolve_artifact_path(oracle_logs.get("clean", ""))
        degraded_oracle = resolve_artifact_path(oracle_logs.get("degraded", ""))
        clean_agent = agent_log_path(row, "clean")
        degraded_agent = agent_log_path(row, "degraded")
        cats = category_by_file[str(row["comparison_file"])]
        verdict, notes = audit_verdict(row, cats)
        rows.append(
            {
                "repo": row["repo"],
                "instance_id": row["instance_id"],
                "condition": row["condition"],
                "replication_index": row["replication_index"],
                "audit_categories": "|".join(cats),
                "clean_success": row["clean_success"],
                "degraded_success": row["degraded_success"],
                "clean_target_failed_tests": row["clean_fail_to_pass_failed_count"],
                "degraded_target_failed_tests": row["degraded_fail_to_pass_failed_count"],
                "clean_regression_failed_tests": row["clean_pass_to_pass_failed_count"],
                "degraded_regression_failed_tests": row["degraded_pass_to_pass_failed_count"],
                "token_delta": row["total_tokens_corrected_delta"],
                "changed_file_delta": row["changed_file_count_delta"],
                "comparison_json_exists": comparison.exists(),
                "clean_oracle_log_exists": clean_oracle.exists(),
                "degraded_oracle_log_exists": degraded_oracle.exists(),
                "clean_agent_log_exists": clean_agent.exists(),
                "degraded_agent_log_exists": degraded_agent.exists(),
                "comparison_json_path": repo_relative(comparison),
                "clean_oracle_log_path": repo_relative(clean_oracle),
                "degraded_oracle_log_path": repo_relative(degraded_oracle),
                "clean_agent_log_path": repo_relative(clean_agent),
                "degraded_agent_log_path": repo_relative(degraded_agent),
                "audit_verdict": verdict,
                "audit_notes": notes,
            }
        )
    out = pd.DataFrame(rows)
    write_csv(out, DATA_DIR / "manual_audit_scope.csv")
    write_csv(out, TABLE_DIR / "manual_audit_scope.csv")
    write_markdown_table(out, TABLE_DIR / "manual_audit_scope.md")
    display_names = {
        "clean_pass_degraded_fail": "Clean passed, degraded failed",
        "regression_test_damage": "Regression-test damage",
        "top_12_absolute_token_deltas": "Top 12 absolute token deltas",
        "top_8_degraded_cheaper": "Top 8 degraded-cheaper cases",
        "remove_tests_patch_target_shift": "Remove-tests patch-target shift",
        "low_or_zero_type_hints_surface": "Low/zero type-hints surface",
        "clean_already_failed": "Clean already failed",
        "astropy_build_compat_sensitive": "Astropy build-compatibility-sensitive",
    }
    summary = pd.DataFrame(
        [
            {
                "audit_bucket": display_names.get(category, category),
                "unique_comparisons": len(files),
                "individual_runs": len(files) * 2,
            }
            for category, files in categories.items()
        ]
        + [
            {
                "audit_bucket": "Deduplicated total",
                "unique_comparisons": len(audit_files),
                "individual_runs": len(audit_files) * 2,
            }
        ]
    )
    write_csv(summary, DATA_DIR / "manual_audit_scope_summary.csv")
    write_csv(summary, TABLE_DIR / "manual_audit_scope_summary.csv")
    write_markdown_table(summary, TABLE_DIR / "manual_audit_scope_summary.md")
    missing = out[
        ~(
            out["comparison_json_exists"]
            & out["clean_oracle_log_exists"]
            & out["degraded_oracle_log_exists"]
            & out["clean_agent_log_exists"]
            & out["degraded_agent_log_exists"]
        )
    ]
    if not missing.empty:
        raise SystemExit(f"Audit artifact check failed for {len(missing)} comparisons")
    print(f"Manual audit scope: {len(audit_files)} comparisons / {len(audit_files) * 2} runs.")


if __name__ == "__main__":
    main()
