"""Tests for heuristic pre-filtering logic."""

from src.scraper.filters import apply_filters
from src.scraper.models import PRMetadata


def _make_pr(**overrides) -> PRMetadata:
    """Create a PRMetadata with sensible defaults, overriding as needed."""
    defaults = {
        "pr_number": 1,
        "title": "Fix something",
        "body": "This fixes a bug where things break unexpectedly.",
        "additions": 50,
        "deletions": 10,
        "changed_files_count": 3,
        "file_paths": ["src/main.py", "tests/test_main.py"],
        "merge_commit_sha": "abc123",
        "base_commit_sha": "def456",
        "head_commit_sha": "ghi789",
        "merged_at": "2024-01-01T00:00:00Z",
        "author_login": "developer",
        "is_bot": False,
    }
    defaults.update(overrides)
    return PRMetadata(**defaults)


class FakeConfig:
    min_lines_changed = 5
    max_lines_changed = 500
    max_files_changed = 20
    min_description_length = 20
    skip_bot_prs = True
    target_candidates = None


def test_good_pr_passes_all_filters():
    pr = _make_pr()
    survivors, stats = apply_filters([pr], FakeConfig())
    assert len(survivors) == 1
    assert stats.passed == 1


def test_no_test_changes_filtered():
    pr = _make_pr(file_paths=["src/main.py", "src/utils.py"])
    survivors, stats = apply_filters([pr], FakeConfig())
    assert len(survivors) == 0
    assert stats.no_test_changes == 1


def test_test_only_filtered():
    pr = _make_pr(file_paths=["tests/test_main.py", "tests/test_utils.py"])
    survivors, stats = apply_filters([pr], FakeConfig())
    assert len(survivors) == 0
    assert stats.test_only == 1


def test_too_few_lines_filtered():
    pr = _make_pr(additions=2, deletions=1)
    survivors, stats = apply_filters([pr], FakeConfig())
    assert len(survivors) == 0
    assert stats.too_few_lines == 1


def test_too_many_lines_filtered():
    pr = _make_pr(additions=400, deletions=200)
    survivors, stats = apply_filters([pr], FakeConfig())
    assert len(survivors) == 0
    assert stats.too_many_lines == 1


def test_too_many_files_filtered():
    files = [f"src/file{i}.py" for i in range(25)] + ["tests/test_x.py"]
    pr = _make_pr(file_paths=files, changed_files_count=26)
    survivors, stats = apply_filters([pr], FakeConfig())
    assert len(survivors) == 0
    assert stats.too_many_files == 1


def test_non_code_only_filtered():
    # Source files are all non-code (markdown, config), plus a test file
    # This hits test_only first since _is_non_code_file filters README.md out of source_files
    pr = _make_pr(file_paths=["README.md", "docs/guide.md", "tests/test_x.py"])
    survivors, stats = apply_filters([pr], FakeConfig())
    assert len(survivors) == 0
    # Filtered as test_only because README.md/docs are non-code, leaving no source files
    assert stats.test_only == 1


def test_config_plus_test_only_filtered():
    # .yml/.cfg are non-code, so source_files is empty -> caught as test_only
    pr = _make_pr(file_paths=["config.yml", "setup.cfg", "tests/test_x.py"])
    survivors, stats = apply_filters([pr], FakeConfig())
    assert len(survivors) == 0
    assert stats.test_only == 1


def test_empty_description_filtered():
    pr = _make_pr(body="short")
    survivors, stats = apply_filters([pr], FakeConfig())
    assert len(survivors) == 0
    assert stats.empty_description == 1


def test_bot_pr_filtered():
    pr = _make_pr(author_login="dependabot[bot]", is_bot=True)
    survivors, stats = apply_filters([pr], FakeConfig())
    assert len(survivors) == 0
    assert stats.bot_pr == 1


def test_bot_pr_passes_when_skip_disabled():
    config = FakeConfig()
    config.skip_bot_prs = False
    pr = _make_pr(author_login="dependabot[bot]", is_bot=True)
    survivors, stats = apply_filters([pr], config)
    assert len(survivors) == 1


def test_target_candidates_early_stop():
    config = FakeConfig()
    config.target_candidates = 2
    prs = [_make_pr(pr_number=i) for i in range(10)]
    survivors, stats = apply_filters(prs, config)
    assert len(survivors) == 2


def test_multiple_prs_mixed():
    prs = [
        _make_pr(pr_number=1),  # good
        _make_pr(pr_number=2, file_paths=["src/main.py"]),  # no tests
        _make_pr(pr_number=3),  # good
        _make_pr(pr_number=4, additions=2, deletions=1),  # too small
    ]
    survivors, stats = apply_filters(prs, FakeConfig())
    assert len(survivors) == 2
    assert stats.no_test_changes == 1
    assert stats.too_few_lines == 1
    assert stats.passed == 2
