"""LightRAG-backed knowledge-graph builder + query handle.

Centralises the LightRAG configuration that both the build script and
the query-time `graphrag_graph` need. The corpus is the same set of
`.mdx` files RAG and Agentic see (loaded via `qa_lab.data.loader`), so
the three paradigms remain comparable.

Configuration choices:

- **LLM for extraction + generation**: Gemini 2.5 Flash, matching the
  generator used by RAG and Agentic.
- **Embeddings**: OpenAI `text-embedding-3-small` (1536 dims), the same
  model that powers the shared Chroma index.
- **Working directory**: `backend/lightrag_storage/` (gitignored).
  LightRAG persists its KV store, graph (NetworkX), and vector store
  here.
- **Storage backends**: default NetworkX + NanoVectorDB + JSON KV.
  Fine for a local demo; Neo4j/PostgreSQL backends are swap-in if we
  ever scale.

The builder is **incremental**: re-inserting the same documents is a
no-op thanks to LightRAG's content-hash dedup. So a partial build can
be resumed by re-running the script with the same arguments.
"""

from __future__ import annotations

import os
from pathlib import Path

from lightrag import LightRAG, QueryParam
from lightrag.llm.gemini import gemini_complete_if_cache
from lightrag.llm.openai import openai_embed

from qa_lab.data.loader import BACKEND_ROOT

LIGHTRAG_DIR: Path = BACKEND_ROOT / "lightrag_storage"
LLM_MODEL = "gemini-2.5-flash"


def _resolve_gemini_key() -> str | None:
    """Pick the Gemini API key for GraphRAG-related work (build + query).

    Preference order so each paradigm can be bound to its own GCP
    project / daily quota without breaking older single-key setups:

      1. ``GOOGLE_API_KEY_GRAPHRAG`` — explicit per-paradigm key
         (qa-lab-graphrag project).
      2. ``GEMINI_API_KEY`` — LightRAG-native naming, in case the user
         set that one instead.
      3. ``GOOGLE_API_KEY`` — project-wide fallback.
    """
    return (
        os.getenv("GOOGLE_API_KEY_GRAPHRAG")
        or os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
    )


async def _gemini_llm(
    prompt: str,
    system_prompt: str | None = None,
    history_messages: list | None = None,
    **kwargs,
) -> str:
    """LightRAG-compatible wrapper around gemini_complete_if_cache."""
    # Drop any api_key in kwargs so we don't double-pass it.
    kwargs.pop("api_key", None)
    return await gemini_complete_if_cache(
        model=LLM_MODEL,
        prompt=prompt,
        system_prompt=system_prompt,
        history_messages=history_messages,
        api_key=_resolve_gemini_key(),
        **kwargs,
    )


def make_rag(working_dir: Path | str | None = None) -> LightRAG:
    """Build a configured LightRAG instance.

    The caller is responsible for `await rag.initialize_storages()`
    before any insert / query, and `await rag.finalize_storages()` on
    shutdown. The function is sync because LightRAG's constructor is.
    """
    return LightRAG(
        working_dir=str(working_dir or LIGHTRAG_DIR),
        llm_model_func=_gemini_llm,
        llm_model_name=LLM_MODEL,
        embedding_func=openai_embed,
    )


# Default QueryParam shared by all read paths. `mode="hybrid"` combines
# entity-graph traversal and vector retrieval — the option that maps
# closest to the GraphRAG paradigm we are evaluating.
DEFAULT_QUERY_PARAM = QueryParam(
    mode="hybrid",
    top_k=5,
)
