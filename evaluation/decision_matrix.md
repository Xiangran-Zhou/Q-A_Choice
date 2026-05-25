# Decision matrix

> Living scoring document. Scores come from **Gemini 2.5 Pro acting as
> judge** (with `read_doc_file` tool access for verification — see
> `evaluation/judge.py`), one notch above the Gemini 2.5 Flash
> generator. Re-running `evaluation/judge.py --all` followed by
> `evaluation/compute_metrics.py` refreshes the numbers below.

## Scoring rubric

From `evaluation/questions.json` metadata:

| Score | Meaning |
|-------|---------|
| **3** | Fully correct: accurate, complete, with sources |
| **2** | Mostly correct: core info right, missing details or sources |
| **1** | Partially correct: has errors or important omissions |
| **0** | Wrong, hallucinated, **or** empty answer |

## Single-hop (5 questions)

Results: `evaluation/results/scored_{rag,agentic}_single_hop.json`

| ID  | Question                                              | Expected | RAG | Agentic | GraphRAG |
|-----|-------------------------------------------------------|----------|:---:|:-------:|:--------:|
| 1.1 | ChatOpenAI temperature default                        | rag      | 1   | 0       | TBD      |
| 1.2 | RecursiveCharacterTextSplitter default chunk_size     | rag      | 2   | 1       | TBD      |
| 1.3 | LangSmith free plan traces/month                      | tie      | 3   | 3       | TBD      |
| 1.4 | BaseChatMessageHistory abstract methods               | rag      | 1   | 1       | TBD      |
| 1.5 | LangGraph interrupt version introduced                | agentic  | 1   | 2       | TBD      |
| **Subtotal (out of 15)** |                                            | –        | **8** | **7** | TBD      |

**Judge highlights**:
- 1.1: RAG hallucinated the default (presented `temperature: 0` examples as the default); Agentic gave the default for `ChatContextual`, not `ChatOpenAI` — both wrong, but Agentic's wrong was more wrong.
- 1.4: Both paradigms wrongly claimed the abstract methods are the async variants (`aget_messages`, etc.). The judge verified the actual abstract methods via the docs.
- 1.5: Agentic edged ahead by inferring a defensible "interrupt existed before v1" from the docs it read; RAG fabricated a code-example claim that didn't hold up.

## Multi-hop (5 questions)

Results: `evaluation/results/scored_{rag,agentic}_multi_hop.json`

| ID  | Question                                                          | Expected | RAG | Agentic | GraphRAG |
|-----|-------------------------------------------------------------------|----------|:---:|:-------:|:--------:|
| 2.1 | LCEL chaining RunnablePassthrough + ChatPromptTemplate            | graphrag | 1   | 3       | TBD      |
| 2.2 | LangGraph agent with 3-retry tool calls — required components     | graphrag | 1   | 1       | TBD      |
| 2.3 | ConversationBufferMemory deprecation + LangGraph MemorySaver      | graphrag | 1   | 3       | TBD      |
| 2.4 | LangSmith @traceable ↔ LangChain callbacks                        | graphrag | 1   | 1       | TBD      |
| 2.5 | LangServe deployment + frontend client                            | agentic  | 1   | 1       | TBD      |
| **Subtotal (out of 15)** |                                                                | –        | **5** | **9** | TBD      |

**Judge highlights**:
- 2.1: RAG claimed the context didn't contain the answer when the judge verified it did — punished 1; Agentic actually synthesized and got 3.
- 2.2: Both paradigms wrongly applied `ToolRetryMiddleware` to LangGraph rather than LangChain agents (the middleware lives in `langchain.agents.middleware`). Tied at 1.
- 2.3: Agentic's two-search pattern paid off — correctly identified that `ConversationBufferMemory` moved to `langchain-classic` and connected it to `MemorySaver`.

## Cross-doc (5 questions)

Results: `evaluation/results/scored_{rag,agentic}_cross_doc.json`

