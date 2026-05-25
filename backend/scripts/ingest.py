"""Run the full ingest pipeline: load → split → embed → write to Chroma.

End-to-end:

    uv run python scripts/ingest.py            # ingest if Chroma is empty
    uv run python scripts/ingest.py --reset    # wipe Chroma first, then ingest

After ingestion, runs a smoke query against the new index so the script
fails loudly if retrieval is broken — not silently three commits later.

Loads `OPENAI_API_KEY` from `.env` at the project root via python-dotenv.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import time

from dotenv import find_dotenv, load_dotenv

from qa_lab.data.ingest import (
    CHROMA_DIR,
    count_existing_chunks,
    get_vector_store,
    split_documents,
)
from qa_lab.data.loader import load_documents

EMBED_BATCH_SIZE = 500
SMOKE_QUERY = "How does LangGraph's interrupt function work?"
SMOKE_K = 3


def _human_time(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, secs = divmod(seconds, 60)
    return f"{int(minutes)}m{int(secs)}s"


def _smoke_test(store) -> None:
    print(f"\nSmoke test — query: {SMOKE_QUERY!r}")
    results = store.similarity_search(SMOKE_QUERY, k=SMOKE_K)
    if not results:
        print("  WARNING: zero results. Index may be broken.")
        return
    for i, doc in enumerate(results, 1):
        source = doc.metadata.get("source", "(unknown)")
        preview = doc.page_content[:120].replace("\n", " ").strip()
        print(f"  [{i}] {source}")
        print(f"      {preview}...")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete the existing Chroma store before ingesting.",
    )
    args = parser.parse_args()

    # Load .env from project root so OPENAI_API_KEY is available.
    load_dotenv(find_dotenv(usecwd=True))

    # Handle existing index.
    if args.reset and CHROMA_DIR.exists():
        print(f"Wiping existing index at {CHROMA_DIR} ...")
        shutil.rmtree(CHROMA_DIR)

    store = get_vector_store()
    existing = count_existing_chunks(store)
    if existing > 0 and not args.reset:
        print(
            f"Chroma already contains {existing} chunks. "
            "Re-run with --reset to rebuild, or query the existing store.",
            file=sys.stderr,
        )
        _smoke_test(store)
        return 0

    # ---- Load ----
    print("Loading documents from raw_docs/ ...")
    t0 = time.time()
    docs = load_documents()
    print(f"  Loaded {len(docs):,} files in {_human_time(time.time() - t0)}")
    if not docs:
        print("ERROR: zero documents loaded. Did you run fetch_docs.py?", file=sys.stderr)
        return 1

    # ---- Split ----
    print("Splitting into chunks ...")
    t0 = time.time()
    chunks = split_documents(docs)
    total_chars = sum(len(c.page_content) for c in chunks)
    print(
        f"  Produced {len(chunks):,} chunks "
        f"({total_chars:,} chars) in {_human_time(time.time() - t0)}"
    )

    # ---- Embed + write ----
    print(f"Embedding into {CHROMA_DIR} (batch={EMBED_BATCH_SIZE}) ...")
    t0 = time.time()
    for i in range(0, len(chunks), EMBED_BATCH_SIZE):
        batch = chunks[i : i + EMBED_BATCH_SIZE]
        store.add_documents(batch)
        done = i + len(batch)
        elapsed = time.time() - t0
        rate = done / elapsed if elapsed else 0
        print(f"  {done:,} / {len(chunks):,}  ({rate:.0f} chunks/s)")
    print(f"  Embedded {len(chunks):,} chunks in {_human_time(time.time() - t0)}")

    # ---- Smoke test ----
    _smoke_test(store)
    return 0


if __name__ == "__main__":
    sys.exit(main())
