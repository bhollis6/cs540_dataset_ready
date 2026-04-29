from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from common import (
    CONDITION_ORDER,
    DATA_DIR,
    RQ1_JSON,
    RQ2_JSON,
    TABLE_DIR,
    comparison_path,
    enriched_rq1,
    ensure_dirs,
    load_rq2,
    read_json,
    write_csv,
    write_markdown_table,
)


EXPECTED_FULL_REPOS = {
    "pytest-dev/pytest",
    "sphinx-doc/sphinx",
    "pydata/xarray",
    "sympy/sympy",
    "django/django",
    "psf/requests",
    "matplotlib/matplotlib",
    "pylint-dev/pylint",
    "scikit-learn/scikit-learn",
    "astropy/astropy",
}


@dataclass
class Check:
    name: str
    expected: object
    observed: object
    passed: bool
    notes: str = ""


def json_row_count(path: Path) -> int:
    data = json.loads(path.read_text())
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        for key in ["rows", "comparisons", "phase_rows", "data"]:
            value = data.get(key)
            if isinstance(value, list):
                return len(value)
    raise ValueError(f"Cannot infer row count from {path}")


def full_repos(df: pd.DataFrame) -> set[str]:
    task_conditions = (
        df.groupby(["repo", "instance_id"])["condition"]
        .agg(lambda values: set(values))
        .reset_index(name="conditions")
    )
    task_conditions["complete_task"] = task_conditions["conditions"].map(
        lambda values: set(CONDITION_ORDER).issubset(values)
    )
    complete_counts = task_conditions.groupby("repo")["complete_task"].sum()
    return set(complete_counts[complete_counts >= 3].index)


def comparison_packet_mismatches(df: pd.DataFrame) -> int:
    mismatches = 0
    fields = [
        ("clean", "target_success", "clean_success", bool),
        ("degraded", "target_success", "degraded_success", bool),
        ("clean", "fail_to_pass_failed_count", "clean_fail_to_pass_failed_count", int),
        ("degraded", "fail_to_pass_failed_count", "degraded_fail_to_pass_failed_count", int),
        ("clean", "pass_to_pass_failed_count", "clean_pass_to_pass_failed_count", int),
        ("degraded", "pass_to_pass_failed_count", "degraded_pass_to_pass_failed_count", int),
    ]
    delta_fields = [
        ("fail_to_pass_failed_count_delta", "fail_to_pass_failed_count_delta", int),
        ("pass_to_pass_failed_count_delta", "pass_to_pass_failed_count_delta", int),
        ("files_opened_before_first_edit_delta", "files_opened_before_first_edit_delta", int),
    ]
    for _, row in df.iterrows():
        path = comparison_path(str(row["comparison_file"]))
        if not path.exists():
            mismatches += 1
            continue
        packet = read_json(path)
        if not isinstance(packet, dict):
            mismatches += 1
            continue
        if packet.get("instance_id") != row["instance_id"]:
            mismatches += 1
        if packet.get("repo") != row["repo"]:
            mismatches += 1
        if packet.get("chosen_condition") != row["condition"]:
            mismatches += 1
        if int(packet.get("replication_index", -1)) != int(row["replication_index"]):
            mismatches += 1
        for side, packet_field, row_field, cast in fields:
            side_packet = packet.get(side, {})
            if not isinstance(side_packet, dict) or cast(side_packet.get(packet_field)) != cast(row[row_field]):
                mismatches += 1
        deltas = packet.get("deltas", {})
        for packet_field, row_field, cast in delta_fields:
            if not isinstance(deltas, dict) or cast(deltas.get(packet_field)) != cast(row[row_field]):
                mismatches += 1
    return mismatches


