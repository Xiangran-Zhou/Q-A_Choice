"""Agentic Search paradigm graph.

A ReAct-style agent built on `langgraph.prebuilt.create_react_agent`
with two retrieval tools (see `agentic_tools.py`). The agent decides
when to search, when to drill into a specific file, and when to stop
and answer — in contrast to the RAG graph, which always runs exactly
one retrieval pass.

This is the **first pass** of M2 — deliberately simple. A later commit
will reimplement it in the style of `chat-langchain`'s production
agent (Summarization + Retry middlewares, explicit state machine).

Output state preserves both the final answer and the sequence of tool
calls the agent made, so the frontend can render the "where it looked"
timeline beneath each answer.

Run as a script to see a real multi-step answer:

    uv run python -m qa_lab.graphs.agentic_graph
"""

from __future__ import annotations

from typing import Any, TypedDict

from dotenv import find_dotenv, load_dotenv
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import create_react_agent

from qa_lab.graphs.agentic_tools import AGENTIC_TOOLS
from qa_lab.llm import get_chat_model

SYSTEM_PROMPT = (
    "You are a precise documentation assistant for the LangChain ecosystem.\n"
    "\n"
    "You have two tools:\n"
    "- search_docs_vector(query): semantic + keyword search over the docs.\n"
    "- read_doc_file(source_path): fetch the full content of one .mdx file.\n"
    "\n"
    "Workflow:\n"
    "1. Call search_docs_vector with specific keywords from the question.\n"
    "2. If the chunks are partial or relevant pages were truncated, call\n"
    "   read_doc_file on a promising source path for full context.\n"
    "3. For multi-hop or comparison questions, run 2-3 searches with\n"
    "   different query angles before concluding. One search is rarely\n"
    "   enough.\n"
    "4. After gathering evidence, write a synthesized FINAL ANSWER.\n"
    "\n"
    "Rules for the final answer (READ CAREFULLY):\n"
    "- Write the answer in your own words as flowing prose. DO NOT copy\n"
    "  the bracketed [1] Source: ... blocks from tool output — those are\n"
    "  raw data for you, not the user's answer.\n"
    "- Always end with a non-empty natural-language message. An empty\n"
    "  reply is never acceptable.\n"
    "- Cite the source paths inline like `(src/oss/langgraph/interrupts.mdx)`\n"
    "  so the user can verify.\n"
    "- If after all searches you still cannot answer, say so explicitly\n"
    "  rather than returning nothing."
)


class State(TypedDict):
    """Public state shape consumed by the evaluation runner and the API layer."""

    question: str
    retrieved_chunks: list[Document]  # kept for runner compat; not populated here
    tool_calls: list[dict]
    answer: str


# The underlying ReAct agent is constructed lazily on first call: it
# needs GOOGLE_API_KEY at construction time, which the caller is
# expected to load from .env *before* invoking the graph. Building it
# at import time would fail in test environments where the key isn't
# set yet.
_react_agent_cache: Any | None = None


def _get_react_agent():
    global _react_agent_cache
    if _react_agent_cache is None:
        _react_agent_cache = create_react_agent(
            model=get_chat_model(paradigm="agentic"),
            tools=AGENTIC_TOOLS,
            prompt=SYSTEM_PROMPT,
        )
    return _react_agent_cache


def _extract_tool_calls(messages: list[Any]) -> list[dict]:
    """Pull tool invocations off the message stream in the order they happened."""
    calls: list[dict] = []
    for msg in messages:
        raw_calls = getattr(msg, "tool_calls", None) or []
        for tc in raw_calls:
            # ToolCall objects are typed dicts: {"name", "args", "id"}.
            calls.append(
                {
                    "name": tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", "?"),
                    "args": tc.get("args") if isinstance(tc, dict) else getattr(tc, "args", {}),
                }
            )
    return calls


def _flatten_content(content: Any) -> str:
    """Render an AIMessage's content as a plain string.

    Gemini 2.5 returns content as a list of typed blocks
    (`[{"type": "text", "text": "...", "extras": {...}}, "...", ...]`).
    Older Gemini versions and most other models return a plain string.
    Handle both so the report stays readable.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                # Gemini structured block: prefer the human-readable "text" field.
                if "text" in block:
                    parts.append(str(block["text"]))
                else:
                    parts.append(str(block))
            else:
                parts.append(str(block))
        return "".join(parts)
    return str(content)


def _final_answer(messages: list[Any]) -> str:
    """Pull the last AI-authored message content as the agent's answer.

    Only `AIMessage` instances count — `ToolMessage` content is raw tool
    output, not an answer. If the agent ended without synthesizing a
    real reply (empty final AIMessage), return a clear placeholder so
    the failure is visible in the report instead of silently surfacing
    the previous tool result.
    """
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            text = _flatten_content(msg.content)
            if text.strip():
                return text
    return "[agent ended without producing a final answer]"


def _agent_node(state: State) -> dict:
    agent = _get_react_agent()
    result = agent.invoke({"messages": [HumanMessage(content=state["question"])]})
    messages = result.get("messages", [])
    return {
        "answer": _final_answer(messages),
        "tool_calls": _extract_tool_calls(messages),
    }


def build_graph():
    builder = StateGraph(State)
    builder.add_node("agent", _agent_node)
    builder.add_edge(START, "agent")
    builder.add_edge("agent", END)
    return builder.compile()


graph = build_graph()


if __name__ == "__main__":
    load_dotenv(find_dotenv(usecwd=True))

    # Star question from PRODUCT.md section 6 (#2.2): multi-hop reasoning
    # that should expose what the agent loop buys you over single-shot RAG.
    question = (
        "If I want to implement automatic retry up to 3 times in LangGraph, "
        "which components do I need to wire together?"
    )
    print(f"Q: {question}\n")
    result = graph.invoke(
        {
            "question": question,
            "retrieved_chunks": [],
            "tool_calls": [],
            "answer": "",
        }
    )
    print(f"A: {result['answer']}\n")
    print(f"Tool calls ({len(result['tool_calls'])}):")
    for i, call in enumerate(result["tool_calls"], 1):
        args = call.get("args", {})
        # Truncate long query/path args for readability.
        rendered_args = {k: (v[:80] + "..." if isinstance(v, str) and len(v) > 80 else v) for k, v in args.items()}
        print(f"  [{i}] {call['name']}({rendered_args})")
