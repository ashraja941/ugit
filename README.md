uGit
====

A educational reimplementation of core Git plumbing written in Python. The goal of this project is to understand how Git works by rebuilding the basics from scratch.

## Getting Started

1. Ensure you have Python 3.11+ available.
2. Install the project locally:
   ```bash
   pip install -e .
   ```
3. From any directory you want to version, run:
   ```bash
   ugit init
   ```

All repository data is stored under a `.ugit/` directory alongside your files.

## Available Commands

The CLI mirrors a minimal subset of Git and is intentionally small:

- `ugit hash-object <file>`: Store a blob and print its object id.
- `ugit write-tree`: Snapshot the working directory as a tree object.
- `ugit commit -m "<message>"`: Create a commit tracking the current tree.
- `ugit log [oid]`: Walk commit history, defaulting to `HEAD`.
- `ugit checkout <oid>`: Restore the working tree to a given commit.
- `ugit tag <name> [oid]`: Create a lightweight tag pointing at a commit.
- `ugit read-tree <tree-oid>` / `ugit cat-file <oid>`: Inspect stored objects.
- `ugit k`: List all refs recorded in `.ugit/refs`.
