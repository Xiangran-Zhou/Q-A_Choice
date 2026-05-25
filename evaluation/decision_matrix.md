# Decision matrix

> Living scoring document. Update by reading each per-question answer in
> `evaluation/results/*.json` and filling in a 0–3 score below. The
> aggregate matrix at the bottom is computed by hand from the scores.

## Scoring rubric

From `evaluation/questions.json` metadata:

| Score | Meaning |
|-------|---------|
| **3** | Fully correct: accurate, complete, with sources |
| **2** | Mostly correct: core info right, missing details or sources |
| **1** | Partially correct: has errors or important omissions |
| **0** | Wrong, hallucinated, **or** empty answer |

Below: one block per dimension, one row per question, score cells per
paradigm. Replace `_` with the score after reviewing the corresponding
JSON. GraphRAG cells stay `TBD` until M3.

## Single-hop (5 questions)

Results: `evaluation/results/{rag,agentic,graphrag}_single_hop.json`

| ID  | Question                                              | Expected | RAG | Agentic | GraphRAG |
|-----|-------------------------------------------------------|----------|:---:|:-------:|:--------:|
| 1.1 | ChatOpenAI temperature default                        | rag      | _   | _       | TBD      |
| 1.2 | RecursiveCharacterTextSplitter default chunk_size     | rag      | _   | _       | TBD      |
| 1.3 | LangSmith free plan traces/month                      | tie      | _   | _       | TBD      |
| 1.4 | BaseChatMessageHistory abstract methods               | rag      | _   | _       | TBD      |
| 1.5 | LangGraph interrupt version introduced                | agentic  | _   | _       | TBD      |
| **Subtotal (out of 15)** |                                            | –        | _/15 | _/15   | TBD      |

## Multi-hop (5 questions)

Results: `evaluation/results/{rag,agentic,graphrag}_multi_hop.json`

| ID  | Question                                                          | Expected | RAG | Agentic | GraphRAG |
|-----|-------------------------------------------------------------------|----------|:---:|:-------:|:--------:|
| 2.1 | LCEL chaining RunnablePassthrough + ChatPromptTemplate            | graphrag | _   | _       | TBD      |
| 2.2 | LangGraph agent with 3-retry tool calls — required components     | graphrag | _   | _       | TBD      |
| 2.3 | ConversationBufferMemory deprecation + LangGraph MemorySaver      | graphrag | _   | _       | TBD      |
| 2.4 | LangSmith @traceable ↔ LangChain callbacks                        | graphrag | _   | _       | TBD      |
| 2.5 | LangServe deployment + frontend client                            | agentic  | _   | _       | TBD      |
| **Subtotal (out of 15)** |                                                                | –        | _/15 | _/15   | TBD      |

## Cross-doc (5 questions)

Results: `evaluation/results/{rag,agentic,graphrag}_cross_doc.json`

| ID  | Question                                                              | Expected | RAG | Agentic | GraphRAG |
|-----|-----------------------------------------------------------------------|----------|:---:|:-------:|:--------:|
| 3.1 | AgentExecutor vs LangGraph agent — which to choose                    | agentic  | _   | _       | TBD      |
| 3.2 | Vector stores supported + best for production                         | agentic  | _   | _       | TBD      |
| 3.3 | Web-search agent — LangChain vs LangGraph approach                    | agentic  | _   | _       | TBD      |
| 3.4 | Document Loaders + Retrievers — roles and integration                 | tie      | _   | _       | TBD      |
| 3.5 | Official RAG chunking recommendation + historical evolution           | agentic  | _   | _       | TBD      |
| **Subtotal (out of 15)** |                                                                    | –        | _/15 | _/15   | TBD      |

## Operational metrics

Computed by `evaluation/compute_metrics.py` over the current contents
of `evaluation/results/`. Re-run after each evaluation pass.

