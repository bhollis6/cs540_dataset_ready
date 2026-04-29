from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "final_analysis"
DATA_DIR = BUNDLE / "data"
TABLE_DIR = BUNDLE / "tables"
FIGURE_DIR = BUNDLE / "figures"
SCRIPT_DIR = BUNDLE / "scripts"

RQ1_CSV = ROOT / "results" / "rq1_comparisons_2026-04-26.csv"
RQ1_JSON = ROOT / "results" / "rq1_comparisons_2026-04-26.json"
RQ2_CSV = ROOT / "results" / "rq2_phase_metrics_2026-04-26.csv"
RQ2_JSON = ROOT / "results" / "rq2_phase_metrics_2026-04-26.json"
PROFILE_DIR = ROOT / "src" / "profiles"
COMPARISON_DIR = ROOT / "archive" / "provenance" / "dev" / "active" / "bootstrap-2026-04-22"

CONDITION_ORDER = ["naming", "type_hints", "comments_docstrings", "remove_tests"]
CONDITION_LABELS = {
    "naming": "Naming",
    "type_hints": "Type hints",
    "comments_docstrings": "Comments/docstrings",
    "remove_tests": "Remove tests",
}


@dataclass(frozen=True)
class WilsonInterval:
    rate: float
    low: float
    high: float


