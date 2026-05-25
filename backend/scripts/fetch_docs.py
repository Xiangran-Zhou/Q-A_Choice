"""Fetch the LangChain documentation corpus.

Clones the public `langchain-ai/docs` repository — the unified source
of truth for python.langchain.com and the same content the Mintlify
backend reads from — into `backend/raw_docs/` as a shallow checkout.

The `.git` directory is removed afterwards so the corpus sits as a
plain tree of `.mdx` / `.md` files, ready to be chunked and embedded
by the next milestone.

`backend/raw_docs/` is gitignored: each developer runs this script
once after cloning the project.

Usage:
    uv run python scripts/fetch_docs.py            # fetch if missing
    uv run python scripts/fetch_docs.py --force    # overwrite existing
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_URL = "https://github.com/langchain-ai/docs.git"
DEST = Path(__file__).resolve().parents[1] / "raw_docs"


def _run_git_clone(url: str, dest: Path) -> None:
    """Shallow-clone *url* into *dest*. Raises on failure."""
    subprocess.run(
        ["git", "clone", "--depth=1", url, str(dest)],
        check=True,
    )


def _strip_git_metadata(repo_root: Path) -> None:
    """Remove `.git/` so the corpus is a plain file tree."""
    git_dir = repo_root / ".git"
    if git_dir.exists():
        shutil.rmtree(git_dir)


def _count_docs(root: Path) -> tuple[int, int]:
    """Return (mdx_count, md_count) under *root*."""
    mdx = sum(1 for _ in root.rglob("*.mdx"))
    md = sum(1 for _ in root.rglob("*.md"))
    return mdx, md


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Remove existing raw_docs/ before fetching.",
    )
    args = parser.parse_args()

    if DEST.exists() and any(DEST.iterdir()):
        if not args.force:
            print(
                f"{DEST} already exists and is not empty.\n"
                f"Re-run with --force to overwrite, or delete the directory manually.",
                file=sys.stderr,
            )
            return 1
        print(f"Removing existing {DEST} ...")
        shutil.rmtree(DEST)

    print(f"Cloning {REPO_URL} into {DEST} (shallow) ...")
    try:
        _run_git_clone(REPO_URL, DEST)
    except FileNotFoundError:
        print("git is not installed or not on PATH.", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"git clone failed (exit {exc.returncode}).", file=sys.stderr)
        return exc.returncode

    _strip_git_metadata(DEST)

    mdx, md = _count_docs(DEST)
    if mdx + md == 0:
        print(
            f"WARNING: no .mdx / .md files found in {DEST}. "
            "The repository layout may have changed.",
            file=sys.stderr,
        )
        return 1

    print(f"Done. {mdx} .mdx and {md} .md files under {DEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
