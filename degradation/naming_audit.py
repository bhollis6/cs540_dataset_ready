from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from naming_conventions import collect_naming_audit, obfuscate_repo


def build_audit_report(
    repo_path: str | Path,
    sample_limit: int = 10,
    live: bool = False,
) -> dict[str, Any]:
    """Build a structured naming-readiness report for a repo."""
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_path": str(Path(repo_path).resolve()),
        "dry_run": collect_naming_audit(repo_path, sample_limit=sample_limit),
    }

    if live:
        stats = obfuscate_repo(str(repo_path), dry_run=False)
        report["live_run"] = stats.to_dict()

    return report


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Generate a structured readiness report for naming obfuscation. "
            "Use --live only on a disposable worktree."
        ),
    )
    parser.add_argument("repo_path")
    parser.add_argument("--sample-limit", type=int, default=10)
    parser.add_argument(
        "--live",
        action="store_true",
        help="Run a real rope-backed rename pass. Only use on a disposable worktree.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write the JSON report to a file instead of stdout.",
    )
    args = parser.parse_args()

    report = build_audit_report(
        args.repo_path,
        sample_limit=args.sample_limit,
        live=args.live,
    )
    payload = json.dumps(report, indent=2)
    if args.output is None:
        print(payload)
    else:
        args.output.write_text(payload + "\n", encoding="utf-8")
        print(f"Wrote naming audit to {args.output}")


if __name__ == "__main__":
    main()
