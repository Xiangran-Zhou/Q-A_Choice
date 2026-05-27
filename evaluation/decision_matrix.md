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

Results: `evaluation/results/scored_{rag,agentic,graphrag}_single_hop.json`

| ID  | Question                                              | Expected | RAG | Agentic | GraphRAG |
|-----|-------------------------------------------------------|----------|:---:|:-------:|:--------:|
| 1.1 | ChatOpenAI temperature default                        | rag      | 1   | 0       | 0        |
| 1.2 | RecursiveCharacterTextSplitter default chunk_size     | rag      | 2   | 1       | 1        |
| 1.3 | LangSmith free plan traces/month                      | tie      | 3   | 3       | 2        |
| 1.4 | BaseChatMessageHistory abstract methods               | rag      | 1   | 1       | 2        |
| 1.5 | LangGraph interrupt version introduced                | agentic  | 1   | 2       | 1        |
| **Subtotal (out of 15)** |                                            | –        | **8** | **7** | **6**    |

**Judge highlights**:
- 1.1: All three paradigms got this wrong. RAG hallucinated "0", Agentic gave `ChatContextual`'s default not `ChatOpenAI`'s, GraphRAG aggregated the same wrong "0" from multiple cited chunks. **The temperature default is genuinely scattered across the docs in a way that fooled every retrieval approach.**
- 1.4: GraphRAG narrowly edged the other two — judge gave it 2 because it honestly said "context insufficient" after searching multiple paths, while RAG/Agentic fabricated wrong abstract method names.
- 1.5: Agentic still wins by inferring "interrupt existed before v1" from release notes. GraphRAG slightly worse — it correctly noted v1 added "typed interrupts" but failed to infer earlier baseline.

## Multi-hop (5 questions)

Results: `evaluation/results/scored_{rag,agentic,graphrag}_multi_hop.json`

| ID  | Question                                                          | Expected | RAG | Agentic | GraphRAG |
|-----|-------------------------------------------------------------------|----------|:---:|:-------:|:--------:|
| 2.1 | LCEL chaining RunnablePassthrough + ChatPromptTemplate            | graphrag | 1   | 3       | 2        |
| 2.2 | LangGraph agent with 3-retry tool calls — required components     | graphrag | 1   | 1       | 2        |
| 2.3 | ConversationBufferMemory deprecation + LangGraph MemorySaver      | graphrag | 1   | 3       | 3        |
| 2.4 | LangSmith @traceable ↔ LangChain callbacks                        | graphrag | 1   | 1       | 2        |
| 2.5 | LangServe deployment + frontend client                            | agentic  | 1   | 1       | 1        |
| **Subtotal (out of 15)** |                                                                | –        | **5** | **9** | **10**   |

**Judge highlights**:
- 2.1: Agentic synthesised the role-of-each-component story best (3); GraphRAG was technically correct on definitions (2) but less narrative.
- 2.2: GraphRAG correctly identified `ToolNode + RetryPolicy` (2) where Agentic mis-attributed `ToolRetryMiddleware` to LangGraph (1). Graph traversal helped here.
- 2.3: GraphRAG and Agentic both got the full 3 — the new "ConversationBufferMemory → checkpointer" relationship is exactly the kind of multi-entity question graph + multi-search both handle well.
- **GraphRAG wins this dimension 10 vs 9**, the first place it beats Agentic — vindicating PRODUCT.md's pre-experiment prediction that GraphRAG's multi-hop reasoning is its home turf.

## Cross-doc (5 questions)

Results: `evaluation/results/scored_{rag,agentic,graphrag}_cross_doc.json`

| ID  | Question                                                              | Expected | RAG | Agentic | GraphRAG |
|-----|-----------------------------------------------------------------------|----------|:---:|:-------:|:--------:|
| 3.1 | AgentExecutor vs LangGraph agent — which to choose                    | agentic  | 1   | 3       | 3        |
| 3.2 | Vector stores supported + best for production                         | agentic  | 1   | 3       | 1        |
| 3.3 | Web-search agent — LangChain vs LangGraph approach                    | agentic  | 1   | 3       | 2        |
| 3.4 | Document Loaders + Retrievers — roles and integration                 | tie      | 1   | 3       | 3        |
| 3.5 | Official RAG chunking recommendation + historical evolution           | agentic  | 1   | 3       | 3        |
| **Subtotal (out of 15)** |                                                                    | –        | **5** | **15** | **12**   |

**Judge highlights**:
- 3.1, 3.4, 3.5: GraphRAG matches Agentic's perfect-3 — relationship-heavy questions where the graph's "X relates-to Y" edges pay off as well as Agentic's multi-search.
- 3.2: GraphRAG fumbled (1) — it correctly said "LangChain supports many" but its list was severely incomplete. Agent-style multi-search beat graph traversal here because the answer required *enumeration*, not relationship reasoning.
- 3.3: GraphRAG got 2 because while accurate, it didn't synthesise specific code examples the way Agentic did.
- **Agentic dominates this dimension 15 vs 12**, but GraphRAG is a close second — both far ahead of RAG's 5.

## Operational metrics

Computed by `evaluation/compute_metrics.py` over the current contents
of `evaluation/results/`. Re-run after each evaluation pass.

