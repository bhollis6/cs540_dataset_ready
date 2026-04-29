from pathlib import Path


REMOVABLE_TEST_PATTERNS = (
    "test_*.py",
    "*_test.py",
    "tests.py",
)

PRESERVED_TEST_SUPPORT = {
    "conftest.py",
}

def strip_test_harness(repo_path: str, dry_run: bool = True):
    target_dir = Path(repo_path)
    if not target_dir.is_dir():
        print(f"Error: '{repo_path}' is not a valid directory.")
        return

    # Preserve test infrastructure so the agent can still write and run new tests.
    protected_extensions = {'.pyi'}
    protected_dir_names = {'stubs', 'typing', 'typings'}

    print(f"Scanning '{target_dir}' for test artifacts... (Dry run: {dry_run})\n")

    files_to_delete = []

    for path in target_dir.rglob('*'):
        # Enforce Safe Lists
        if path.suffix in protected_extensions:
            continue
        if any(protected_dir in path.parts for protected_dir in protected_dir_names):
            continue

        if not path.is_file():
            continue

        if path.name in PRESERVED_TEST_SUPPORT:
            continue

        if any(path.match(pattern) for pattern in REMOVABLE_TEST_PATTERNS):
            files_to_delete.append(path)

    for f in files_to_delete:
        print(f"[FILE] {f}")
        if not dry_run:
            f.unlink()

    print("-" * 50)
    if dry_run:
        print(f"DRY RUN: Flagged {len(files_to_delete)} files.")
        print("Set `dry_run=False` to execute.")
    else:
        print(f"DELETED: {len(files_to_delete)} files.")

if __name__ == "__main__":
    # Dry run = False, permantely delete
    # Insert repo directory for first parameter
    import sys
    target = sys.argv[1]
    strip_test_harness(target, dry_run=False)