def main() -> None:
    ensure_dirs()
    rq1 = enriched_rq1()
    rq2 = load_rq2()
    checks: list[Check] = []

    checks.append(Check("RQ1 CSV row count", 128, len(rq1), len(rq1) == 128))
    checks.append(Check("RQ1 JSON row count", 128, json_row_count(RQ1_JSON), json_row_count(RQ1_JSON) == 128))
    checks.append(Check("RQ2 CSV row count", 256, len(rq2), len(rq2) == 256))
    checks.append(Check("RQ2 JSON row count", 256, json_row_count(RQ2_JSON), json_row_count(RQ2_JSON) == 256))

    duplicate_count = int(
        rq1.duplicated(["instance_id", "condition", "replication_index"]).sum()
    )
    checks.append(
        Check(
            "No duplicate RQ1 instance/condition/replication rows",
            0,
            duplicate_count,
            duplicate_count == 0,
        )
    )

    observed_full_repos = full_repos(rq1)
    checks.append(
        Check(
            "Fully complete repos",
            sorted(EXPECTED_FULL_REPOS),
            sorted(observed_full_repos),
            observed_full_repos == EXPECTED_FULL_REPOS,
            "Definition: at least three tasks, each with all four degradation families.",
        )
    )
    checks.append(Check("Fully complete repo count", 10, len(observed_full_repos), len(observed_full_repos) == 10))
    checks.append(Check("Represented repo count", 11, rq1["repo"].nunique(), rq1["repo"].nunique() == 11))
    checks.append(Check("Unique task count", 32, rq1["instance_id"].nunique(), rq1["instance_id"].nunique() == 32))
    transitions = int(rq1["clean_success_degraded_failure"].sum())
    checks.append(Check("Clean-success to degraded-failure transitions", 11, transitions, transitions == 11))
    p2p_damage = int(rq1["pass_to_pass_damage"].sum())
    checks.append(Check("Regression-test damage rows", 11, p2p_damage, p2p_damage == 11))
    packet_mismatches = comparison_packet_mismatches(rq1)
    checks.append(
        Check(
            "RQ1 rows match comparison JSON packets",
            0,
            packet_mismatches,
            packet_mismatches == 0,
            "Checks success flags, target/regression failure counts, selected condition, replication index, and core deltas.",
        )
    )

    clean_token_mismatches = int(
        (
            rq1["clean_total_tokens_corrected"]
            != rq1["clean_input_tokens"] + rq1["clean_output_tokens"]
        ).sum()
    )
    degraded_token_mismatches = int(
        (
            rq1["degraded_total_tokens_corrected"]
            != rq1["degraded_input_tokens"] + rq1["degraded_output_tokens"]
        ).sum()
    )
    checks.append(
        Check(
            "Corrected clean token formula input+output",
            0,
            clean_token_mismatches,
            clean_token_mismatches == 0,
            "cached_input_tokens is diagnostic and must not be added.",
        )
    )
    checks.append(
        Check(
            "Corrected degraded token formula input+output",
            0,
            degraded_token_mismatches,
            degraded_token_mismatches == 0,
            "cached_input_tokens is diagnostic and must not be added.",
        )
    )

    rq2_side_counts = rq2.groupby("comparison_file")["side"].nunique()
    bad_phase_pairs = int((rq2_side_counts != 2).sum())
    checks.append(
        Check(
            "RQ2 has clean and degraded side for every comparison",
            0,
            bad_phase_pairs,
            bad_phase_pairs == 0,
        )
    )
    rq2_join_missing = int(not set(rq2["comparison_file"]).issubset(set(rq1["comparison_file"])))
    checks.append(
        Check(
            "RQ2 comparison files join to RQ1",
            0,
            rq2_join_missing,
            rq2_join_missing == 0,
        )
    )

    result = pd.DataFrame([check.__dict__ for check in checks])
    write_csv(result, TABLE_DIR / "validation_summary.csv")
    write_markdown_table(result, TABLE_DIR / "validation_summary.md")
    write_csv(result, DATA_DIR / "validation_summary.csv")

    failed = result[~result["passed"]]
    if failed.empty:
        print("All export validation checks passed.")
    else:
        print(result.to_string(index=False))
        raise SystemExit(f"{len(failed)} validation check(s) failed.")


if __name__ == "__main__":
    main()
