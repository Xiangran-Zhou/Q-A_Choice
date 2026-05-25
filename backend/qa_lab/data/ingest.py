"""Chunk loaded documents and embed them into a persistent Chroma store.

This is the shared retrieval index used by all three paradigms — the
RAG graph queries it directly, the Agentic graph wraps it in a tool,
and the GraphRAG graph uses it as one of several retrieval signals.

Configuration (single source of truth):

- Chunk size:    1,000 characters
- Chunk overlap: 200 characters
- Embedding:     OpenAI `text-embedding-3-small`
- Persist dir:   `backend/chroma_db/`
- Collection:    `langchain_docs`

The chunking config matches the plan and is intentionally not tuned —
this is a baseline meant to be honest about what "default RAG" looks
like.
"""

from __future__ import annotations

from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from qa_lab.data.loader import BACKEND_ROOT

CHROMA_DIR: Path = BACKEND_ROOT / "chroma_db"
COLLECTION_NAME = "langchain_docs"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
EMBEDDING_MODEL = "text-embedding-3-small"


def split_documents(docs: list[Document]) -> list[Document]:
    """Split documents into ~1k-char chunks with 200-char overlap."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    return splitter.split_documents(docs)


def get_embeddings() -> OpenAIEmbeddings:
    """Return the configured embedding model."""
    return OpenAIEmbeddings(model=EMBEDDING_MODEL)


def get_vector_store() -> Chroma:
    """Open (or create) the persistent Chroma collection."""
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=get_embeddings(),
        persist_directory=str(CHROMA_DIR),
    )


def count_existing_chunks(store: Chroma) -> int:
    """How many chunks are already indexed? Used for idempotency checks."""
    try:
        return store._collection.count()
    except Exception:
        return 0
