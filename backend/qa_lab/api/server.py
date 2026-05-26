"""FastAPI server exposing the three paradigm graphs over HTTP.

One JSON endpoint, paradigm chosen by request body:

    POST /api/query
    {
        "paradigm": "rag" | "agentic" | "graphrag",
        "question": "..."
    }
    →
    {
        "paradigm": "...",
        "question": "...",
        "answer": "...",
        "retrieved_chunks": [{"source": "...", "content_preview": "..."}],
        "tool_calls":       [{"name": "...", "args": {...}}],
        "latency_ms": 1234,
        "model": "gemini-2.5-flash"
    }

Graphs are imported lazily on the first request so a missing
LightRAG store doesn't break server boot for the other two paradigms.

CORS is open to http://localhost:3000 so the Next.js dev server can
hit this from the browser without proxying.

Run locally (from `backend/`):

    uv run uvicorn qa_lab.api.server:app --reload --port 8000
"""

from __future__ import annotations

import importlib
import os
import time
from typing import Any, Literal

from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from qa_lab.llm import DEFAULT_GEMINI_MODEL

# Load .env from the project root so GOOGLE_API_KEY / OPENAI_API_KEY are
# in os.environ before any graph module is imported.
load_dotenv(find_dotenv(usecwd=True))

PARADIGM_MODULES: dict[str, str] = {
    "rag": "qa_lab.graphs.rag_graph",
    "agentic": "qa_lab.graphs.agentic_graph",
    "graphrag": "qa_lab.graphs.graphrag_graph",
}

# Module cache so we don't re-import for every request.
_graph_cache: dict[str, Any] = {}


def _get_graph(paradigm: str):
    if paradigm not in PARADIGM_MODULES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown paradigm {paradigm!r}; must be one of {list(PARADIGM_MODULES)}",
        )
    if paradigm not in _graph_cache:
        module = importlib.import_module(PARADIGM_MODULES[paradigm])
        if not hasattr(module, "graph"):
            raise HTTPException(
                status_code=500,
                detail=f"{PARADIGM_MODULES[paradigm]} does not expose a `graph` attribute",
            )
        _graph_cache[paradigm] = module.graph
    return _graph_cache[paradigm]


# ---------------------------------------------------------------- schema


class QueryRequest(BaseModel):
    paradigm: Literal["rag", "agentic", "graphrag"]
    question: str = Field(..., min_length=1, max_length=2_000)


class RetrievedChunk(BaseModel):
    source: str
    content_preview: str


class ToolCallRecord(BaseModel):
    name: str
    args: dict[str, Any]


class QueryResponse(BaseModel):
    paradigm: str
    question: str
    answer: str
    retrieved_chunks: list[RetrievedChunk]
    tool_calls: list[ToolCallRecord]
    latency_ms: int
    model: str


# ---------------------------------------------------------------- app


app = FastAPI(
    title="Q&A Paradigm Lab",
    description="HTTP surface for the three paradigm graphs.",
    version="0.1.0",
)

# Next.js dev server runs on :3000; tighten for production deploys.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/query", response_model=QueryResponse)
def query(req: QueryRequest) -> QueryResponse:
    """Invoke the chosen paradigm's graph and return its answer + evidence."""
    graph = _get_graph(req.paradigm)

    initial_state = {
        "question": req.question,
        "retrieved_chunks": [],
        "tool_calls": [],
        "answer": "",
    }

    t0 = time.time()
    try:
        final_state = graph.invoke(initial_state)
    except Exception as exc:  # noqa: BLE001 — translate upstream LLM errors into clean HTTP
        msg = str(exc)
        # Surface Gemini per-day-quota walls as 429 so the frontend can
        # show a friendly "try again later" instead of a generic 500.
        if "RESOURCE_EXHAUSTED" in msg or "generate_requests_per_model_per_day" in msg:
            raise HTTPException(
                status_code=429,
                detail={
                    "kind": "upstream_quota_exhausted",
                    "paradigm": req.paradigm,
                    "message": (
                        "Gemini daily quota exhausted. The rolling 24-hour window "
                        "needs to slide before queries can resume."
                    ),
                },
            ) from exc
        raise HTTPException(
            status_code=502,
            detail={
                "kind": "upstream_error",
                "paradigm": req.paradigm,
                "message": msg[:400],
            },
        ) from exc

    latency_ms = int((time.time() - t0) * 1000)

    chunks = [
        RetrievedChunk(
            source=c.metadata.get("source", "(unknown)") if hasattr(c, "metadata") else "(unknown)",
            content_preview=(
                (c.page_content if hasattr(c, "page_content") else str(c))[:500]
            ),
        )
        for c in (final_state.get("retrieved_chunks") or [])
    ]

    tool_calls = [
        ToolCallRecord(
            name=tc.get("name", "?"),
            args=tc.get("args") if isinstance(tc.get("args"), dict) else {"raw": tc.get("args")},
        )
        for tc in (final_state.get("tool_calls") or [])
    ]

    return QueryResponse(
        paradigm=req.paradigm,
        question=req.question,
        answer=final_state.get("answer", ""),
        retrieved_chunks=chunks,
        tool_calls=tool_calls,
        latency_ms=latency_ms,
        model=os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL),
    )
