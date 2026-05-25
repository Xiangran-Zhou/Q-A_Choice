# Q&A Paradigm Lab

A side-by-side comparison of three AI document-Q&A paradigms — **traditional RAG**, **Agentic Search**, and **GraphRAG** — answering the same questions against the same corpus, so the trade-offs are visible instead of hand-waved.

> **Status:** 🚧 Early scaffolding. See the milestone checklist below.

## Why

"Should we use RAG, Agentic search, or GraphRAG?" is one of the most common selection questions enterprise AI teams face in 2026 — and most public answers boil down to *"it depends."* This project replaces that hand-wave with a small, reproducible experiment: 20 evaluation questions, three paradigms, one shared corpus (the public LangChain documentation), and a side-by-side UI that surfaces real differences in latency, cost, and answer quality.

## The three paradigms

| Paradigm | What it does | Where it shines |
|---|---|---|
| **Traditional RAG** | Vector retrieval (Chroma) + BM25 hybrid + single-shot generation | Single-hop factual questions, high QPS, cost-sensitive workloads |
| **Agentic Search** | LangGraph agent with document-search tools and multi-turn tool use | Cross-document synthesis, unpredictable query patterns |
| **GraphRAG** | Knowledge-graph extraction (LightRAG) + graph traversal + generation | Multi-hop reasoning, relationship questions, high-explainability domains |

All three share the same generator model (Gemini Flash Lite) and the same source documents, so observed differences reflect the **paradigm**, not the model or the data.

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

## Milestone progress

- [ ] **M1** — Infrastructure + RAG baseline (project skeleton, `rag_graph`, 5 single-hop questions passing)
- [ ] **M2** — Agentic search adaptation (port from `chat-langchain`'s `docs_graph`, multi-hop / cross-doc questions passing)
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
