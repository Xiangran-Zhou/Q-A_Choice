"""Tools exposed to the Agentic Search graph.

Two minimal tools, intentionally kept simple — the goal of the first
agentic pass is to show that an agent loop can decompose a question
into multiple retrieval steps, not to compete with the hand-crafted
retrieval stack inside `chat-langchain`'s production support bot.

- `search_docs_vector(query)`: hybrid (vector + BM25) retrieval over
  the same chunks the RAG graph uses. Returns formatted top-k results
  with source paths and content previews.
- `read_doc_file(source_path)`: read a full `.mdx` file by its
  `src/...` path. Useful for drilling into a specific page after a
  vector search reveals it.

Together these let the agent do "search broadly → drill in" without
needing a Mintlify-style hosted API or shell access.
"""

from __future__ import annotations

from pathlib import Path

from langchain_core.tools import tool

from qa_lab.data.loader import RAW_DOCS_ROOT
from qa_lab.data.retriever import get_hybrid_retriever

SEARCH_K = 5
CHUNK_PREVIEW_CHARS = 600
MAX_FILE_CHARS = 12_000


@tool
def search_docs_vector(query: str) -> str:
    """Search the LangChain documentation by semantic + keyword similarity.

    Uses a hybrid retriever (Chroma vector store + BM25 over the same
    chunks). Returns up to 5 chunks, each labeled with a source path
    you can pass to `read_doc_file` if you need the full file.

    Use this for: open-ended exploration, "where is X documented?", or
    when you need multiple candidate sources.
    """
    retriever = get_hybrid_retriever(k=SEARCH_K)
    chunks = retriever.invoke(query)
    if not chunks:
        return "No matching documentation found."
    blocks: list[str] = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.metadata.get("source", "(unknown)")
        preview = chunk.page_content[:CHUNK_PREVIEW_CHARS]
        blocks.append(f"[{i}] Source: {source}\n{preview}")
    return "\n\n---\n\n".join(blocks)


@tool
def read_doc_file(source_path: str) -> str:
    """Read a documentation file by its path under `raw_docs/`.

    The path should look like `src/oss/langgraph/interrupts.mdx` —
    exactly the form `search_docs_vector` reports.

    Use this when a vector-search result looks promising but truncated,
    and you need the full surrounding context before answering.
    """
    # Defend against absolute paths or `..` escapes.
    candidate = (RAW_DOCS_ROOT / source_path).resolve()
    try:
        candidate.relative_to(RAW_DOCS_ROOT.resolve())
    except ValueError:
        return f"Refused to read {source_path!r}: outside raw_docs/."

    if not candidate.exists():
        return f"File not found: {source_path}"
    if not candidate.is_file():
        return f"Not a file: {source_path}"

    try:
        content = candidate.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as exc:
        return f"Could not read {source_path}: {exc}"

    if len(content) > MAX_FILE_CHARS:
        content = (
            content[:MAX_FILE_CHARS]
            + f"\n\n... [truncated; full file is {len(content):,} chars]"
        )
    return content


AGENTIC_TOOLS = [search_docs_vector, read_doc_file]