def ensure_dirs() -> None:
    for path in [DATA_DIR, TABLE_DIR, FIGURE_DIR, SCRIPT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def load_rq1() -> pd.DataFrame:
    df = pd.read_csv(RQ1_CSV)
    for col in ["clean_success", "degraded_success", "target_success_changed"]:
        df[col] = df[col].astype(bool)
    return df


def load_rq2() -> pd.DataFrame:
    df = pd.read_csv(RQ2_CSV)
    for col in ["target_success", "first_edit_observed"]:
        df[col] = df[col].astype(bool)
    return df


def read_json(path: Path) -> object:
    return json.loads(path.read_text())


def resolve_artifact_path(value: object) -> Path:
    """Resolve archived absolute paths after the workspace is moved or renamed."""
    text = "" if value is None else str(value)
    if not text:
        return Path("")
    path = Path(text)
    candidate = path if path.is_absolute() else ROOT / path
    if candidate.exists():
        return candidate

    rewrites = [
        ("/archive/provenance/dev/", ROOT / "archive" / "provenance" / "dev"),
        ("/dev/active/", ROOT / "archive" / "provenance" / "dev" / "active"),
        ("/runs/", ROOT / "runs"),
        ("/results/", ROOT / "results"),
    ]
    for marker, base in rewrites:
        marker_index = text.find(marker)
        if marker_index >= 0:
            suffix = text[marker_index + len(marker) :]
            return base / suffix
    return candidate


def repo_relative(path: Path) -> str:
    candidate = path if path.is_absolute() else ROOT / path
    try:
        return str(candidate.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def comparison_path(comparison_file: str) -> Path:
    path = COMPARISON_DIR / comparison_file
    if not path.exists():
        matches = list(COMPARISON_DIR.glob(comparison_file))
        if matches:
            return matches[0]
    return path


def profile_path(instance_id: str) -> Path:
    return PROFILE_DIR / f"{instance_id}_eligibility.json"


def pipe_split(value: object) -> list[str]:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return []
    text = str(value)
    if not text:
        return []
    return [part for part in text.split("|") if part]


def wilson_interval(successes: int, n: int, z: float = 1.96) -> WilsonInterval:
    if n == 0:
        return WilsonInterval(float("nan"), float("nan"), float("nan"))
    phat = successes / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n) / denom
    return WilsonInterval(phat, max(0.0, center - margin), min(1.0, center + margin))


def safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return float("nan")
    return numerator / denominator


def odds_ratio(a_success: int, a_fail: int, b_success: int, b_fail: int) -> float:
    # Haldane-Anscombe correction keeps ratios finite for small cells.
    return ((a_success + 0.5) * (b_fail + 0.5)) / ((a_fail + 0.5) * (b_success + 0.5))


def first_int(text: str | None) -> int | None:
    if not text:
        return None
    match = re.search(r"(\d+)", text)
    return int(match.group(1)) if match else None


def parse_comments_counts(text: str | None) -> tuple[int | None, int | None]:
    if not text:
        return None, None
    doc_match = re.search(r"(\d+)\s+docstring", text)
    comment_match = re.search(r"(\d+)\s+comment", text)
    return (
        int(doc_match.group(1)) if doc_match else None,
        int(comment_match.group(1)) if comment_match else None,
    )


def parse_profile(profile: dict) -> dict[str, object]:
    conditions = profile.get("conditions", {})
    type_rationale = conditions.get("type_hints", {}).get("signal", {}).get("rationale", "")
    naming_rationale = conditions.get("naming", {}).get("signal", {}).get("rationale", "")
    comments_rationale = (
        conditions.get("comments_docstrings", {}).get("signal", {}).get("rationale", "")
    )
    docstring_count, comment_count = parse_comments_counts(comments_rationale)
    return {
        "instance_id": profile.get("instance_id"),
        "repo": profile.get("repo"),
        "base_commit": profile.get("base_commit"),
        "changed_source_files_profile": "|".join(profile.get("changed_source_files", [])),
        "changed_test_files_profile": "|".join(profile.get("changed_test_files", [])),
        "overall_status": profile.get("overall_status"),
        "eligible_conditions": "|".join(profile.get("eligible_conditions", [])),
        "test_signal_level": profile.get("test_signal", {}).get("level"),
        "type_hints_signal_level": conditions.get("type_hints", {}).get("signal", {}).get("level"),
        "type_hints_rationale": type_rationale,
        "annotation_nodes": first_int(type_rationale),
        "naming_signal_level": conditions.get("naming", {}).get("signal", {}).get("level"),
        "naming_rationale": naming_rationale,
        "naming_candidates": first_int(naming_rationale),
        "comments_signal_level": conditions.get("comments_docstrings", {})
        .get("signal", {})
        .get("level"),
        "comments_docstrings_rationale": comments_rationale,
        "docstring_count": docstring_count,
        "comment_count": comment_count,
        "remove_tests_signal_level": conditions.get("remove_tests", {}).get("signal", {}).get("level"),
        "decision_summary": profile.get("decision_summary"),
    }


def load_task_profiles(instance_ids: Iterable[str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for instance_id in sorted(set(instance_ids)):
        path = profile_path(instance_id)
        if path.exists():
            rows.append(parse_profile(read_json(path)))  # type: ignore[arg-type]
        else:
            rows.append({"instance_id": instance_id, "profile_missing": True})
    return pd.DataFrame(rows)


def enriched_rq1() -> pd.DataFrame:
    df = load_rq1().copy()
    profiles = load_task_profiles(df["instance_id"])
    df = df.merge(profiles, on=["instance_id", "repo"], how="left")
    df["clean_success_degraded_failure"] = df["clean_success"] & ~df["degraded_success"]
    df["clean_failure_degraded_success"] = ~df["clean_success"] & df["degraded_success"]
    df["baseline_hard"] = ~df["clean_success"]
    df["degraded_failed_when_clean_failed"] = ~df["clean_success"] & ~df["degraded_success"]
    df["pass_to_pass_damage"] = df["pass_to_pass_failed_count_delta"] > 0
    df["fail_to_pass_damage"] = df["fail_to_pass_failed_count_delta"] > 0
    df["any_official_damage"] = (
        df["clean_success_degraded_failure"]
        | df["pass_to_pass_damage"]
        | df["fail_to_pass_damage"]
    )
    df["token_delta_sign"] = df["total_tokens_corrected_delta"].map(
        lambda value: "higher" if value > 0 else "lower" if value < 0 else "same"
    )
    df["clean_changed_file_list"] = df["clean_changed_files"].map(pipe_split)
    df["degraded_changed_file_list"] = df["degraded_changed_files"].map(pipe_split)
    df["clean_opened_file_list"] = df["clean_opened_files_before_first_edit"].map(pipe_split)
    df["degraded_opened_file_list"] = df["degraded_opened_files_before_first_edit"].map(pipe_split)
    df["comparison_path"] = df["comparison_file"].map(
        lambda name: repo_relative(comparison_path(str(name)))
    )
    df["type_hints_low_signal"] = (df["condition"] == "type_hints") & (
        df["annotation_nodes"].fillna(0) <= 1
    )
    df["type_hints_zero_annotation_surface"] = (df["condition"] == "type_hints") & (
        df["annotation_nodes"].fillna(0) == 0
    )
    return df


def condition_sort_key(value: str) -> int:
    try:
        return CONDITION_ORDER.index(value)
    except ValueError:
        return len(CONDITION_ORDER)


def write_markdown_table(df: pd.DataFrame, path: Path, index: bool = False) -> None:
    out = df.reset_index() if index else df.copy()
    headers = [str(col) for col in out.columns]

    def cell(value: object) -> str:
        if isinstance(value, float):
            text = f"{value:.3f}" if not value.is_integer() else str(int(value))
        elif isinstance(value, (list, tuple, set)):
            text = ", ".join(str(part) for part in value)
        else:
            text = "" if value is None or (not isinstance(value, (dict, list, tuple, set)) and pd.isna(value)) else str(value)
        return text.replace("|", "\\|").replace("\n", " ")

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in out.iterrows():
        lines.append("| " + " | ".join(cell(row[col]) for col in out.columns) + " |")
    path.write_text("\n".join(lines) + "\n")


def write_latex_table(df: pd.DataFrame, path: Path, index: bool = False) -> None:
    out = df.reset_index() if index else df.copy()

    def latex_cell(value: object) -> str:
        if isinstance(value, float):
            text = f"{value:.3f}" if not value.is_integer() else str(int(value))
        else:
            text = "" if pd.isna(value) else str(value)
        replacements = {
            "\\": r"\textbackslash{}",
            "&": r"\&",
            "%": r"\%",
            "$": r"\$",
            "#": r"\#",
            "_": r"\_",
            "{": r"\{",
            "}": r"\}",
            "~": r"\textasciitilde{}",
            "^": r"\textasciicircum{}",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

    columns = "l" * len(out.columns)
    lines = [rf"\begin{{tabular}}{{{columns}}}", r"\toprule"]
    lines.append(" & ".join(latex_cell(col) for col in out.columns) + r" \\")
    lines.append(r"\midrule")
    for _, row in out.iterrows():
        lines.append(" & ".join(latex_cell(row[col]) for col in out.columns) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}", ""])
    path.write_text("\n".join(lines))


def write_csv(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, index=False)


def as_rate_pct(value: float) -> float:
    return round(100 * value, 1) if pd.notna(value) else value
