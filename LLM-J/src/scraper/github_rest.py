"""GitHub REST API client for fetching PR diffs."""

from __future__ import annotations

import time

import requests

from src.scraper.models import CandidatePR, PRMetadata, _is_test_file


def fetch_pr_diff(
    repo: str,
    pr_metadata: PRMetadata,
    token: str,
) -> CandidatePR | None:
    """Fetch the raw diff for a PR and construct a CandidatePR.

    Returns None if the diff could not be fetched.
    """
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_metadata.pr_number}"

    try:
        response = requests.get(
            url,
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.diff",
            },
            timeout=30,
        )

        # Rate limit handling
        remaining = int(response.headers.get("X-RateLimit-Remaining", 100))
        if remaining < 50:
            reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
            wait = max(0, reset_time - int(time.time())) + 1
            print(f"\n    Rate limit low ({remaining} remaining), waiting {wait}s...")
            time.sleep(wait)

        response.raise_for_status()
        raw_diff = response.text

    except requests.RequestException as e:
        print(f"Error fetching diff for PR #{pr_metadata.pr_number}: {e}")
        return None

    # Split diff into patch (source) and test portions
    patch_diff, test_diff = _split_diff(raw_diff)

    repo_short = repo.split("/")[-1]
    candidate_id = f"{repo_short}_pr_{pr_metadata.pr_number}"

    return CandidatePR(
        candidate_id=candidate_id,
        repo=repo,
        pr_number=pr_metadata.pr_number,
        title=pr_metadata.title,
        description=pr_metadata.body,
        patch_diff=patch_diff,
        test_diff=test_diff,
        files_changed=pr_metadata.file_paths,
        source_files=pr_metadata.source_files,
        test_files=pr_metadata.test_files,
        test_support_files=pr_metadata.test_support_files,
        lines_added=pr_metadata.additions,
        lines_removed=pr_metadata.deletions,
        has_test_changes=pr_metadata.has_test_changes,
        merge_commit_sha=pr_metadata.merge_commit_sha,
        base_commit_sha=pr_metadata.base_commit_sha,
        env_commit_sha=pr_metadata.base_commit_sha,
        head_commit_sha=pr_metadata.head_commit_sha,
        merged_at=pr_metadata.merged_at,
    )


def _split_diff(raw_diff: str) -> tuple[str, str]:
    """Split a unified diff into source changes and test changes.

    Splits on 'diff --git' boundaries, classifying each file's hunk
    as test or source based on the file path.
    """
    if not raw_diff:
        return "", ""

    # Split into per-file chunks
    chunks = raw_diff.split("diff --git ")
    patch_parts: list[str] = []
    test_parts: list[str] = []

    for chunk in chunks:
        if not chunk.strip():
            continue

        # Reconstruct the full chunk header
        full_chunk = "diff --git " + chunk

        # Extract file paths from the diff header (a/path b/path)
        first_line = chunk.split("\n", 1)[0]
        parts = first_line.split()
        if len(parts) >= 2:
            # Use b/ path (the destination)
            file_path = parts[-1].lstrip("b/")
        else:
            file_path = ""

        if _is_test_file(file_path):
            test_parts.append(full_chunk)
        else:
            patch_parts.append(full_chunk)

    return "".join(patch_parts), "".join(test_parts)