| ID  | Question                                                              | Expected | RAG | Agentic | GraphRAG |
|-----|-----------------------------------------------------------------------|----------|:---:|:-------:|:--------:|
| 3.1 | AgentExecutor vs LangGraph agent — which to choose                    | agentic  | 1   | 3       | TBD      |
| 3.2 | Vector stores supported + best for production                         | agentic  | 1   | 3       | TBD      |
| 3.3 | Web-search agent — LangChain vs LangGraph approach                    | agentic  | 1   | 3       | TBD      |
| 3.4 | Document Loaders + Retrievers — roles and integration                 | tie      | 1   | 3       | TBD      |
| 3.5 | Official RAG chunking recommendation + historical evolution           | agentic  | 1   | 3       | TBD      |
| **Subtotal (out of 15)** |                                                                    | –        | **5** | **15** | TBD      |

**Cross-doc is where the agentic pattern earns its keep**: 15/15 perfect.
The agent did 2–3 searches per question with varying queries (verified
in the `tool_calls` field of the un-scored reports), giving it material
from multiple parts of the docs to synthesize. RAG ran a single hybrid
retrieval and consistently misframed the question — judge punished
every cross-doc answer at score 1, including 3.5 where RAG claimed the
answer wasn't in the docs but the judge confirmed the main RAG tutorial
page covers it.

## Operational metrics (from `compute_metrics.py`)

|                              | Single-hop   | Multi-hop  | Cross-doc  |
|------------------------------|-------------:|-----------:|-----------:|
| **RAG** — latency mean       | 4,874 ms     | 5,752 ms   | 7,058 ms   |
| **RAG** — success rate       | 5/5          | 5/5        | 5/5        |
| **Agentic** — latency mean   | 56,346 ms ⚠️ | 10,938 ms  | 9,901 ms   |
| **Agentic** — tool calls mean| 1.6          | 1.8        | 2.0        |
| **Agentic** — success rate   | 5/5          | 5/5        | 5/5        |
| **GraphRAG**                 | TBD (M3)     | TBD (M3)   | TBD (M3)   |

⚠️ Agentic single-hop latency is skewed by Q 1.2 (~250 s — a Gemini API
stall on that one call). Excluding 1.2, mean drops to ~7.7 s.

## Final matrix

| Paradigm     | Single-hop      | Multi-hop      | Cross-doc      | Overall          | Avg latency  |
|--------------|:---------------:|:--------------:|:--------------:|:----------------:|:------------:|
| **RAG**      | 8/15 (1.60)     | 5/15 (1.00)    | 5/15 (1.00)    | **18/45 (40%)**  | ~5.9 s       |
| **Agentic**  | 7/15 (1.40)     | 9/15 (1.80)    | 15/15 (3.00)   | **31/45 (69%)**  | ~9.4 s¹      |
| **GraphRAG** | TBD             | TBD            | TBD            | TBD              | TBD          |

¹ Mean across all 15 questions, excluding the single 250 s Q 1.2
outlier. Raw mean is ~26 s.

## Scenario recommendations

Mirroring `PRODUCT.md §5.1`, with one important update — the actual
numbers tell a slightly different story than the pre-experiment
intuition:

### Scenario A — Customer FAQ / high-QPS retrieval
**Recommendation: RAG.**
On single-hop, RAG (8) edges Agentic (7). The 8/15 isn't great in
absolute terms, but RAG is **6× faster** (5 s vs 56 s mean — even
adjusted for the outlier, ~5 s vs ~10 s) and runs at a fraction of the
per-query cost. For FAQ workloads the latency floor matters more than
ceiling correctness, and RAG's failure modes here (1.1 hallucination,
1.4 wrong answer) are the kind that better single-hop chunking +
reranking would fix without changing paradigm.

