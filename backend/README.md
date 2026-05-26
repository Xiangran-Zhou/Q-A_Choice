# Backend — `qa_lab`

LangGraph implementations for the three Q&A paradigms. Each paradigm
lives in its own module under [`qa_lab/graphs/`](./qa_lab/graphs) and
exposes a compiled `graph` object plus a `build_graph()` factory.

## Layout

```
backend/
├── pyproject.toml          uv-managed project + dependencies
├── .python-version         Python 3.11
├── scripts/
│   ├── fetch_docs.py       Clones langchain-ai/docs into raw_docs/
│   ├── ingest.py           Loads → chunks → embeds → writes Chroma
│   ├── build_graph.py      Builds the LightRAG knowledge graph
│   └── run_overnight_build.sh / auto_resume_when_ready.sh
├── raw_docs/               LangChain docs corpus (gitignored)
├── chroma_db/              Persistent vector store (gitignored)
├── lightrag_storage/       Knowledge graph + LightRAG state (gitignored)
└── qa_lab/
    ├── __init__.py
    ├── llm.py                  Shared Gemini chat-model factory
    ├── api/
    │   ├── __init__.py
    │   └── server.py           FastAPI HTTP surface (one /api/query endpoint)
    ├── data/
    │   ├── __init__.py
    │   ├── loader.py           Read .mdx files into LangChain Documents
    │   ├── ingest.py           Chunking + embedding configuration
    │   ├── retriever.py        Vector + BM25 + hybrid retrievers
    │   └── graph_builder.py    LightRAG config (shared by build + query)
    └── graphs/
        ├── __init__.py
        ├── rag_graph.py        Traditional RAG  (hybrid retrieval + Gemini)
        ├── agentic_graph.py    Agentic Search   (create_react_agent + 2 tools)
        ├── agentic_tools.py    Tools: search_docs_vector, read_doc_file
        └── graphrag_graph.py   GraphRAG         (LightRAG hybrid query)
```

All three graphs are currently **placeholders** — they accept a
`{"question": ...}` input and return a fixed `[paradigm stub]` answer.
Real retrieval, agent loop, and graph traversal land in later commits.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) installed (`brew install uv` or
  `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Python 3.11 (uv will install it automatically from `.python-version`
  if missing)

## Setup

From this directory:

```bash
uv sync
```

This creates a `.venv/`, installs all dependencies from
`pyproject.toml`, and pins versions in `uv.lock`.

## Fetching the documentation corpus

All three paradigms share the same source corpus: the `.mdx` files from
[`langchain-ai/docs`](https://github.com/langchain-ai/docs) — the
unified documentation repo that backs python.langchain.com. Pull a
local copy once per environment:

```bash
uv run python scripts/fetch_docs.py
```

This shallow-clones the repo into `backend/raw_docs/` (gitignored) and
strips the `.git` directory so the corpus sits as a plain file tree.
Re-run with `--force` to refresh.

## Building the vector index

Once the corpus is on disk and `OPENAI_API_KEY` is in `.env` at the
project root, build the shared Chroma index:

```bash
uv run python scripts/ingest.py            # ingest if Chroma is empty
uv run python scripts/ingest.py --reset    # wipe + re-ingest
```

Configuration (single source of truth in `qa_lab/data/ingest.py`):

| Setting        | Value                              |
|----------------|------------------------------------|
| Chunk size     | 1,000 characters                   |
| Chunk overlap  | 200 characters                     |
| Embedding      | OpenAI `text-embedding-3-small`    |
| Collection     | `langchain_docs`                   |
| Persist dir    | `backend/chroma_db/` (gitignored)  |

A full ingest produces ~28k chunks, takes ~10 minutes, and costs
approximately **$0.12** in OpenAI embedding calls.

After ingestion the script runs a smoke query so retrieval failures
surface immediately.

## Running the graphs

The RAG graph is wired end-to-end. The other two are still stubs.

```bash
uv run python -m qa_lab.graphs.rag_graph        # real: hybrid retrieval + Gemini
uv run python -m qa_lab.graphs.agentic_graph    # placeholder
uv run python -m qa_lab.graphs.graphrag_graph   # placeholder
```

The RAG smoke run prints the question, Gemini's answer with inline
source citations, and the 10 chunks the hybrid retriever surfaced (5
each from Chroma and BM25, fused via reciprocal rank fusion).

The shared generator is `gemini-2.5-flash` (see the top-level
[README](../README.md#notes-on-model-choice) for why this isn't Flash
Lite). Override with `GEMINI_MODEL=...` in `.env`.

## Using a graph from Python

```python
from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv(usecwd=True))   # picks up OPENAI_API_KEY + GOOGLE_API_KEY

from qa_lab.graphs.rag_graph import graph

result = graph.invoke({
    "question": "How does LangGraph's interrupt function work?",
    "retrieved_chunks": [],
    "answer": "",
})
print(result["answer"])
for chunk in result["retrieved_chunks"]:
    print(chunk.metadata["source"])
```

## Running the HTTP API

The FastAPI server exposes one POST endpoint that all three paradigms
share. Designed for the Next.js frontend at <http://localhost:3000>.

```bash
cd backend
uv run uvicorn qa_lab.api.server:app --reload --port 8000
```

Then call it:

```bash
curl -X POST http://localhost:8000/api/query \
  -H 'Content-Type: application/json' \
  -d '{"paradigm": "rag", "question": "What is LangSmith?"}'
```

Response shape:

```json
{
  "paradigm": "rag",
  "question": "...",
  "answer": "...",
  "retrieved_chunks": [{"source": "src/...mdx", "content_preview": "..."}],
  "tool_calls":       [{"name": "search_docs_vector", "args": {...}}],
  "latency_ms": 1234,
  "model": "gemini-2.5-flash"
}
```

Upstream errors are mapped to clean HTTP statuses:

- **429** — Gemini daily quota exhausted. `detail.kind ===
  "upstream_quota_exhausted"`. Frontend should show a friendly
  retry-later banner; the rolling 24-h window will slide eventually.
- **502** — Any other upstream LLM error.

CORS is open to `http://localhost:3000` only; tighten for any
production deploy.

## What's next

The next milestones, in order:

1. ✅ Fetch the LangChain documentation corpus (`scripts/fetch_docs.py`)
2. ✅ Chunk + embed the corpus into a local Chroma store (shared by all three paradigms)
3. ✅ Implement real `rag_graph` (Chroma + BM25 hybrid retrieval + Gemini Flash)
4. ✅ Implement `agentic_graph` (own tools querying Chroma + filesystem; ReAct loop)
5. 🚧 Build the knowledge graph and implement `graphrag_graph` with LightRAG (M3, in progress)
6. ✅ HTTP API surface for the frontend (`qa_lab/api/server.py`)

See the top-level [`README.md`](../README.md) for the project-wide
milestone checklist.
