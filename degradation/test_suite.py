import shutil
from pathlib import Path

def strip_test_harness(repo_path: str, dry_run: bool = True):
    target_dir = Path(repo_path)
    if not target_dir.is_dir():
        print(f"Error: '{repo_path}' is not a valid directory.")
        return

    # --- TARGET LISTS ---
    # Standard tests, caches, coverage, and mock data
    target_dirs = {
        'tests', 'test', 'testing', '.pytest_cache', 
        '.tox', '.nox', 'htmlcov', '__snapshots__', 
        'fixtures', 'test_data'
    }
    
    # Framework files, configuration, and coverage metrics
    target_file_patterns = [
        'test_*.py', '*_test.py', 'tests.py', 'conftest.py', 
        'tox.ini', 'pytest.ini', 'noxfile.py', '.coverage', 'coverage.xml'
    ]

    # --- SAFE LISTS ---
    # Protected directories and files to preserve the static type graph 
    # for static analysis and AI coding agents.
    protected_extensions = {'.pyi'}
    protected_dir_names = {'stubs', 'typing', 'typings'}

    print(f"Scanning '{target_dir}' for test artifacts... (Dry run: {dry_run})\n")

    dirs_to_delete = []
    files_to_delete = []

    for path in target_dir.rglob('*'):
        # 1. Skip if already inside a directory marked for deletion
        if any(parent in dirs_to_delete for parent in path.parents):
            continue
            
        # 2. Enforce Safe Lists
        if path.suffix in protected_extensions:
            continue
        if any(protected_dir in path.parts for protected_dir in protected_dir_names):
            continue

        # 3. Flag Directories
        if path.is_dir() and path.name in target_dirs:
            dirs_to_delete.append(path)
            
        # 4. Flag Files
        elif path.is_file() and any(path.match(pattern) for pattern in target_file_patterns):
            files_to_delete.append(path)

    # Execute Deletions
    for d in dirs_to_delete:
        print(f"[DIR]  {d}")
        if not dry_run:
            shutil.rmtree(d)

    for f in files_to_delete:
        print(f"[FILE] {f}")
        if not dry_run:
            f.unlink()

    print("-" * 50)
    if dry_run:
        print(f"DRY RUN: Flagged {len(dirs_to_delete)} directories and {len(files_to_delete)} files.")
        print("Set `dry_run=False` to execute.")
    else:
        print(f"DELETED: {len(dirs_to_delete)} directories and {len(files_to_delete)} files.")

if __name__ == "__main__":
    # Dry run = False, permantely delete
    # Insert repo directory for first parameter
    import sys
    target = sys.argv[1]
    strip_test_harness(target, dry_run=False)