"""Build the LightRAG knowledge graph from raw_docs/.

Reads `.mdx` files via `qa_lab.data.loader.load_documents()` (the same
corpus the Chroma index uses) and inserts them into a LightRAG store
at `backend/lightrag_storage/`. LightRAG handles chunking, entity +
relation extraction, embedding, and graph construction internally.

The build is **incremental and idempotent**: re-running picks up where
it left off, so a long build can be interrupted and resumed.

Usage (from the project root):

    cd backend

    # Smoke test on the first 5 documents (~1-2 min, ~$0.20):
    uv run python scripts/build_graph.py --limit 5

    # Full corpus (~1500 docs, overnight, ~$15-30 estimated):
    uv run python scripts/build_graph.py

    # Resume / re-attempt a partially-built store:
    uv run python scripts/build_graph.py --resume

Costs and timings are dominated by the LLM-driven entity / relation
extraction step. Watch `backend/lightrag_storage/` size for progress.
"""

from __future__ import annotations

import argparse
import asyncio
import shutil
import sys
import time

from dotenv import find_dotenv, load_dotenv

from qa_lab.data.graph_builder import LIGHTRAG_DIR, make_rag
from qa_lab.data.loader import load_documents


def _human_time(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    if seconds < 3600:
        m, s = divmod(seconds, 60)
        return f"{int(m)}m{int(s)}s"
    h, rem = divmod(seconds, 3600)
    m, _ = divmod(rem, 60)
    return f"{int(h)}h{int(m)}m"


async def _build(limit: int | None) -> int:
    print("Loading documents from raw_docs/ ...")
    t0 = time.time()
    docs = load_documents()
    if limit is not None:
        docs = docs[:limit]
    print(f"  Loaded {len(docs):,} files in {_human_time(time.time() - t0)}")
    if not docs:
        print("ERROR: zero documents loaded. Did you run fetch_docs.py?", file=sys.stderr)
        return 1

    print(f"Initializing LightRAG at {LIGHTRAG_DIR} ...")
    LIGHTRAG_DIR.mkdir(parents=True, exist_ok=True)
    rag = make_rag()
    await rag.initialize_storages()

    try:
        # LightRAG accepts a list of strings + a parallel list of ids
        # for source tracking. Use the file path as the id so the
        # graph keeps provenance per document.
        contents = [d.page_content for d in docs]
        ids = [d.metadata["source"] for d in docs]

        print(f"Inserting {len(contents):,} document(s) ...")
        t0 = time.time()
        await rag.ainsert(contents, ids=ids)
        print(f"  ainsert returned in {_human_time(time.time() - t0)}")
    finally:
        await rag.finalize_storages()

    print(f"\nDone. LightRAG store is at {LIGHTRAG_DIR}.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only process the first N documents (smoke-test mode).",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete the existing lightrag_storage/ before building.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Keep existing storage (default). Documented for clarity.",
    )
    args = parser.parse_args()

    load_dotenv(find_dotenv(usecwd=True))

    if args.reset and LIGHTRAG_DIR.exists():
        print(f"Wiping {LIGHTRAG_DIR} (--reset) ...")
        shutil.rmtree(LIGHTRAG_DIR)

    return asyncio.run(_build(args.limit))


if __name__ == "__main__":
    sys.exit(main())