|                              | Single-hop  | Multi-hop  | Cross-doc  |
|------------------------------|------------:|-----------:|-----------:|
| **RAG** — latency mean       | 4,874 ms    | 5,752 ms   | 7,058 ms   |
| **RAG** — success rate       | 5/5         | 5/5        | 5/5        |
| **Agentic** — latency mean   | 56,346 ms ⚠️ | 10,938 ms  | 9,901 ms   |
| **Agentic** — tool calls mean| 1.6         | 1.8        | 2.0        |
| **Agentic** — success rate   | 5/5         | 5/5        | 5/5        |
| **GraphRAG**                 | TBD (M3)    | TBD (M3)   | TBD (M3)   |

⚠️ Agentic single-hop mean is skewed by question 1.2 which took ~250 s on
this run — a Gemini API stall, not a paradigm limitation. Excluding 1.2,
the mean drops to roughly 7.7 s. Re-runs typically smooth it.

Notable signal: agentic tool-calls mean rising from 1.6 → 1.8 → 2.0
across dimensions is exactly the expected pattern — harder questions
trigger more search/read cycles. This is the agentic loop earning its
latency cost.

## Final matrix (fill after scoring)

|                  | Single-hop (avg / 3) | Multi-hop (avg / 3) | Cross-doc (avg / 3) | Avg latency |
|------------------|:--------------------:|:-------------------:|:-------------------:|:-----------:|
| **RAG**          | _                    | _                   | _                   | ~5.9 s      |
| **Agentic**      | _                    | _                   | _                   | ~10.4 s¹    |
| **GraphRAG**     | TBD                  | TBD                 | TBD                 | TBD         |

¹ Excluding the 250 s Q 1.2 outlier; raw mean across all 15 questions is ~26 s.

## Scenario recommendations (fill once scored)

Mirroring `PRODUCT.md §5.1`:

- **Scenario A — Customer FAQ / high-QPS retrieval:** TBD
- **Scenario B — Technical-docs assistant:** TBD
- **Scenario C — Compliance / legal / medical:** TBD
- **Scenario D — High-concurrency real-time:** TBD

## Per-paradigm observations

### RAG (Gemini 2.5 Flash + hybrid retrieval)

- 5/5 questions ran to completion in all three dimensions.
- Honest about gaps in context — produces "the provided context does not
  contain…" responses instead of fabricating (e.g., Q 1.2, Q 2.5).
- Known failure mode: source mismatch on Q 1.1. Hybrid retrieval pulls
  in `searchapi` (JS tools) examples that mention `temperature: 0`,
  and the answer leans on those instead of the canonical
  `langchain-openai` reference. Documented in commit `5e4fcc4`.

### Agentic (Gemini 2.5 Flash + `create_react_agent`)

- 5/5 success after the Flash upgrade. With Flash Lite the failure rate
  was 4/5 on multi-hop (see `README.md` § "Notes on model choice").
- Multi-step retrieval is visibly working: 3 tool calls on Q 3.4
  (Loaders + Retrievers) and Q 3.5 (chunking history); 2 calls on
  the trickier multi-hop questions.
- One latency outlier — Q 1.2 took 250 s on this run. Re-running gives
  normal 5–10 s latencies. Treat the 56 s single-hop mean as suspect.

### GraphRAG

Not yet implemented (M3). Will be populated alongside the M3 commit.

## Workflow

1. After each `run_one_paradigm.py` invocation, the corresponding
   `evaluation/results/<paradigm>_<dimension>.json` is overwritten.
2. Open the JSON. For each question, read the model's `answer` and
   the `retrieved_sources` / `tool_calls`, then judge against
   `source_hint`.
3. Score 0–3 per the rubric and update the relevant cell above.
4. Optionally add a sentence under "Per-paradigm observations" for
   any new failure-mode pattern you noticed.
5. Re-run `evaluation/compute_metrics.py` to refresh the operational
   metrics table after new runs land.
