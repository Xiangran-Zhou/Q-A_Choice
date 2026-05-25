"""Retriever construction: vector, BM25, and the hybrid ensemble.

Three retrievers, one corpus:

- **Vector**: dense semantic retrieval against the Chroma index built
  by `scripts/ingest.py`.
- **BM25**: lexical retrieval over the same chunks (loaded from
  `chunks.pkl`, written alongside the Chroma index during ingest).
- **Hybrid**: an `EnsembleRetriever` combining the two via reciprocal
  rank fusion. This is the default `rag_graph` retriever — matches the
  project plan's "vector + BM25 hybrid" baseline.

The BM25 chunks file is stored next to the Chroma directory so the two
caches stay in sync (wipe one, wipe both).
"""

from __future__ import annotations

import pickle
from pathlib import Path

from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from qa_lab.data.ingest import CHROMA_DIR, get_vector_store

BM25_CHUNKS_PATH: Path = CHROMA_DIR / "bm25_chunks.pkl"

DEFAULT_K = 5
DEFAULT_WEIGHTS = (0.5, 0.5)  # (vector, bm25)


def save_chunks_for_bm25(chunks: list[Document]) -> None:
    """Persist the split chunks for BM25 to reload at startup."""
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    with BM25_CHUNKS_PATH.open("wb") as f:
        pickle.dump(chunks, f)


def load_chunks_for_bm25() -> list[Document]:
    """Reload the persisted chunks. Raises if the file is missing."""
    if not BM25_CHUNKS_PATH.exists():
        raise FileNotFoundError(
            f"{BM25_CHUNKS_PATH} not found. Run `uv run python scripts/ingest.py` first."
        )
    with BM25_CHUNKS_PATH.open("rb") as f:
        return pickle.load(f)


def get_vector_retriever(k: int = DEFAULT_K) -> BaseRetriever:
    """Dense retrieval via the Chroma vector store."""
    return get_vector_store().as_retriever(search_kwargs={"k": k})


def get_bm25_retriever(k: int = DEFAULT_K) -> BM25Retriever:
    """Lexical retrieval via BM25 over the same chunks as the vector store."""
    chunks = load_chunks_for_bm25()
    retriever = BM25Retriever.from_documents(chunks)
    retriever.k = k
    return retriever


def get_hybrid_retriever(
    k: int = DEFAULT_K,
    weights: tuple[float, float] = DEFAULT_WEIGHTS,
) -> EnsembleRetriever:
    """Vector + BM25 fused via reciprocal rank fusion.

    `weights` is `(vector_weight, bm25_weight)`. Both retrievers fetch
    `k` results each before RRF merging.
    """
    return EnsembleRetriever(
        retrievers=[get_vector_retriever(k=k), get_bm25_retriever(k=k)],
        weights=list(weights),
    )
