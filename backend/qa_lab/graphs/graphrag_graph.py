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


async def _aquery_lightrag(question: str) -> tuple[str, str]:
    """Run a hybrid LightRAG query.

    Returns `(answer, context)` — the generated answer and the raw
    context block (entities + relations + chunks) LightRAG retrieved.
    Two API calls so we can surface both to the caller.
    """
    rag = make_rag()
    await rag.initialize_storages()
    try:
        context = await rag.aquery(
            question,
            param=QueryParam(mode="hybrid", top_k=5, only_need_context=True),
        )
        answer = await rag.aquery(
            question,
            param=QueryParam(mode="hybrid", top_k=5),
        )
    finally:
        await rag.finalize_storages()
    return answer, context


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

    answer, context = asyncio.run(_aquery_lightrag(state["question"]))
    # Wrap the retrieved context as a single Document so the evaluation
    # runner can dedup "sources" like it does for RAG; the metadata
    # source tag distinguishes graph-derived context from doc chunks.
    chunks = [
        Document(
            page_content=context,
            metadata={"source": "lightrag://hybrid-context"},
        )
    ]
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
