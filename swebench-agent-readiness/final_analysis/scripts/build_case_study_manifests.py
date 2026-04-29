from __future__ import annotations

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


def add_case_category(df: pd.DataFrame, category: str) -> pd.DataFrame:
    out = df.copy()
    out["case_category"] = category
    return out


def artifact_status(row: pd.Series) -> dict[str, object]:
    path = comparison_path(str(row["comparison_file"]))
    status: dict[str, object] = {
        "comparison_json_path": repo_relative(path),
        "comparison_json_exists": path.exists(),
        "clean_oracle_log_exists": False,
        "degraded_oracle_log_exists": False,
        "clean_agent_log_exists": False,
        "degraded_agent_log_exists": False,
    }
    if not path.exists():
        return status
    packet = read_json(path)
    if not isinstance(packet, dict):
        return status
    oracle_logs = packet.get("oracle_logs", {})
    for side in ["clean", "degraded"]:
        oracle_path = resolve_artifact_path(oracle_logs.get(side, ""))
        status[f"{side}_oracle_log_exists"] = oracle_path.exists()
    for side, condition in [("clean", "clean"), ("degraded", row["condition"])]:
        agent_path = (
            ROOT
            / "runs"
            / str(row["instance_id"])
            / "codex-cli"
            / str(condition)
            / f"rep_{int(row['replication_index'])}"
            / "logs"
            / "agent_stdout.jsonl"
        )
        status[f"{side}_agent_log_exists"] = agent_path.exists()
    return status


def interpretation(row: pd.Series) -> str:
    if row["clean_success_degraded_failure"]:
        return "Official clean pass and degraded failure; count as degradation-associated outcome transition in the paired design."
    if row["baseline_hard"] and row["pass_to_pass_damage"]:
        return "Clean already missed the target, so target failure is not new; extra regression-test failures still count as damage."
    if row["baseline_hard"]:
        return "Clean already missed target; do not attribute degraded target failure to the degradation."
    if row["pass_to_pass_damage"]:
        return "Official target success may be unchanged, but degraded run introduced additional PASS_TO_PASS failures."
    if row["condition"] == "type_hints" and row.get("annotation_nodes", 0) <= 1:
        return "Low-signal type-hints surface; use mainly as matrix-completeness/process evidence."
    if row["condition"] == "remove_tests" and row["degraded_only_changed_file_count"] > 0:
        return "Remove-tests changed the visible patch/test target; oracle replay is the authoritative score."
    if row["total_tokens_corrected_delta"] < 0:
        return "Degraded run was cheaper in corrected cumulative tokens despite the degradation."
    return "Outcome-stable comparison; useful mainly for process, cost, and patch-shape interpretation."


def concise_columns(df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "case_category",
        "repo",
        "instance_id",
        "condition",
        "replication_index",
        "clean_success",
        "degraded_success",
        "clean_success_degraded_failure",
        "baseline_hard",
        "clean_fail_to_pass_failed_count",
        "degraded_fail_to_pass_failed_count",
        "fail_to_pass_failed_count_delta",
        "clean_pass_to_pass_failed_count",
        "degraded_pass_to_pass_failed_count",
        "pass_to_pass_failed_count_delta",
        "total_tokens_corrected_delta",
        "changed_file_count_delta",
        "files_opened_before_first_edit_delta",
        "exploration_efficiency_delta",
        "clean_changed_files",
        "degraded_changed_files",
        "annotation_nodes",
        "comparison_file",
        "comparison_path",
        "interpretation",
    ]
    return df[columns]


def main() -> None:
    ensure_dirs()
    df = enriched_rq1()

    transition = add_case_category(df[df["clean_success_degraded_failure"]], "clean_success_to_degraded_failure")
    p2p = add_case_category(df[df["pass_to_pass_damage"]], "pass_to_pass_damage")
    high_token = add_case_category(
        df.reindex(df["total_tokens_corrected_delta"].abs().sort_values(ascending=False).index).head(20),
        "high_abs_token_delta",
    )
    cheaper = add_case_category(
        df[df["total_tokens_corrected_delta"] < 0].sort_values("total_tokens_corrected_delta").head(20),
        "degraded_cheaper",
    )
    baseline_hard = add_case_category(df[df["baseline_hard"]], "clean_already_failed")
    low_type = add_case_category(
        df[(df["condition"] == "type_hints") & (df["annotation_nodes"].fillna(0) <= 1)],
        "type_hints_zero_or_low_annotation_surface",
    )
    remove_shift = add_case_category(
        df[(df["condition"] == "remove_tests") & (df["degraded_only_changed_file_count"] > 0)],
        "remove_tests_patch_target_shift",
    )

    manifests = {
        "transition_manifest": transition,
        "pass_to_pass_damage_manifest": p2p,
        "audit_sample_manifest": pd.concat(
            [transition, p2p, high_token, cheaper, baseline_hard, low_type, remove_shift],
            ignore_index=True,
        ).drop_duplicates(["comparison_file", "case_category"]),
        "case_study_manifest": pd.concat(
            [transition, p2p, high_token, cheaper, baseline_hard, low_type, remove_shift],
            ignore_index=True,
        ),
    }

    for name, manifest in manifests.items():
        manifest = manifest.copy()
        manifest["interpretation"] = manifest.apply(interpretation, axis=1)
        artifact_rows = manifest.apply(artifact_status, axis=1, result_type="expand")
        manifest = pd.concat([manifest.reset_index(drop=True), artifact_rows.reset_index(drop=True)], axis=1)
        compact = concise_columns(manifest)
        write_csv(compact, DATA_DIR / f"{name}.csv")
        write_csv(compact, TABLE_DIR / f"{name}.csv")
        write_markdown_table(compact, TABLE_DIR / f"{name}.md")

    audited = pd.read_csv(TABLE_DIR / "audit_sample_manifest.csv")
    audited_status = []
    for _, row in audited.iterrows():
        status = artifact_status(row)
        audited_status.append(
            {
                **{key: row[key] for key in ["repo", "instance_id", "condition", "case_category"]},
                **status,
                "audit_read": row["interpretation"],
                "residual_uncertainty": "Low for official scoring fields; medium for process interpretation because logs lack phase-specific token/time splits.",
            }
        )
    audited_df = pd.DataFrame(audited_status).drop_duplicates(
        ["instance_id", "condition", "case_category"]
    )
    write_csv(audited_df, TABLE_DIR / "audited_run_table.csv")
    write_markdown_table(audited_df, TABLE_DIR / "audited_run_table.md")
    print(f"Wrote case-study and audit manifests to {DATA_DIR} and {TABLE_DIR}")


if __name__ == "__main__":
    main()
