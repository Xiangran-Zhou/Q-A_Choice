# Q&A Paradigm Lab

**English** · [中文报告](./README.zh-CN.md)

A side-by-side comparison of three AI document-Q&A paradigms — **traditional RAG**, **Agentic Search**, and **GraphRAG** — answering the same questions against the same corpus, so the trade-offs are visible instead of hand-waved.

| Paradigm | Single-hop | Multi-hop | Cross-doc | Overall |
|---|:---:|:---:|:---:|:---:|
| **RAG** | 8/15 | 5/15 | 5/15 | **18/45 (40%)** |
| **Agentic** | 7/15 | 9/15 | 15/15 | **31/45 (69%)** |
| **GraphRAG** | 6/15 | **10/15** ★ | 12/15 | **28/45 (62%)** |

★ GraphRAG narrowly beats Agentic on multi-hop reasoning — exactly the pre-experiment prediction. Full breakdown in the [decision matrix](./evaluation/decision_matrix.md).

## Why

"Should we use RAG, Agentic search, or GraphRAG?" is one of the most common selection questions enterprise AI teams face in 2026 — and most public answers boil down to *"it depends."* This project replaces that hand-wave with a small, reproducible experiment: 15 evaluation questions, three paradigms, one shared corpus (the public LangChain documentation), one LLM-as-judge for blind scoring, and a side-by-side UI that surfaces real differences in latency and answer quality.

## The three paradigms

| Paradigm | What it does | Where it shines |
|---|---|---|
| **Traditional RAG** | Vector retrieval (Chroma) + BM25 hybrid + single-shot generation | Single-hop factual questions, high QPS, cost-sensitive workloads |
| **Agentic Search** | LangGraph agent with document-search tools and multi-turn tool use | Cross-document synthesis, unpredictable query patterns |
| **GraphRAG** | Knowledge-graph extraction (LightRAG, ~66k entities / ~125k relations) + multi-hop traversal + generation | Multi-hop reasoning, relationship questions, high-explainability domains |