|                              | Single-hop   | Multi-hop  | Cross-doc  |
|------------------------------|-------------:|-----------:|-----------:|
| **RAG** — latency mean       | 4,874 ms     | 5,752 ms   | 7,058 ms   |
| **RAG** — success rate       | 5/5          | 5/5        | 5/5        |
| **Agentic** — latency mean   | 56,346 ms ⚠️ | 10,938 ms  | 9,901 ms   |
| **Agentic** — tool calls mean| 1.6          | 1.8        | 2.0        |
| **Agentic** — success rate   | 5/5          | 5/5        | 5/5        |
| **GraphRAG** — latency mean  | 11,058 ms    | 13,874 ms  | 12,641 ms  |
| **GraphRAG** — success rate  | 5/5          | 5/5        | 5/5        |

⚠️ Agentic single-hop latency is skewed by Q 1.2 (~250 s — a Gemini API
stall on that one call). Excluding 1.2, mean drops to ~7.7 s.

Notable: GraphRAG latency is **~2× RAG** and similar to Agentic — but
without Agentic's outlier variance. It's a very *consistent* paradigm
once the knowledge graph is built.

## Final matrix

| Paradigm     | Single-hop      | Multi-hop      | Cross-doc      | Overall          | Avg latency  |
|--------------|:---------------:|:--------------:|:--------------:|:----------------:|:------------:|
| **RAG**      | 8/15 (1.60)     | 5/15 (1.00)    | 5/15 (1.00)    | **18/45 (40%)**  | ~5.9 s       |
| **Agentic**  | 7/15 (1.40)     | 9/15 (1.80)    | 15/15 (3.00)   | **31/45 (69%)**  | ~9.4 s¹      |
| **GraphRAG** | 6/15 (1.20)     | 10/15 (2.00)   | 12/15 (2.40)   | **28/45 (62%)**  | ~12.5 s      |

¹ Agentic mean across 15 questions, excluding the single 250 s Q 1.2
outlier. Raw mean is ~26 s.

**Ranking by dimension** (winner per row):

- Single-hop: **RAG (8) > Agentic (7) > GraphRAG (6)** — RAG's home turf
- Multi-hop: **GraphRAG (10) > Agentic (9) > RAG (5)** — graph wins here
- Cross-doc: **Agentic (15) > GraphRAG (12) > RAG (5)** — multi-search wins
- Overall: **Agentic (31) > GraphRAG (28) > RAG (18)**

## Scenario recommendations

Based on the now-complete three-paradigm data, mirroring `PRODUCT.md §5.1`:

### Scenario A — Customer FAQ / high-QPS retrieval
**Recommendation: RAG.**
RAG narrowly wins single-hop (8 vs 7 vs 6) and is **~2× faster than
GraphRAG / Agentic**. The 8/15 isn't great, but RAG's failure modes
(1.1 hallucination, 1.4 wrong answer) are the kind better chunking +
reranking can fix without changing paradigm. For FAQ workloads, the
latency floor matters more than ceiling correctness.

### Scenario B — Technical-docs assistant / developer tools
**Recommendation: Agentic.**
Cross-doc 15/15 is decisive — developer questions are cross-doc by
nature, and Agentic's multi-search loop reliably synthesises across
pages. GraphRAG is a close second (12/15) and would be a defensible
alternative if you needed lower latency variance (no outliers). RAG
out at 5/15 here.

### Scenario C — Compliance / legal / medical
**Recommendation: GraphRAG.**
Multi-hop 10/15 is the highest of any paradigm — **GraphRAG beats
Agentic on multi-hop reasoning** (10 vs 9), confirming the
pre-experiment hypothesis. Compliance domains demand explicit
relationship traceability (regulation X applies to entity Y under
condition Z) — exactly what graph traversal makes auditable. The 2×
latency vs RAG is acceptable when correctness is non-negotiable.

### Scenario D — High-concurrency real-time
**Recommendation: RAG + intent routing.**
Only RAG fits a sub-second latency budget. The realistic move is to
sniff for cross-doc / multi-hop intent and route those *out* of the
RAG path — to an Agentic backend (best cross-doc) or GraphRAG (best
multi-hop). The data shows RAG is reliable only on single-hop fact
lookups; pretending otherwise in production produces the 5/15
multi-hop score.

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

### GraphRAG (LightRAG + Gemini 2.5 Flash; 1,471-doc knowledge graph)

- **Wins multi-hop overall (10/15)** — beats Agentic by 1 point.
  Where the answer requires "X relates-to Y under condition Z", the
  graph traversal pays off (Q 2.2, 2.3). PRODUCT.md predicted this;
  the data confirmed it.
- **Loses single-hop** (6/15 vs RAG's 8) — entity-graph reasoning is
  overkill for simple fact lookup. Q 1.1 inherited the same
  hallucination as RAG (the docs themselves have "temperature: 0"
  examples scattered everywhere, fooling graph-based aggregation too).
- **Consistent latency** (11-14 s, no outliers) thanks to deterministic
  graph traversal — unlike Agentic where some questions burst tool
  calls and others don't.
- **Knowledge graph stats**: 1471/1472 docs ingested (1 tiktoken
  failure), ~66k entities, ~125k relations. Build took multiple
  sessions due to Gemini Tier 1 daily quota — see README "Notes on
  GraphRAG build" for the operational story.

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
