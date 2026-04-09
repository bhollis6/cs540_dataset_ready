"""GitHub GraphQL API client for bulk PR metadata fetching."""

from __future__ import annotations

import time

import requests

from src.scraper.models import PRMetadata

GRAPHQL_URL = "https://api.github.com/graphql"

PR_QUERY = """
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    pullRequests(
      states: MERGED,
      first: 100,
      after: $cursor,
      orderBy: {field: UPDATED_AT, direction: DESC}
    ) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        number
        title
        body
        additions
        deletions
        changedFiles
        mergeCommit {
          oid
        }
        baseRefOid
        headRefOid
        merged
        mergedAt
        author {
          login
        }
      }
    }
  }
}
"""

# Separate query for file paths — avoids hitting GraphQL complexity limits
# by not nesting files inside the bulk PR query
FILES_QUERY = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      files(first: 100) {
        pageInfo {
          hasNextPage
        }
        nodes {
          path
          additions
          deletions
          changeType
        }
      }
    }
  }
}
"""


def _graphql_request(query: str, variables: dict, token: str, max_retries: int = 3) -> dict:
    """Execute a GraphQL query against the GitHub API with retry on transient errors."""
    for attempt in range(max_retries):
        response = requests.post(
            GRAPHQL_URL,
            json={"query": query, "variables": variables},
            headers={
                "Authorization": f"bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )

        if response.status_code in (502, 503, 504) and attempt < max_retries - 1:
            wait = 2 ** attempt  # 1s, 2s, 4s
            print(f"    GitHub returned {response.status_code}, retrying in {wait}s...")
            time.sleep(wait)
            continue

        response.raise_for_status()
        break

    data = response.json()

    if "errors" in data:
        error_msgs = "; ".join(e.get("message", str(e)) for e in data["errors"])
        raise RuntimeError(f"GraphQL errors: {error_msgs}")

    return data["data"]


def _parse_pr_node(node: dict) -> PRMetadata:
    """Parse a single PR node from the GraphQL response (without file paths yet)."""
    author = node.get("author") or {}
    author_login = author.get("login", "")
    is_bot = author_login.endswith("[bot]") or author_login.endswith("-bot")

    merge_commit = node.get("mergeCommit") or {}

    return PRMetadata(
        pr_number=node["number"],
        title=node.get("title", ""),
        body=node.get("body", "") or "",
        additions=node.get("additions", 0),
        deletions=node.get("deletions", 0),
        changed_files_count=node.get("changedFiles", 0),
        file_paths=[],  # populated later via FILES_QUERY
        merge_commit_sha=merge_commit.get("oid"),
        base_commit_sha=node.get("baseRefOid"),
        head_commit_sha=node.get("headRefOid"),
        merged_at=node.get("mergedAt"),
        author_login=author_login,
        is_bot=is_bot,
    )


def _fetch_file_paths(owner: str, name: str, pr_number: int, token: str) -> list[str]:
    """Fetch file paths for a single PR."""
    data = _graphql_request(
        FILES_QUERY,
        {"owner": owner, "name": name, "number": pr_number},
        token,
    )
    pr_data = data["repository"]["pullRequest"]
    files_data = pr_data.get("files", {})
    nodes = files_data.get("nodes", [])

    if files_data.get("pageInfo", {}).get("hasNextPage"):
        print(f"    Warning: PR #{pr_number} has >100 files, list truncated")

    return [n["path"] for n in nodes]


def fetch_pr_metadata(
    repo: str,
    token: str,
    max_prs: int = 300,
) -> list[PRMetadata]:
    """Fetch merged PR metadata from a GitHub repo using GraphQL.

    Returns PRMetadata objects with file_paths populated.
    Paginates automatically up to max_prs.
    """
    owner, name = repo.split("/")
    all_prs: list[PRMetadata] = []
    cursor: str | None = None

    while len(all_prs) < max_prs:
        data = _graphql_request(
            PR_QUERY,
            {"owner": owner, "name": name, "cursor": cursor},
            token,
        )

        pr_connection = data["repository"]["pullRequests"]
        nodes = pr_connection["nodes"]

        if not nodes:
            break

        for node in nodes:
            pr = _parse_pr_node(node)
            all_prs.append(pr)

            if len(all_prs) >= max_prs:
                break

        page_info = pr_connection["pageInfo"]
        if not page_info["hasNextPage"]:
            break
        cursor = page_info["endCursor"]

    # Fetch file paths for each PR (needed for pre-filtering)
    print(f"  Fetching file lists for {len(all_prs)} PRs...")
    for i, pr in enumerate(all_prs):
        pr.file_paths = _fetch_file_paths(owner, name, pr.pr_number, token)
        if (i + 1) % 50 == 0:
            print(f"    ...{i + 1}/{len(all_prs)}")

    return all_prs
