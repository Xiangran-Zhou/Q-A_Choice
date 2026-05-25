# Q&A Paradigm Lab

A side-by-side comparison of three AI document-Q&A paradigms — **traditional RAG**, **Agentic Search**, and **GraphRAG** — answering the same questions against the same corpus, so the trade-offs are visible instead of hand-waved.

> **Status:** 🚧 M1 complete — RAG baseline runs end-to-end. M2 (Agentic) in progress. See milestone checklist below.

## Why

"Should we use RAG, Agentic search, or GraphRAG?" is one of the most common selection questions enterprise AI teams face in 2026 — and most public answers boil down to *"it depends."* This project replaces that hand-wave with a small, reproducible experiment: 20 evaluation questions, three paradigms, one shared corpus (the public LangChain documentation), and a side-by-side UI that surfaces real differences in latency, cost, and answer quality.

## The three paradigms

| Paradigm | What it does | Where it shines |
|---|---|---|
| **Traditional RAG** | Vector retrieval (Chroma) + BM25 hybrid + single-shot generation | Single-hop factual questions, high QPS, cost-sensitive workloads |
| **Agentic Search** | LangGraph agent with document-search tools and multi-turn tool use | Cross-document synthesis, unpredictable query patterns |
| **GraphRAG** | Knowledge-graph extraction (LightRAG) + graph traversal + generation | Multi-hop reasoning, relationship questions, high-explainability domains |

All three share the same generator model (Gemini 2.5 Flash) and the same source documents, so observed differences reflect the **paradigm**, not the model or the data. See [Notes on model choice](#notes-on-model-choice) for why this isn't Flash Lite.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (Next.js)                                      │
│  ┌──────┬──────┬──────────┬──────────────┬────────────┐ │
│  │ RAG  │Agent │GraphRAG  │Side-by-side  │Decision    │ │
│  │ tab  │ tab  │ tab      │ tab          │matrix tab  │ │
│  └──────┴──────┴──────────┴──────────────┴────────────┘ │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  Backend (LangGraph)                                     │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ rag_graph│  │ agentic_graph│  │ graphrag_graph   │   │
│  └──────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  Shared data layer                                       │
│  Chroma vector store · Mintlify API · Knowledge graph    │
│  LangChain official documentation (.mdx)                 │
└─────────────────────────────────────────────────────────┘
```

## Repository layout

```
.
├── backend/          LangGraph implementations for the three paradigms
├── frontend/         Next.js UI (5 tabs)
├── evaluation/       Question set, results, scoring
│   └── questions.json    20 questions across single-hop / multi-hop / cross-doc
├── .env.example      Required API keys
└── .gitignore
```

## Notes on model choice

The shared generator is **Gemini 2.5 Flash**, not Flash Lite as the
original engineering plan called for.

The plan picked Flash Lite for cost reasons, but an early M2 run found
that Flash Lite produced an **empty final answer in 4 out of 5
multi-hop questions** when driving the ReAct-style Agentic loop. The
agent would call `search_docs_vector`, receive the chunks, and then
emit an empty `AIMessage` with no synthesis — a known failure mode of
smaller models with tool-calling loops. The same question on the same
prompt with `gemini-2.5-flash` produced a correct, fully synthesized
answer identifying `ToolRetryMiddleware` as the canonical solution.

The fix was to upgrade the shared default for all three paradigms so
the comparison stays fair (the alternative — letting Agentic use Flash
while RAG and GraphRAG stay on Flash Lite — would let model capability
masquerade as paradigm capability, defeating the point of the
experiment).

Cost impact is small: at $0.30 / $2.50 per million input/output tokens
for Flash, each evaluation question is roughly **$0.005**, and a full
15-question run across all three paradigms stays under **$0.25**.

Override the model with `GEMINI_MODEL=…` in `.env` if you want to
re-confirm the Flash Lite finding or experiment with a different
generator.

## Milestone progress

- [x] **M1** — Infrastructure + RAG baseline (project skeleton, `rag_graph` runs end-to-end against all 5 single-hop questions; full per-question report in `evaluation/results/rag_single_hop.json` locally)
- [ ] **M2** — Agentic search (`agentic_graph` with two retrieval tools, multi-hop / cross-doc questions passing)
- [ ] **M3** — GraphRAG (knowledge-graph build, `graphrag_graph`, full 20-question coverage)
- [ ] **M4** — Evaluation + demo (run all questions, score, generate decision matrix, demo rehearsal)

## Getting started

> Coming soon — the scaffolding is still being filled in. Once the backend skeleton lands, this section will document how to run each paradigm locally.

For now:

```bash
cp .env.example .env   # then fill in your API keys
```

## Acknowledgements

The Agentic Search implementation is adapted from [`langchain-ai/chat-langchain`](https://github.com/langchain-ai/chat-langchain). The evaluation corpus uses the public [LangChain documentation](https://python.langchain.com/).
