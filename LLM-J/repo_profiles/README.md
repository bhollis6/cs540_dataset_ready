# Repo Profiles

This directory is reserved for repo-specific historical execution profiles.

Profiles are intended to capture repo-owned execution knowledge outside generic
workflow code, such as:

- Python version
- package manager choice
- install commands
- dependency pins
- test command
- plugin policy
- env vars
- known historical quirks

Early migration rule:
- profile support may be loaded and surfaced before it changes runtime behavior
- behavior should stay backward-compatible until Stage 2 containerization is ready

Current file format:
- JSON

Expected file naming:
- `owner__repo.json`

Example:
- `encode__httpx.json`
