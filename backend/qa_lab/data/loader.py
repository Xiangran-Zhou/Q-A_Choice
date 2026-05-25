"""Load LangChain documentation `.mdx` / `.md` files into LangChain Documents.

Walks `backend/raw_docs/src/<included>/` and wraps each text file in a
`Document` with `source` metadata (path relative to `raw_docs/`).

Only the `oss` (open-source library docs) and `langsmith` (product docs)
subtrees are loaded — these are the human-written content. We skip
`snippets/`, `code-samples/`, `images/`, `fonts/`, and other support
directories because they are either referenced from the main pages or
binary assets.

Run as a module to count documents without embedding anything:

    uv run python -m qa_lab.data.loader
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from langchain_core.documents import Document

BACKEND_ROOT = Path(__file__).resolve().parents[2]
RAW_DOCS_ROOT = BACKEND_ROOT / "raw_docs"
SRC_ROOT = RAW_DOCS_ROOT / "src"

# Directories under `src/` to ingest. Everything else is skipped.
INCLUDED_SUBDIRS: tuple[str, ...] = ("oss", "langsmith")

# File extensions to load.
EXTENSIONS: tuple[str, ...] = (".mdx", ".md")

# Skip near-empty files (table of contents stubs, empty placeholders, etc).
MIN_CONTENT_CHARS = 50


def _iter_doc_files(roots: Iterable[Path]) -> Iterable[Path]:
    for root in roots:
        if not root.exists():
            continue
        for ext in EXTENSIONS:
            yield from root.rglob(f"*{ext}")


def load_documents() -> list[Document]:
    """Load every `.mdx` / `.md` under the included subdirectories of `raw_docs/`.

    Returns:
        A list of `Document` objects, one per file, with `source` metadata
        set to the file path relative to `raw_docs/`.
    """
    if not SRC_ROOT.exists():
        raise FileNotFoundError(
            f"{SRC_ROOT} does not exist. Run `uv run python scripts/fetch_docs.py` first."
        )

    roots = [SRC_ROOT / d for d in INCLUDED_SUBDIRS]
    docs: list[Document] = []
    skipped = 0

    for path in _iter_doc_files(roots):
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            skipped += 1
            continue

        if len(content.strip()) < MIN_CONTENT_CHARS:
            skipped += 1
            continue

        rel_path = path.relative_to(RAW_DOCS_ROOT)
        docs.append(
            Document(
                page_content=content,
                metadata={"source": str(rel_path)},
            )
        )

    if skipped:
        print(f"  (skipped {skipped} files: unreadable or too short)")

    return docs


if __name__ == "__main__":
    docs = load_documents()
    print(f"Loaded {len(docs)} documents from {SRC_ROOT}")
    if docs:
        total_chars = sum(len(d.page_content) for d in docs)
        avg_chars = total_chars // len(docs)
        print(f"  Total characters: {total_chars:,}")
        print(f"  Average per doc:  {avg_chars:,}")
        print(f"  Sample source:    {docs[0].metadata['source']}")
