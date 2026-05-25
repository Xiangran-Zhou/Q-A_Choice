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
│   └── fetch_docs.py       Clones langchain-ai/docs into raw_docs/
├── raw_docs/               LangChain docs corpus (gitignored, populated
│                           by fetch_docs.py)
└── qa_lab/
    ├── __init__.py
    └── graphs/
        ├── __init__.py
        ├── rag_graph.py        Traditional RAG (stub)
        ├── agentic_graph.py    Agentic Search   (stub)
        └── graphrag_graph.py   GraphRAG         (stub)
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

## Running the stubs

Each graph module is runnable as a script and prints its placeholder
response:

```bash
uv run python -m qa_lab.graphs.rag_graph
uv run python -m qa_lab.graphs.agentic_graph
uv run python -m qa_lab.graphs.graphrag_graph
```

Expected output (one line per command), for example:

```
[rag_graph stub] Real retrieval not implemented yet. You asked: 'What is LangChain?'
```

## Using a graph from Python

```python
from qa_lab.graphs.rag_graph import graph

result = graph.invoke({"question": "What is LangChain?", "answer": ""})
print(result["answer"])
```

## What's next

The next milestones, in order:

1. ✅ Fetch the LangChain documentation corpus (`scripts/fetch_docs.py`)
2. Chunk + embed the corpus into a local Chroma store (shared by all three paradigms)
3. Implement real `rag_graph` (Chroma + BM25 hybrid retrieval + Gemini Flash Lite)
4. Implement `agentic_graph` (own tools querying Chroma + filesystem; agent pattern inspired by `chat-langchain`)
5. Build the knowledge graph and implement `graphrag_graph` with LightRAG

See the top-level [`README.md`](../README.md) for the project-wide
milestone checklist.
