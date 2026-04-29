"""CLI entry point for LLM-Judge PR selection tool."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.config import Config, load_config
from src.evaluator.judge import evaluate_candidates
from src.output.csv_writer import write_detailed_json, write_results_csv, write_summary_csv
from src.output.manifest import write_manifest
from src.scraper.filters import apply_filters
from src.scraper.github_graphql import fetch_pr_metadata
from src.scraper.github_rest import fetch_pr_diff


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="llm-judge",
        description="LLM-as-a-Judge PR selection for agent-readiness experiments",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- scrape subcommand ---
    scrape = subparsers.add_parser("scrape", help="Scrape candidate PRs from GitHub repos")
    repo_source = scrape.add_mutually_exclusive_group(required=True)
    repo_source.add_argument(
        "--repo", action="append", dest="repos",
        help="GitHub repo in owner/name format (can specify multiple)",
    )
    repo_source.add_argument(
        "--repos-file", type=Path, default=None,
        help="JSON file with repo list (e.g., repos.json)",
    )
    scrape.add_argument("--output-dir", type=Path, default=Path("candidates"))
    scrape.add_argument("--max-prs", type=int, default=300)
    scrape.add_argument("--target-candidates", type=int, default=None,
                        help="Stop early after this many candidates pass pre-filtering")
    scrape.add_argument("--skip-bot-prs", action="store_true", default=True)
    scrape.add_argument("--no-skip-bot-prs", action="store_false", dest="skip_bot_prs")
    scrape.add_argument("--min-lines", type=int, default=5)
    scrape.add_argument("--max-lines", type=int, default=500)
    scrape.add_argument("--max-files", type=int, default=20)
    scrape.add_argument("--min-date", type=str, default="2022-01-01",
                        help="Skip PRs merged before this date (YYYY-MM-DD)")

    # --- evaluate subcommand ---
    evaluate = subparsers.add_parser("evaluate", help="Evaluate candidate PRs with LLM judge")
    eval_input = evaluate.add_mutually_exclusive_group()
    eval_input.add_argument("--input-dir", type=Path, default=Path("candidates"))
    eval_input.add_argument("--input-file", type=Path, default=None)
    evaluate.add_argument("--output-dir", type=Path, default=Path("results"))
    evaluate.add_argument("--repo", type=str, default=None,
                          help="Only evaluate candidates from this repo (e.g., 'starlette')")
    evaluate.add_argument("--max-candidates", type=int, default=None,
                          help="Limit number of candidates to evaluate")
    evaluate.add_argument("--provider", default="claude-code",
                          choices=["claude-code", "anthropic", "openrouter"])
    evaluate.add_argument("--model", default=None,
                          help="Model name (default depends on provider)")
    model_shortcut = evaluate.add_mutually_exclusive_group()
    model_shortcut.add_argument("--opus", action="store_true", default=False,
                                help="Use claude-sonnet-4-6 (default)")
    model_shortcut.add_argument("--sonnet", action="store_true", default=False,
                                help="Use claude-sonnet-4-6")
    evaluate.add_argument("--reliability-check", action="store_true", default=False,
                          help="Run each candidate twice and compute ICC")
    evaluate.add_argument("--accept-threshold", type=int, default=18)
    evaluate.add_argument("--review-threshold", type=int, default=13)

    # --- deep-evaluate subcommand ---
    deep = subparsers.add_parser(
        "deep-evaluate",
        help=(
            "Stage 2: deep evaluation with full repo context + "
            "pre-flight validation"
        ),
    )
    deep.add_argument("--candidates-dir", type=Path, default=Path("candidates"),
                      help="Directory with candidate JSON files")
    deep.add_argument("--results-dir", type=Path, default=Path("results"),
                      help="Directory with Stage 1 results (manifests)")
    deep.add_argument("--output-dir", type=Path, default=Path("deep_results"))
    deep.add_argument("--clones-dir", type=Path, default=Path("clones"),
                      help="Directory for bare git clones")
    deep.add_argument("--provider", default="claude-code",
                      choices=["claude-code", "anthropic", "openrouter"])
    deep.add_argument("--model", default=None)
    deep_model = deep.add_mutually_exclusive_group()
    deep_model.add_argument("--opus", action="store_true", default=False)
    deep_model.add_argument("--sonnet", action="store_true", default=False)
    deep.add_argument("--repo", type=str, default=None,
                      help="Only evaluate candidates from this repo")
    deep.add_argument("--preflight-only", action="store_true", default=False,
                      help="Only run pre-flight validation, skip LLM evaluation")
    deep.add_argument("--skip-preflight", action="store_true", default=False,
                      help="Skip pre-flight validation, only run LLM evaluation")
    deep.add_argument("--context-budget", type=int, default=None,
                      help="Max chars for source context (default: no limit)")
    deep.add_argument(
        "--min-navigation-depth",
        type=int,
        default=3,
        help="Minimum Stage 2 navigation depth score required for verified manifests",
    )

    audit = subparsers.add_parser(
        "audit-naming",
        help="Create a disposable worktree and generate a repo-level naming readiness report",
    )
    audit.add_argument("--repo", required=True, help="GitHub repo in owner/name format")
    audit.add_argument("--clones-dir", type=Path, default=Path("clones"))
    audit.add_argument("--output-dir", type=Path, default=Path("audit_results"))
    audit.add_argument("--commit", type=str, default=None,
                       help="Optional commit SHA to audit instead of the current clone HEAD")
    audit.add_argument("--sample-limit", type=int, default=10,
                       help="How many sample symbols per kind to keep in the dry-run summary")
    audit.add_argument("--live", action="store_true", default=False,
                       help="Run a real rope-backed rename pass on the disposable worktree")
    audit.add_argument("--keep-worktree", action="store_true", default=False,
                       help="Keep the disposable audit worktree after the report is written")

    readiness = subparsers.add_parser(
        "audit-repo",
        help="Create a disposable worktree and generate a repo-level degradation readiness report",
    )
    readiness.add_argument("--repo", required=True, help="GitHub repo in owner/name format")
    readiness.add_argument("--clones-dir", type=Path, default=Path("clones"))
    readiness.add_argument("--output-dir", type=Path, default=Path("audit_results"))
    readiness.add_argument("--commit", type=str, default=None,
                           help="Optional commit SHA to audit instead of the current clone HEAD")
    readiness.add_argument("--sample-limit", type=int, default=10,
                           help="How many sample symbols to keep for the embedded naming summary")
    readiness.add_argument("--keep-worktree", action="store_true", default=False,
                           help="Keep the disposable audit worktree after the report is written")

    stage2_probe = subparsers.add_parser(
        "probe-stage2",
        help="Run a profile-aware Stage 2 environment probe over sampled historical commits",
    )
    stage2_probe.add_argument("--repo", required=True, help="GitHub repo in owner/name format")
    stage2_probe.add_argument("--clones-dir", type=Path, default=Path("clones"))
    stage2_probe.add_argument("--output-dir", type=Path, default=Path("probe_results"))
    stage2_probe.add_argument(
        "--profiles-dir",
        type=Path,
        default=Path("repo_profiles"),
        help="Directory containing repo execution profiles",
    )
    stage2_probe.add_argument(
        "--commit",
        action="append",
        dest="commits",
        help="Specific commit SHA to probe. Repeat to select multiple commits.",
    )
    stage2_probe.add_argument(
        "--sample-size",
        type=int,
        default=3,
        help="How many recent first-parent commits to probe when no explicit commits are given",
    )
    stage2_probe.add_argument(
        "--install-timeout-seconds",
        type=int,
        default=60,
        help="Maximum wall time for each install command attempt during probing",
    )
    stage2_probe.add_argument(
        "--probe-timeout-seconds",
        type=int,
        default=60,
        help="Maximum wall time for the pytest collection probe command",
    )
    stage2_probe.add_argument(
        "--keep-worktrees",
        action="store_true",
        default=False,
        help="Keep disposable probe worktrees after the report is written",
    )

    stage2_bundle = subparsers.add_parser(
        "prepare-stage2-container",
        help="Prepare container-ready Stage 2 probe bundles from repo profiles and historical commits",
    )
    stage2_bundle.add_argument("--repo", required=True, help="GitHub repo in owner/name format")
    stage2_bundle.add_argument("--clones-dir", type=Path, default=Path("clones"))
    stage2_bundle.add_argument("--output-dir", type=Path, default=Path("container_probe_bundles"))
    stage2_bundle.add_argument(
        "--profiles-dir",
        type=Path,
        default=Path("repo_profiles"),
        help="Directory containing repo execution profiles",
    )
    stage2_bundle.add_argument(
        "--commit",
        action="append",
        dest="commits",
        help="Specific commit SHA to bundle. Repeat to select multiple commits.",
    )
    stage2_bundle.add_argument(
        "--sample-size",
        type=int,
        default=1,
        help="How many recent first-parent commits to bundle when no explicit commits are given",
    )

    stage2_compare = subparsers.add_parser(
        "compare-stage2-runtimes",
        help="Compare host-vs-container Stage 2 runtime outcomes across one or more repos",
    )
    stage2_compare.add_argument(
        "--repo",
        action="append",
        dest="repos",
        required=True,
        help="GitHub repo in owner/name format. Repeat to compare multiple repos.",
    )
    stage2_compare.add_argument(
        "--host-probe-root",
        type=Path,
        default=Path("probe_results/host_stage2_compare"),
        help="Root directory containing host-backed Stage 2 probe reports",
    )
    stage2_compare.add_argument(
        "--container-bundle-root",
        type=Path,
        default=Path("container_probe_bundles"),
        help="Root directory containing Stage 2 container bundle reports and probe_results",
    )
    stage2_compare.add_argument(
        "--output-dir",
        type=Path,
        default=Path("probe_results/stage2_runtime_compare"),
        help="Directory to write the cross-repo Stage 2 runtime comparison report",
    )

    packet = subparsers.add_parser(
        "build-packet",
        help="Assemble a repo-level experiment review packet from readiness and task artifacts",
    )
    packet.add_argument("--repo", required=True, help="GitHub repo in owner/name format")
    packet.add_argument("--results-dir", type=Path, default=Path("results"))
    packet.add_argument("--deep-results-dir", type=Path, default=Path("deep_results"))
    packet.add_argument("--readiness-dir", type=Path, default=Path("audit_results"))
    packet.add_argument("--naming-audit-dir", type=Path, default=None,
                        help="Optional separate directory for naming readiness reports")
    packet.add_argument(
        "--host-probe-root",
        type=Path,
        default=Path("probe_results/host_stage2_compare"),
        help="Root directory containing host-backed Stage 2 probe reports",
    )
    packet.add_argument(
        "--container-bundle-root",
        type=Path,
        default=Path("container_probe_bundles"),
        help="Root directory containing Stage 2 container bundle reports and probe_results",
    )
    packet.add_argument("--output-dir", type=Path, default=Path("packets"))

    run_plan = subparsers.add_parser(
        "build-run-plan",
        help="Assemble a Stage 5 run plan from verified tasks and the repo review packet",
    )
    run_plan.add_argument("--repo", required=True, help="GitHub repo in owner/name format")
    run_plan.add_argument("--deep-results-dir", type=Path, default=Path("deep_results"))
    run_plan.add_argument("--packet-dir", type=Path, default=Path("packets"))
    run_plan.add_argument("--candidates-dir", type=Path, default=Path("candidates"))
    run_plan.add_argument("--output-dir", type=Path, default=Path("run_plans"))
    run_plan.add_argument(
        "--agent",
        action="append",
        dest="agents",
        choices=["claude-code", "codex-cli"],
        help="Agent harness to include. Repeat to select a subset. Defaults to both.",
    )
    run_plan.add_argument(
        "--replications",
        type=int,
        default=3,
        help="How many non-deterministic replications to schedule per task/condition/harness",
    )

    materialize = subparsers.add_parser(
        "materialize-runs",
        help="Stage 4: create per-run historical workspaces and apply planned degradations",
    )
    materialize.add_argument("--repo", required=True, help="GitHub repo in owner/name format")
    materialize.add_argument("--run-plan-dir", type=Path, default=Path("run_plans"))
    materialize.add_argument("--clones-dir", type=Path, default=Path("clones"))
    materialize.add_argument(
        "--output-dir",
        type=Path,
        default=Path("."),
        help="Base directory under which run-plan output paths will be created",
    )
    materialize.add_argument(
        "--run-id",
        action="append",
        dest="run_ids",
        help="Specific run_id to materialize. Repeat to select multiple runs.",
    )
    materialize.add_argument(
        "--condition",
        action="append",
        dest="conditions",
        choices=["clean", "type_hints", "naming", "comments_docstrings", "remove_tests"],
        help="Only materialize this condition. Repeat to select multiple conditions.",
    )
    materialize.add_argument(
        "--agent",
        action="append",
        dest="agents",
        choices=["claude-code", "codex-cli", "claude_code", "codex_cli"],
        help="Only materialize runs for the selected harness IDs/runners.",
    )
    materialize.add_argument("--limit", type=int, default=None)
    materialize.add_argument("--overwrite", action="store_true", default=False)

    execute = subparsers.add_parser(
        "execute-runs",
        help="Stage 5: run selected materialized experiments with Claude or Codex and write result artifacts",
    )
    execute.add_argument("--repo", required=True, help="GitHub repo in owner/name format")
    execute.add_argument("--run-plan-dir", type=Path, default=Path("run_plans"))
    execute.add_argument("--clones-dir", type=Path, default=Path("clones"))
    execute.add_argument(
        "--output-dir",
        type=Path,
        default=Path("."),
        help="Base directory under which the materialized run roots live",
    )
    execute.add_argument(
        "--run-id",
        action="append",
        dest="run_ids",
        help="Specific run_id to execute. Repeat to select multiple runs.",
    )
    execute.add_argument(
        "--condition",
        action="append",
        dest="conditions",
        choices=["clean", "type_hints", "naming", "comments_docstrings", "remove_tests"],
        help="Only execute this condition. Repeat to select multiple conditions.",
    )
    execute.add_argument(
        "--agent",
        action="append",
        dest="agents",
        choices=["claude-code", "codex-cli", "claude_code", "codex_cli"],
        help="Only execute runs for the selected harness IDs/runners.",
    )
    execute.add_argument("--limit", type=int, default=None)
    execute.add_argument("--overwrite", action="store_true", default=False)
    execute.add_argument(
        "--agent-timeout-seconds",
        type=int,
        default=1800,
        help="Maximum wall time per agent run before subprocess termination",
    )

    stage6 = subparsers.add_parser(
        "parse-runs",
        help="Stage 6: parse Stage 5 artifacts into richer bootstrap/execution metrics",
    )
    stage6.add_argument("--repo", required=True, help="GitHub repo in owner/name format")
    stage6.add_argument(
        "--execution-dir",
        type=Path,
        default=Path("."),
        help="Directory containing {repo}_stage5_execution.json and per-run artifacts",
    )
    stage6.add_argument(
        "--run-id",
        action="append",
        dest="run_ids",
        help="Specific run_id to parse. Repeat to select multiple runs.",
    )
    stage6.add_argument(
        "--condition",
        action="append",
        dest="conditions",
        choices=["clean", "type_hints", "naming", "comments_docstrings", "remove_tests"],
        help="Only parse metrics for this condition. Repeat to select multiple conditions.",
    )
    stage6.add_argument(
        "--agent",
        action="append",
        dest="agents",
        choices=["claude-code", "codex-cli", "claude_code", "codex_cli"],
        help="Only parse runs for the selected harness IDs/runners.",
    )
    stage6.add_argument("--limit", type=int, default=None)
    stage6.add_argument(
        "--no-write-back",
        action="store_true",
        default=False,
        help="Do not update per-run metrics.json files; only emit the Stage 6 summary artifact.",
    )

    stage7 = subparsers.add_parser(
        "analyze-runs",
        help="Stage 7: aggregate Stage 6 metrics into experiment analysis artifacts",
    )
    stage7.add_argument("--repo", required=True, help="GitHub repo in owner/name format")
    stage7.add_argument(
        "--stage6-dir",
        type=Path,
        default=Path("."),
        help="Directory containing {repo}_stage6_metrics.json and per-run artifacts",
    )
    stage7.add_argument(
        "--run-id",
        action="append",
        dest="run_ids",
        help="Specific run_id to analyze. Repeat to select multiple runs.",
    )
    stage7.add_argument(
        "--condition",
        action="append",
        dest="conditions",
        choices=["clean", "type_hints", "naming", "comments_docstrings", "remove_tests"],
        help="Only analyze this condition. Repeat to select multiple conditions.",
    )
    stage7.add_argument(
        "--agent",
        action="append",
        dest="agents",
        choices=["claude-code", "codex-cli", "claude_code", "codex_cli"],
        help="Only analyze runs for the selected harness IDs/runners.",
    )
    stage7.add_argument("--limit", type=int, default=None)

    task_packet = subparsers.add_parser(
        "build-task-packet",
        help="Build a focused single-task packet from Stage 7 analysis artifacts",
    )
    task_packet.add_argument("--repo", required=True, help="GitHub repo in owner/name format")
    task_packet.add_argument("--stage7-dir", type=Path, default=Path("."))
    task_packet.add_argument("--candidate-id", required=True)
    task_packet.add_argument(
        "--agent",
        type=str,
        default=None,
        help="Optional harness filter, e.g. codex-cli or claude-code",
    )
    task_packet.add_argument("--output-dir", type=Path, default=None)

    return parser


def cmd_scrape(config: Config) -> None:
    """Scrape merged PRs from GitHub repos and write candidate JSON files."""
    config.output_dir = config.input_dir  # scraper writes to the "input" dir for evaluate
    config.output_dir.mkdir(parents=True, exist_ok=True)

    for repo in config.repos:
        print(f"\n{'='*60}")
        print(f"Scraping: {repo}")
        print(f"{'='*60}")

        # Phase 1: GraphQL bulk fetch
        print(f"Fetching merged PR metadata (up to {config.max_prs})...")
        try:
            all_prs = fetch_pr_metadata(
                repo=repo,
                token=config.github_token,
                max_prs=config.max_prs,
            )
        except Exception as e:
            print(f"  ERROR scraping {repo}: {e}")
            print("  Skipping to next repo.")
            continue
        print(f"  Fetched {len(all_prs)} merged PRs")

        # Phase 2: Heuristic pre-filter
        survivors, stats = apply_filters(all_prs, config)
        print("\nPre-filter results:")
        print(f"  {stats}")
        print(f"  {len(survivors)} candidates survived")

        if not survivors:
            print(f"  No candidates survived pre-filtering for {repo}. Skipping.")
            continue

        # Phase 3: REST diff fetch for survivors
        repo_short = repo.split("/")[-1]
        written = 0
        for i, pr in enumerate(survivors, 1):
            candidate_id = f"{repo_short}_pr_{pr.pr_number}"
            out_path = config.output_dir / f"{candidate_id}.json"

            print(f"  [{i}/{len(survivors)}] Fetching diff for PR #{pr.pr_number}...", end=" ")

            candidate = fetch_pr_diff(
                repo=repo,
                pr_metadata=pr,
                token=config.github_token,
            )

            if candidate is None:
                print("FAILED (could not fetch diff)")
                continue

            with open(out_path, "w") as f:
                json.dump(candidate.to_dict(), f, indent=2)
            written += 1
            print("OK")

        print(f"\nWrote {written} candidate files to {config.output_dir}/")


def cmd_evaluate(config: Config) -> None:
    """Evaluate candidate PRs using the LLM judge."""
    config.output_dir.mkdir(parents=True, exist_ok=True)

    # Load candidates
    from src.scraper.models import CandidatePR

    candidates: list[CandidatePR] = []
    if config.input_file:
        with open(config.input_file) as f:
            candidates.append(CandidatePR.from_dict(json.load(f)))
    else:
        for json_file in sorted(config.input_dir.glob("*.json")):
            with open(json_file) as f:
                candidates.append(CandidatePR.from_dict(json.load(f)))

    # Filter by repo if specified
    repo_filter = getattr(config, '_repo_filter', None)
    if repo_filter:
        candidates = [
            c
            for c in candidates
            if repo_filter in c.candidate_id or repo_filter in c.repo
        ]
        print(f"Filtered to repo '{repo_filter}': {len(candidates)} candidates")

    # Limit count if specified
    max_candidates = getattr(config, '_max_candidates', None)
    if max_candidates and len(candidates) > max_candidates:
        candidates = candidates[:max_candidates]
        print(f"Limited to {max_candidates} candidates")

    if not candidates:
        print("No candidate files found. Run 'scrape' first.")
        sys.exit(1)

    print(f"Loaded {len(candidates)} candidates")
    runs_per_candidate = 2 if config.reliability_check else 1
    print(f"Evaluation runs per candidate: {runs_per_candidate}")
    print(f"Provider: {config.provider} | Model: {config.model}")
    print()

    # Run evaluation
    results = evaluate_candidates(candidates, config)

    # Write outputs
    write_results_csv(results, config.output_dir / "results.csv")
    write_summary_csv(results, config.output_dir / "summary.csv")
    write_detailed_json(results, config.output_dir / "results_detailed.json")
    write_manifest(results, config)

    if config.reliability_check:
        from src.evaluator.reliability import compute_reliability
        compute_reliability(results, config.output_dir / "reliability.csv")

    # Console summary
    print(f"\n{'='*60}")
    print("Evaluation Summary")
    print(f"{'='*60}")

    repos = sorted(set(r.repo for r in results))
    for repo in repos:
        repo_results = [r for r in results if r.repo == repo and r.run_number == 1]
        accepted = sum(1 for r in repo_results if r.response.recommendation == "ACCEPT")
        review = sum(1 for r in repo_results if r.response.recommendation == "REVIEW")
        rejected = sum(1 for r in repo_results if r.response.recommendation == "REJECT")
        print(f"\n  {repo}: {len(repo_results)} candidates")
        print(f"    ACCEPT: {accepted} | REVIEW: {review} | REJECT: {rejected}")
        top = sorted(repo_results, key=lambda r: r.response.total_score, reverse=True)[:5]
        if top:
            top_ids = ", ".join(f"PR#{r.pr_number}({r.response.total_score})" for r in top)
            print(f"    Top candidates: {top_ids}")

    print(f"\nResults written to {config.output_dir}/")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    config = load_config()

    if args.command == "scrape":
        if args.repos_file:
            with open(args.repos_file) as f:
                repos_data = json.load(f)
            config.repos = [r["name"] for r in repos_data["repos"]]
        else:
            config.repos = args.repos
        config.input_dir = args.output_dir
        config.max_prs = args.max_prs
        config.target_candidates = args.target_candidates
        config.skip_bot_prs = args.skip_bot_prs
        config.min_lines_changed = args.min_lines
        config.max_lines_changed = args.max_lines
        config.min_date = args.min_date
        config.max_files_changed = args.max_files

        errors = config.validate_scraper()
        if errors:
            for e in errors:
                print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        cmd_scrape(config)

    elif args.command == "evaluate":
        config.provider = args.provider

        # --opus / --sonnet shortcuts override --model
        if args.sonnet:
            config.model = "claude-sonnet-4-6"
        elif args.model:
            config.model = args.model
        else:
            # Default: opus for claude-code/anthropic, sonnet for openrouter
            default_models = {
                "claude-code": "claude-sonnet-4-6",
                "anthropic": "claude-sonnet-4-6",
                "openrouter": "anthropic/claude-sonnet-4-6",
            }
            config.model = default_models.get(args.provider, "claude-sonnet-4-6")
        config.input_dir = args.input_dir
        config.input_file = args.input_file
        config.output_dir = args.output_dir
        config.reliability_check = args.reliability_check
        config.accept_threshold = args.accept_threshold
        config.review_threshold = args.review_threshold
        config._repo_filter = args.repo
        config._max_candidates = args.max_candidates

        errors = config.validate_evaluator()
        if errors:
            for e in errors:
                print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        cmd_evaluate(config)

    elif args.command == "deep-evaluate":
        config.provider = args.provider

        # Sonnet default, --opus flag for deeper reasoning if needed
        if args.opus:
            config.model = "claude-opus-4-6"
        elif args.model:
            config.model = args.model
        else:
            config.model = "claude-sonnet-4-6"

        config.output_dir = args.output_dir
        config.clones_dir = args.clones_dir
        config.preflight_only = args.preflight_only
        config.skip_preflight = args.skip_preflight
        config.context_budget_chars = args.context_budget
        config.min_navigation_depth = args.min_navigation_depth
        config._repo_filter = args.repo
        config._candidates_dir = args.candidates_dir

        cmd_deep_evaluate(config, args.candidates_dir, args.results_dir)

    elif args.command == "audit-naming":
        cmd_audit_naming(
            repo=args.repo,
            clones_dir=args.clones_dir,
            output_dir=args.output_dir,
            commit_sha=args.commit,
            sample_limit=args.sample_limit,
            live=args.live,
            keep_worktree=args.keep_worktree,
        )

    elif args.command == "audit-repo":
        cmd_audit_repo(
            repo=args.repo,
            clones_dir=args.clones_dir,
            output_dir=args.output_dir,
            commit_sha=args.commit,
            sample_limit=args.sample_limit,
            keep_worktree=args.keep_worktree,
        )
    elif args.command == "probe-stage2":
        cmd_probe_stage2(
            repo=args.repo,
            clones_dir=args.clones_dir,
            output_dir=args.output_dir,
            profiles_dir=args.profiles_dir,
            commits=args.commits,
            sample_size=args.sample_size,
            install_timeout_seconds=args.install_timeout_seconds,
            probe_timeout_seconds=args.probe_timeout_seconds,
            keep_worktrees=args.keep_worktrees,
        )
    elif args.command == "prepare-stage2-container":
        cmd_prepare_stage2_container(
            repo=args.repo,
            clones_dir=args.clones_dir,
            output_dir=args.output_dir,
            profiles_dir=args.profiles_dir,
            commits=args.commits,
            sample_size=args.sample_size,
        )
    elif args.command == "compare-stage2-runtimes":
        cmd_compare_stage2_runtimes(
            repos=args.repos,
            host_probe_root=args.host_probe_root,
            container_bundle_root=args.container_bundle_root,
            output_dir=args.output_dir,
        )

    elif args.command == "build-packet":
        cmd_build_packet(
            repo=args.repo,
            results_dir=args.results_dir,
            deep_results_dir=args.deep_results_dir,
            readiness_dir=args.readiness_dir,
            naming_audit_dir=args.naming_audit_dir,
            host_probe_root=args.host_probe_root,
            container_bundle_root=args.container_bundle_root,
            output_dir=args.output_dir,
        )
    elif args.command == "build-run-plan":
        cmd_build_run_plan(
            repo=args.repo,
            deep_results_dir=args.deep_results_dir,
            packet_dir=args.packet_dir,
            candidates_dir=args.candidates_dir,
            output_dir=args.output_dir,
            agents=args.agents,
            replications=args.replications,
        )
    elif args.command == "materialize-runs":
        cmd_materialize_runs(
            repo=args.repo,
            run_plan_dir=args.run_plan_dir,
            clones_dir=args.clones_dir,
            output_dir=args.output_dir,
            run_ids=args.run_ids,
            conditions=args.conditions,
            agents=args.agents,
            limit=args.limit,
            overwrite=args.overwrite,
        )
    elif args.command == "execute-runs":
        cmd_execute_runs(
            repo=args.repo,
            run_plan_dir=args.run_plan_dir,
            clones_dir=args.clones_dir,
            output_dir=args.output_dir,
            run_ids=args.run_ids,
            conditions=args.conditions,
            agents=args.agents,
            limit=args.limit,
            overwrite=args.overwrite,
            agent_timeout_seconds=args.agent_timeout_seconds,
        )
    elif args.command == "parse-runs":
        cmd_parse_runs(
            repo=args.repo,
            execution_dir=args.execution_dir,
            run_ids=args.run_ids,
            conditions=args.conditions,
            agents=args.agents,
            limit=args.limit,
            write_back=not args.no_write_back,
        )
    elif args.command == "analyze-runs":
        cmd_analyze_runs(
            repo=args.repo,
            stage6_dir=args.stage6_dir,
            run_ids=args.run_ids,
            conditions=args.conditions,
            agents=args.agents,
            limit=args.limit,
        )
    elif args.command == "build-task-packet":
        cmd_build_task_packet(
            repo=args.repo,
            stage7_dir=args.stage7_dir,
            candidate_id=args.candidate_id,
            agent=args.agent,
            output_dir=args.output_dir,
        )


def cmd_deep_evaluate(config: Config, candidates_dir: Path, results_dir: Path) -> None:
    """Run Stage 2 deep evaluation on Stage 1 accepted candidates."""
    from src.deep_eval.deep_judge import deep_evaluate_repo, write_deep_results

    config.output_dir.mkdir(parents=True, exist_ok=True)

    # Find Stage 1 manifests
    manifests = sorted(results_dir.glob("*_selected_prs.json"))
    if not manifests:
        print(f"No Stage 1 manifests found in {results_dir}/")
        print("Run 'evaluate' first to generate *_selected_prs.json files.")
        sys.exit(1)

    repo_filter = getattr(config, "_repo_filter", None)

    for manifest_path in manifests:
        with open(manifest_path) as f:
            manifest = json.load(f)

        repo = manifest["repo"]
        repo_short = repo.split("/")[-1]

        if repo_filter and repo_filter not in repo_short and repo_filter not in repo:
            continue

        accepted_prs = manifest.get("selected_prs", [])
        if not accepted_prs:
            print(f"No accepted PRs in {manifest_path.name}")
            continue

        print(f"\n{'='*60}")
        print(f"Deep Evaluation: {repo} ({len(accepted_prs)} candidates)")
        print(f"Provider: {config.provider} | Model: {config.model}")
        if getattr(config, "preflight_only", False):
            print("Mode: pre-flight only (no LLM evaluation)")
        elif getattr(config, "skip_preflight", False):
            print("Mode: LLM evaluation only (skipping pre-flight)")
        print(f"{'='*60}")

        results = deep_evaluate_repo(repo, accepted_prs, candidates_dir, config)
        write_deep_results(results, repo, config.output_dir, config)

        # Summary
        preflight_pass = sum(1 for r in results if r.preflight.status == "PASS")
        judged = [r for r in results if r.judge_response is not None]
        accepted = sum(1 for r in judged if r.judge_response.recommendation == "ACCEPT")

        print(f"\n  Summary: {len(results)} evaluated")
        print(f"    Pre-flight PASS: {preflight_pass}/{len(results)}")
        if judged:
            print(f"    Stage 2 ACCEPT: {accepted}/{len(judged)}")


def cmd_audit_naming(
    *,
    repo: str,
    clones_dir: Path,
    output_dir: Path,
    commit_sha: str | None,
    sample_limit: int,
    live: bool,
    keep_worktree: bool,
) -> None:
    """Generate a repo-level naming readiness report."""
    from src.workflow.repo_audit import run_repo_naming_audit

    print(f"\n{'='*60}")
    print(f"Naming Audit: {repo}")
    print(f"Mode: {'live' if live else 'dry-run'}")
    print(f"{'='*60}", flush=True)

    report_path = run_repo_naming_audit(
        repo=repo,
        clones_dir=clones_dir,
        output_dir=output_dir,
        sample_limit=sample_limit,
        live=live,
        commit_sha=commit_sha,
        keep_worktree=keep_worktree,
    )
    print(f"\nWrote naming readiness report to {report_path}")


def cmd_audit_repo(
    *,
    repo: str,
    clones_dir: Path,
    output_dir: Path,
    commit_sha: str | None,
    sample_limit: int,
    keep_worktree: bool,
) -> None:
    """Generate a repo-level degradation readiness report."""
    from src.workflow.repo_readiness import run_repo_readiness_audit

    print(f"\n{'='*60}")
    print(f"Repo Readiness Audit: {repo}")
    print(f"{'='*60}", flush=True)

    report_path = run_repo_readiness_audit(
        repo=repo,
        clones_dir=clones_dir,
        output_dir=output_dir,
        sample_limit=sample_limit,
        commit_sha=commit_sha,
        keep_worktree=keep_worktree,
    )
    print(f"\nWrote repo readiness report to {report_path}")


def cmd_build_packet(
    *,
    repo: str,
    results_dir: Path,
    deep_results_dir: Path,
    readiness_dir: Path,
    naming_audit_dir: Path | None,
    host_probe_root: Path | None,
    container_bundle_root: Path | None,
    output_dir: Path,
) -> None:
    """Assemble a repo-level review packet."""
    from src.workflow.repo_packet import build_repo_experiment_packet

    print(f"\n{'='*60}")
    print(f"Experiment Packet: {repo}")
    print(f"{'='*60}")

    packet_path = build_repo_experiment_packet(
        repo=repo,
        results_dir=results_dir,
        deep_results_dir=deep_results_dir,
        readiness_dir=readiness_dir,
        naming_audit_dir=naming_audit_dir,
        host_probe_root=host_probe_root,
        container_bundle_root=container_bundle_root,
        output_dir=output_dir,
    )
    print(f"\nWrote experiment packet to {packet_path}")


def cmd_probe_stage2(
    *,
    repo: str,
    clones_dir: Path,
    output_dir: Path,
    profiles_dir: Path,
    commits: list[str] | None,
    sample_size: int,
    install_timeout_seconds: int,
    probe_timeout_seconds: int,
    keep_worktrees: bool,
) -> None:
    """Run the profile-aware Stage 2 environment probe."""
    from src.workflow.stage2_probe import run_stage2_probe

    print(f"\n{'='*60}")
    print(f"Stage 2 Probe: {repo}")
    print(f"{'='*60}", flush=True)

    report_path = run_stage2_probe(
        repo=repo,
        clones_dir=clones_dir,
        output_dir=output_dir,
        profiles_dir=profiles_dir,
        commits=commits,
        sample_size=sample_size,
        install_timeout_seconds=install_timeout_seconds,
        probe_timeout_seconds=probe_timeout_seconds,
        keep_worktrees=keep_worktrees,
    )
    print(f"\nWrote Stage 2 probe report to {report_path}")


def cmd_prepare_stage2_container(
    *,
    repo: str,
    clones_dir: Path,
    output_dir: Path,
    profiles_dir: Path,
    commits: list[str] | None,
    sample_size: int,
) -> None:
    """Prepare container-ready Stage 2 probe bundles."""
    from src.workflow.stage2_container_bundle import prepare_stage2_container_bundles

    print(f"\n{'='*60}")
    print(f"Stage 2 Container Bundles: {repo}")
    print(f"{'='*60}", flush=True)

    bundle_path = prepare_stage2_container_bundles(
        repo=repo,
        clones_dir=clones_dir,
        output_dir=output_dir,
        profiles_dir=profiles_dir,
        commits=commits,
        sample_size=sample_size,
    )
    print(f"\nWrote Stage 2 container bundle report to {bundle_path}")


def cmd_compare_stage2_runtimes(
    *,
    repos: list[str],
    host_probe_root: Path,
    container_bundle_root: Path,
    output_dir: Path,
) -> None:
    """Compare host-vs-container Stage 2 runtime evidence across repos."""
    from src.workflow.stage2_runtime import build_stage2_runtime_comparison_matrix

    print(f"\n{'='*60}")
    print("Stage 2 Runtime Comparison")
    print(f"{'='*60}")

    output_path = build_stage2_runtime_comparison_matrix(
        repos=repos,
        host_probe_root=host_probe_root,
        container_bundle_root=container_bundle_root,
        output_dir=output_dir,
    )
    print(f"\nWrote Stage 2 runtime comparison matrix to {output_path}")


def cmd_build_run_plan(
    *,
    repo: str,
    deep_results_dir: Path,
    packet_dir: Path,
    candidates_dir: Path,
    output_dir: Path,
    agents: list[str] | None,
    replications: int,
) -> None:
    """Assemble a Stage 5 run plan for one repo."""
    from src.workflow.run_plan import build_repo_run_plan

    print(f"\n{'='*60}")
    print(f"Run Plan: {repo}")
    print(f"{'='*60}")

    plan_path = build_repo_run_plan(
        repo=repo,
        deep_results_dir=deep_results_dir,
        packet_dir=packet_dir,
        candidates_dir=candidates_dir,
        output_dir=output_dir,
        harnesses=agents,
        replications=replications,
    )
    print(f"\nWrote run plan to {plan_path}")


def cmd_materialize_runs(
    *,
    repo: str,
    run_plan_dir: Path,
    clones_dir: Path,
    output_dir: Path,
    run_ids: list[str] | None,
    conditions: list[str] | None,
    agents: list[str] | None,
    limit: int | None,
    overwrite: bool,
) -> None:
    """Materialize Stage 4 workspaces for planned runs."""
    from src.workflow.stage4_executor import materialize_stage4_runs

    print(f"\n{'='*60}")
    print(f"Stage 4 Materialization: {repo}")
    print(f"{'='*60}")

    summary_path = materialize_stage4_runs(
        repo=repo,
        run_plan_dir=run_plan_dir,
        clones_dir=clones_dir,
        output_dir=output_dir,
        run_ids=run_ids,
        conditions=conditions,
        harnesses=agents,
        limit=limit,
        overwrite=overwrite,
    )
    print(f"\nWrote Stage 4 materialization summary to {summary_path}")


def cmd_execute_runs(
    *,
    repo: str,
    run_plan_dir: Path,
    clones_dir: Path,
    output_dir: Path,
    run_ids: list[str] | None,
    conditions: list[str] | None,
    agents: list[str] | None,
    limit: int | None,
    overwrite: bool,
    agent_timeout_seconds: int,
) -> None:
    """Execute Stage 5 runs from the run-plan artifact."""
    from src.workflow.stage5_runner import execute_stage5_runs

    print(f"\n{'='*60}")
    print(f"Stage 5 Execution: {repo}")
    print(f"{'='*60}")

    summary_path = execute_stage5_runs(
        repo=repo,
        run_plan_dir=run_plan_dir,
        clones_dir=clones_dir,
        output_dir=output_dir,
        run_ids=run_ids,
        conditions=conditions,
        harnesses=agents,
        limit=limit,
        overwrite=overwrite,
        agent_timeout_seconds=agent_timeout_seconds,
    )
    print(f"\nWrote Stage 5 execution summary to {summary_path}")


def cmd_parse_runs(
    *,
    repo: str,
    execution_dir: Path,
    run_ids: list[str] | None,
    conditions: list[str] | None,
    agents: list[str] | None,
    limit: int | None,
    write_back: bool,
) -> None:
    """Parse Stage 5 artifacts into richer Stage 6 metrics."""
    from src.workflow.stage6_metrics import parse_stage6_metrics

    print(f"\n{'='*60}")
    print(f"Stage 6 Metrics: {repo}")
    print(f"{'='*60}")

    summary_path = parse_stage6_metrics(
        repo=repo,
        execution_dir=execution_dir,
        run_ids=run_ids,
        conditions=conditions,
        harnesses=agents,
        limit=limit,
        write_back=write_back,
    )
    print(f"\nWrote Stage 6 metrics summary to {summary_path}")


def cmd_analyze_runs(
    *,
    repo: str,
    stage6_dir: Path,
    run_ids: list[str] | None,
    conditions: list[str] | None,
    agents: list[str] | None,
    limit: int | None,
) -> None:
    """Aggregate Stage 6 metrics into Stage 7 analysis artifacts."""
    from src.workflow.stage7_analysis import analyze_stage7_results

    print(f"\n{'='*60}")
    print(f"Stage 7 Analysis: {repo}")
    print(f"{'='*60}")

    summary_path = analyze_stage7_results(
        repo=repo,
        stage6_dir=stage6_dir,
        run_ids=run_ids,
        conditions=conditions,
        harnesses=agents,
        limit=limit,
    )
    print(f"\nWrote Stage 7 analysis summary to {summary_path}")


def cmd_build_task_packet(
    *,
    repo: str,
    stage7_dir: Path,
    candidate_id: str,
    agent: str | None,
    output_dir: Path | None,
) -> None:
    """Build a focused Stage 7 task packet for one candidate."""
    from src.workflow.task_packet import build_task_packet

    print(f"\n{'='*60}")
    print(f"Task Packet: {repo} / {candidate_id}")
    print(f"{'='*60}")

    packet_path = build_task_packet(
        repo=repo,
        stage7_dir=stage7_dir,
        candidate_id=candidate_id,
        harness=agent,
        output_dir=output_dir,
    )
    print(f"\nWrote task packet to {packet_path}")


if __name__ == "__main__":
    main()
