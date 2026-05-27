"""GraphRAG paradigm graph (LightRAG-backed).

Pipeline:

    question
       │
       ▼
    [query_lightrag]    LightRAG hybrid mode: entity graph + vector
                        retrieval, then LightRAG's own LLM generation.
       │
       ▼
    {answer, retrieved_chunks}

LightRAG does retrieval AND generation internally — the entity/edge
context, vector chunks, and the generator LLM are all wired together
behind the `aquery` call. So unlike the RAG graph, we don't do a
separate generate step; we surface the answer LightRAG returns.

`retrieved_chunks` is populated with a single synthesized Document
holding the context block (mode="hybrid", `only_need_context=True`),
so the evaluation runner and the eventual UI have something concrete
to display as "what the graph saw".

Prerequisites:

- `GOOGLE_API_KEY` and `OPENAI_API_KEY` set (loaded from `.env` by the
  caller).
- `scripts/build_graph.py` has been run so `backend/lightrag_storage/`
  exists with extracted entities + edges.

Run as a script to see a real GraphRAG answer:

    uv run python -m qa_lab.graphs.graphrag_graph
"""

from __future__ import annotations

import asyncio
from typing import TypedDict

from dotenv import find_dotenv, load_dotenv
from langchain_core.documents import Document
from langgraph.graph import END, START, StateGraph
from lightrag import QueryParam

from qa_lab.data.graph_builder import LIGHTRAG_DIR, make_rag


class State(TypedDict):
    question: str
    retrieved_chunks: list[Document]
    answer: str


# Module-level singleton: one LightRAG instance + one event loop, reused
# across every query in this process. Calling `initialize_storages()` and
# `finalize_storages()` per query (the old pattern) left LightRAG's
# internal state stuck after the first call — every subsequent query
# returned None for `only_need_context=True` and an empty answer for the
# real query. One-time init avoids that lifecycle entirely.
#
# The loop is pinned because LightRAG's async tasks bind to the event
# loop that created them; running queries via `asyncio.run()` would spin
# up a fresh loop each time and detach them.
_rag_instance: object | None = None
_rag_loop: asyncio.AbstractEventLoop | None = None


def _get_rag_and_loop():
    """Lazy-init the singleton LightRAG instance + its event loop."""
    global _rag_instance, _rag_loop
    if _rag_instance is None or _rag_loop is None:
        _rag_loop = asyncio.new_event_loop()
        _rag_instance = make_rag()
        _rag_loop.run_until_complete(_rag_instance.initialize_storages())
    return _rag_instance, _rag_loop


async def _aquery_lightrag(rag, question: str) -> tuple[str, str]:
    """Run a hybrid LightRAG query using the shared singleton rag.

    Returns `(answer, context)` — the generated answer and the raw
    context block (entities + relations + chunks) LightRAG retrieved.

    Wraps each `aquery` call defensively so a single edge-case failure
    on one question doesn't crash the whole eval batch; the runner
    will record an empty answer / context, which is honest data.
    """
    try:
        context = await rag.aquery(
            question,
            param=QueryParam(mode="hybrid", top_k=5, only_need_context=True),
        )
    except Exception:
        context = ""
    try:
        answer = await rag.aquery(
            question,
            param=QueryParam(mode="hybrid", top_k=5),
        )
    except Exception as exc:
        answer = f"[graphrag_graph error: {exc}]"
    return (answer or ""), (context or "")


def _graphrag_node(state: State) -> dict:
    """Run LightRAG and pack its output into our State shape."""
    if not LIGHTRAG_DIR.exists() or not any(LIGHTRAG_DIR.iterdir()):
        return {
            "answer": (
                "[graphrag_graph] LightRAG store missing or empty. "
                "Run `uv run python scripts/build_graph.py` first."
            ),
            "retrieved_chunks": [],
        }

    rag, loop = _get_rag_and_loop()
    answer, context = loop.run_until_complete(
        _aquery_lightrag(rag, state["question"])
    )

    chunks: list[Document] = []
    if context:  # only build a chunk Document if we got real context text
        chunks.append(
            Document(
                page_content=context,
                metadata={"source": "lightrag://hybrid-context"},
            )
        )
    return {"answer": answer, "retrieved_chunks": chunks}


def build_graph():
    builder = StateGraph(State)
    builder.add_node("query_lightrag", _graphrag_node)
    builder.add_edge(START, "query_lightrag")
    builder.add_edge("query_lightrag", END)
    return builder.compile()


graph = build_graph()


if __name__ == "__main__":
    load_dotenv(find_dotenv(usecwd=True))

    question = "How does LangGraph's interrupt function work?"
    print(f"Q: {question}\n")
    result = graph.invoke(
        {"question": question, "retrieved_chunks": [], "answer": ""}
    )
    print(f"A: {result['answer']}\n")
    if result["retrieved_chunks"]:
        ctx = result["retrieved_chunks"][0].page_content
        print(f"Context (first 500 chars):\n{ctx[:500]}...")