All three share the same generator model (Gemini 2.5 Flash) and the same source documents, so observed differences reflect the **paradigm**, not the model or the data. See [Notes on model choice](#notes-on-model-choice) for why this isn't Flash Lite.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (Next.js 16 + App Router + Tailwind 4)         │
│  ┌──────┬──────┬──────────┬──────────────┬────────────┐ │
│  │ RAG  │Agent │GraphRAG  │Side-by-side  │Decision    │ │
│  │ tab  │ tab  │ tab      │ tab          │matrix tab  │ │
│  └──────┴──────┴──────────┴──────────────┴────────────┘ │
└─────────────────────────────────────────────────────────┘
                          │ HTTP POST /api/query
                          ▼
┌─────────────────────────────────────────────────────────┐
│  Backend (FastAPI + LangGraph)                           │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ rag_graph│  │ agentic_graph│  │ graphrag_graph   │   │
│  └──────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  Shared data layer                                       │
│  Chroma vector store · BM25 chunks · LightRAG graph      │
│  langchain-ai/docs (1,471 .mdx files)                    │
└─────────────────────────────────────────────────────────┘
```

## Repository layout

```
.
├── backend/           FastAPI server + 3 LangGraph paradigm implementations
│   ├── qa_lab/        Python package
│   │   ├── api/       /api/query HTTP endpoint
│   │   ├── data/      loader / ingest / retriever / graph_builder
│   │   └── graphs/    rag_graph, agentic_graph, graphrag_graph
│   └── scripts/       fetch_docs, ingest (Chroma), build_graph (LightRAG)
├── frontend/          Next.js UI (5 tabs)
│   └── app/
│       ├── rag/ agentic/ graphrag/ compare/ matrix/
│       └── _components/  QueryPanel, CompareGrid, NavBar
├── evaluation/
│   ├── questions.json           15 questions × 3 dimensions
│   ├── run_one_paradigm.py      Runner harness
│   ├── judge.py                 Gemini 2.5 Pro as judge
│   ├── compute_metrics.py       Aggregation
│   ├── decision_matrix.md       Living scoring document
│   └── results/                 scored_*.json (audit trail, committed)
├── .env.example       Required API keys
└── .gitignore
```

## Notes on model choice

The shared generator is **Gemini 2.5 Flash**, not Flash Lite as the original engineering plan called for.

The plan picked Flash Lite for cost reasons, but an early M2 run found that Flash Lite produced an **empty final answer in 4 out of 5 multi-hop questions** when driving the ReAct-style Agentic loop. The agent would call `search_docs_vector`, receive the chunks, and then emit an empty `AIMessage` with no synthesis — a known failure mode of smaller models with tool-calling loops. The same question on the same prompt with `gemini-2.5-flash` produced a correct, fully synthesized answer identifying `ToolRetryMiddleware` as the canonical solution.

The fix was to upgrade the shared default for all three paradigms so the comparison stays fair (the alternative — letting Agentic use Flash while RAG and GraphRAG stay on Flash Lite — would let model capability masquerade as paradigm capability, defeating the point of the experiment).

Cost impact is small: at $0.30 / $2.50 per million input/output tokens for Flash, each evaluation question is roughly **$0.005**, and a full 15-question run across all three paradigms stays under **$0.25**.

Override the model with `GEMINI_MODEL=…` in `.env` if you want to re-confirm the Flash Lite finding or experiment with a different generator.

## Methodology

- **LLM-as-judge over human scoring.** Gemini 2.5 Pro (one notch above the Flash generator, the standard guardrail against self-preference) scores each answer 0–3 with a `read_doc_file` tool to verify claims against the actual `.mdx` files. Per-question judge reasoning lives in `evaluation/results/scored_*.json` — the public audit trail.
- **Blind judging.** The judge prompt never reveals which paradigm produced an answer.
- **Per-paradigm GCP projects.** Each paradigm is bound to its own Google Cloud project + API key, so the three daily quotas (10k req/day each on Tier 1) don't contend. See `qa_lab/llm.py` for the `paradigm`-scoped key resolver.

## Getting started

### Prerequisites

- **Python 3.11**, [uv](https://docs.astral.sh/uv/) (`brew install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **Node.js 20+**, npm 10+
- **Git**
- **API keys**:
  - OpenAI (for `text-embedding-3-small`)
  - Gemini (1 key min; 3 keys recommended — see below)

### 1. Clone + install dependencies

```bash
git clone https://github.com/Xiangran-Zhou/Q-A_Choice.git
cd Q-A_Choice

# Backend
cd backend
uv sync          # installs Python deps, creates .venv
cd ..

# Frontend
cd frontend
npm install
cd ..
```

### 2. Configure API keys

Copy `.env.example` to `.env` and fill in:

```bash
cp .env.example .env
```

```env
# Minimum: a single Gemini key + an OpenAI key
GOOGLE_API_KEY=<your-gemini-key>
OPENAI_API_KEY=<your-openai-key>

# Optional but recommended: paradigm-scoped keys from *separate* GCP
# projects, so the three daily 10k/day Tier 1 quotas don't contend.
GOOGLE_API_KEY_RAG=<key-from-qa-lab-rag-project>
GOOGLE_API_KEY_AGENTIC=<key-from-qa-lab-agentic-project>
GOOGLE_API_KEY_GRAPHRAG=<key-from-qa-lab-graphrag-project>
```

> **Why per-paradigm keys?** Gemini quotas are per-GCP-project, not per-key. Multiple keys inside one project share the same 10k/day cap on Tier 1. Binding each paradigm to a separate project decouples their quotas — see `qa_lab/llm.py` for the resolver.

### 3. Fetch the corpus

```bash
cd backend
uv run python scripts/fetch_docs.py
```

Shallow-clones [`langchain-ai/docs`](https://github.com/langchain-ai/docs) into `backend/raw_docs/` (1,471 `.mdx` files, ~544 MB on disk).

### 4. Build the Chroma vector index (RAG + Agentic + GraphRAG share this)

```bash
uv run python scripts/ingest.py
```

Chunks the corpus into ~28k chunks (1k chars, 200 overlap), embeds via `text-embedding-3-small`, writes to `backend/chroma_db/`. Takes ~10 minutes; costs ~$0.12 in OpenAI embedding calls.

### 5. Build the LightRAG knowledge graph (GraphRAG)

```bash
# Note: this is a long-running build (Tier 1 quota may cause it to
# span multiple days). The wrapper handles auto-restart + idempotent
# resume. See backend/scripts/run_overnight_build.sh.
nohup bash scripts/run_overnight_build.sh > /dev/null 2>&1 & disown
tail -f /tmp/lightrag_build.log
```

When the log says `Build completed successfully on attempt N` (typically after 1–2 days due to Tier 1 daily-quota cycling), the graph is ready. End state: ~66k entities + ~125k relations from 1,471 docs.

### 6. Run the backend API

```bash
cd backend
uv run uvicorn qa_lab.api.server:app --port 8000 --reload
```

Smoke test:

```bash
curl -X POST http://localhost:8000/api/query \
  -H 'Content-Type: application/json' \
  -d '{"paradigm": "rag", "question": "What is LangSmith?"}'
```

### 7. Run the frontend

```bash
cd frontend
npm run dev
```

Open <http://localhost:3000>. Five tabs:

- `/rag`, `/agentic`, `/graphrag` — single-paradigm chat panels
- `/compare` — three columns running in parallel (the demo centrepiece)
- `/matrix` — the full decision matrix with per-question scores

### 8. (Optional) Re-run the evaluation

```bash
cd backend

# Run a paradigm against one dimension (5 questions)
uv run python ../evaluation/run_one_paradigm.py --paradigm rag --dimension single_hop

# Or run everything
for p in rag agentic graphrag; do
  for d in single_hop multi_hop cross_doc; do
    uv run python ../evaluation/run_one_paradigm.py --paradigm $p --dimension $d
  done
done

# Score with the LLM judge
uv run python ../evaluation/judge.py --all

# Aggregate
uv run python ../evaluation/compute_metrics.py
```

Scored audit trails write to `evaluation/results/scored_*.json` (committed to the repo so judge reasoning is publicly verifiable).

## Acknowledgements

- Agentic Search architecture inspired by [`langchain-ai/chat-langchain`](https://github.com/langchain-ai/chat-langchain). The agent loop is reimplemented locally: chat-langchain's current `master` queries Mintlify's documentation search API via `MINTLIFY_API_URL` + `MINTLIFY_API_KEY` env vars — a private contract between langchain-ai and Mintlify that isn't publicly available. This project rebuilds the equivalent functionality with two locally-implemented tools (`search_docs_vector` against our own Chroma + BM25 hybrid index, and `read_doc_file` against the `.mdx` corpus), so anyone can clone and run it without obtaining private credentials.
- GraphRAG implementation: [`HKUDS/LightRAG`](https://github.com/HKUDS/LightRAG).
- Evaluation corpus: the public [LangChain documentation](https://python.langchain.com/) via the [`langchain-ai/docs`](https://github.com/langchain-ai/docs) repository.

---

📄 **中文版本与项目报告：** [README.zh-CN.md](./README.zh-CN.md)
