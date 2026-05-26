"""Traditional RAG paradigm graph.

Pipeline:

    question
       │
       ▼
    [retrieve]    hybrid retrieval (Chroma vector + BM25), top-k chunks
       │
       ▼
    [generate]    Gemini Flash Lite, prompted with the chunks as context
       │
       ▼
    {answer, retrieved_chunks}

The retrieved chunks stay in the output state so the frontend can show
the evidence trail beneath each answer.

Prerequisites:

- `OPENAI_API_KEY` and `GOOGLE_API_KEY` set (loaded from `.env` at the
  project root by callers, e.g. `scripts/ingest.py` or the API layer).
- `scripts/ingest.py` has been run so Chroma + BM25 caches exist.

Run as a script to see a real answer plus its source chunks:

    uv run python -m qa_lab.graphs.rag_graph
"""

from __future__ import annotations

from typing import TypedDict

from dotenv import find_dotenv, load_dotenv
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from qa_lab.data.retriever import get_hybrid_retriever
from qa_lab.llm import get_chat_model

RETRIEVAL_K = 5

SYSTEM_PROMPT = (
    "You are a precise documentation assistant for the LangChain ecosystem.\n"
    "Answer the user's question using ONLY the provided context.\n"
    "If the context does not contain enough information, say so honestly "
    "rather than guessing.\n"
    "Cite the sources you used by their file path."
)


class State(TypedDict):
    question: str
    retrieved_chunks: list[Document]
    answer: str


def _format_chunks(chunks: list[Document]) -> str:
    """Render retrieved chunks as a labelled context block for the LLM."""
    blocks: list[str] = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.metadata.get("source", "(unknown)")
        blocks.append(f"[{i}] Source: {source}\n{chunk.page_content}")
    return "\n\n---\n\n".join(blocks)


def _retrieve_node(state: State) -> dict:
    """Run hybrid retrieval and stash the chunks on the state."""
    retriever = get_hybrid_retriever(k=RETRIEVAL_K)
    chunks = retriever.invoke(state["question"])
    return {"retrieved_chunks": chunks}


def _generate_node(state: State) -> dict:
    """Feed the question + chunks to Gemini and return its answer."""
    context = _format_chunks(state["retrieved_chunks"])
    user_message = (
        f"Context:\n\n{context}\n\n---\n\nQuestion: {state['question']}"
    )
    response = get_chat_model(paradigm="rag").invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_message),
        ]
    )
    return {"answer": response.content}


def build_graph():
    builder = StateGraph(State)
    builder.add_node("retrieve", _retrieve_node)
    builder.add_node("generate", _generate_node)
    builder.add_edge(START, "retrieve")
    builder.add_edge("retrieve", "generate")
    builder.add_edge("generate", END)
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
    print(f"Retrieved {len(result['retrieved_chunks'])} chunks:")
    for i, chunk in enumerate(result["retrieved_chunks"], 1):
        source = chunk.metadata.get("source", "(unknown)")
        preview = chunk.page_content[:100].replace("\n", " ").strip()
        print(f"  [{i}] {source}")
        print(f"      {preview}...")