### Scenario B — Technical-docs assistant / developer tools
**Recommendation: Agentic.**
Multi-hop and cross-doc both go to Agentic by wide margins (9 vs 5 and
15 vs 5). Developer questions are almost always cross-doc by nature —
"how do X and Y interact" — and the data shows the agentic loop's
multi-search pattern handles those reliably, including questions where
RAG insisted the docs didn't contain the answer when they did. The ~2×
latency tax is acceptable for an IDE-side or chat-side helper.

### Scenario C — Compliance / legal / medical
**Recommendation: GraphRAG (pending M3 data).**
Not yet measured, but the project plan's framing still holds: these
domains demand explicit relationship traceability that neither
retrieval nor a multi-step agent surfaces cleanly. Will revisit once
M3 lands.

### Scenario D — High-concurrency real-time
**Recommendation: RAG, with explicit "I don't know" routing.**
Only RAG fits the latency budget here. The realistic move is to
sniff for cross-doc / multi-hop intent and route those *out* of the
RAG path (escalate to a slower Agentic backend or return a graceful
"this is being researched, here's a partial answer"). The data shows
RAG is reliable only on single-hop fact lookups; pretending otherwise
in production produces the 5/15 multi-hop score above.

## Per-paradigm observations

### RAG (Gemini 2.5 Flash + hybrid retrieval, top-10 chunks)

- Success rate 15/15 (no crashes) but quality is consistently 1 on
  anything past single-hop. RAG **produces** an answer reliably but
  isn't **right** reliably.
- Distinctive failure pattern: confidently citing the wrong source.
  Q 1.1 cites `searchapi.mdx` for ChatOpenAI's temperature default;
  judge caught the source mismatch.
- Honesty failure mode: claiming the docs don't contain an answer when
  they do (Q 2.1, Q 3.5). Judge punished these at 1 since the failure
  is a retrieval miss, not a corpus gap.

### Agentic (Gemini 2.5 Flash + `create_react_agent` + 2 tools)

- Bimodal score distribution: when the agent uses ≥2 searches it
  tends to land 3s; when it does one search it tends to mirror RAG's
  failure modes. Tool-call mean of 2.0 on cross-doc directly explains
  the 15/15 cross-doc total.
- Q 1.1 score 0 is the worst single answer in the run — the agent
  retrieved `ChatContextual` docs and returned that as the answer for
  `ChatOpenAI`. Lesson: retrieval mismatches that an LLM-only RAG
  would launder into "looks-like-an-answer" output get exposed when
  the agent commits to a specific cited source.
- Latency is paradigm-real: ~10 s mean on multi-hop / cross-doc,
  not counting the Q 1.2 outlier. This is the cost of the loop.

### GraphRAG

Not yet implemented (M3). The plan expects it to lift Multi-hop /
Cross-doc above Agentic in domains with rich entity relationships;
LangChain documentation may or may not be such a domain (the docs
are a fairly flat set of how-to pages, not a deeply entity-linked
corpus). M3 will tell.

## Methodology notes

- **LLM-as-judge, not human scoring.** This is a deliberate switch
  from the original plan. Rationale and the comparison to RAGAS-style
  scoring is in the top-level [`README.md`](../README.md) and in the
  judge's own prompt at `evaluation/judge.py`.
- **Blind judging.** The judge prompt never reveals which paradigm
  produced an answer — only the question, the source hint, the
  retrieved sources, and the candidate answer.
- **Judge model is one notch above generator** (Pro vs Flash), the
  standard LLM-as-judge guardrail against self-preference.
- **Judge uses tools.** Every claim of "the docs say X" can be
  verified by calling `read_doc_file`. The `verified_sources` field in
  each scored result captures which paths the judge actually opened.

## Workflow

1. Re-run candidates: `cd backend && uv run python ../evaluation/run_one_paradigm.py --paradigm <p> --dimension <d>`
2. Re-judge:         `uv run python ../evaluation/judge.py --paradigm <p> --dimension <d>` (or `--all`)
3. Refresh tables:   `uv run python ../evaluation/compute_metrics.py`
4. Hand-edit this file with any new scores / observations.
