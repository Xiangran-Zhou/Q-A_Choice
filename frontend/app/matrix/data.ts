// Static snapshot of evaluation/decision_matrix.md.
// Updated by hand when new scoring runs land — small enough to inline,
// avoids needing a backend just to render the matrix.
//
// Source of truth: evaluation/decision_matrix.md
// LLM-as-judge: Gemini 2.5 Pro with read_doc_file tool access.

export const PARADIGMS = ["rag", "agentic", "graphrag"] as const;
export type Paradigm = (typeof PARADIGMS)[number];

export const DIMENSIONS = ["single_hop", "multi_hop", "cross_doc"] as const;
export type Dimension = (typeof DIMENSIONS)[number];

export const PARADIGM_LABELS: Record<Paradigm, string> = {
  rag: "RAG",
  agentic: "Agentic",
  graphrag: "GraphRAG",
};

export const DIMENSION_LABELS: Record<Dimension, string> = {
  single_hop: "Single-hop",
  multi_hop: "Multi-hop",
  cross_doc: "Cross-doc",
};

export type ExpectedWinner = Paradigm | "tie";

export interface QuestionRecord {
  id: string;
  dimension: Dimension;
  title: string;
  expected: ExpectedWinner;
  scores: Record<Paradigm, number | null>; // null = pending
}

// 15 questions, scored per evaluation/decision_matrix.md after the
// first LLM-as-judge pass (RAG + Agentic only; GraphRAG pending M3).
export const QUESTIONS: QuestionRecord[] = [
  // Single-hop
  {
    id: "1.1",
    dimension: "single_hop",
    title: "ChatOpenAI temperature default",
    expected: "rag",
    scores: { rag: 1, agentic: 0, graphrag: 0 },
  },
  {
    id: "1.2",
    dimension: "single_hop",
    title: "RecursiveCharacterTextSplitter default chunk_size",
    expected: "rag",
    scores: { rag: 2, agentic: 1, graphrag: 1 },
  },
  {
    id: "1.3",
    dimension: "single_hop",
    title: "LangSmith free plan traces / month",
    expected: "tie",
    scores: { rag: 3, agentic: 3, graphrag: 2 },
  },
  {
    id: "1.4",
    dimension: "single_hop",
    title: "BaseChatMessageHistory abstract methods",
    expected: "rag",
    scores: { rag: 1, agentic: 1, graphrag: 2 },
  },
  {
    id: "1.5",
    dimension: "single_hop",
    title: "LangGraph interrupt — version introduced",
    expected: "agentic",
    scores: { rag: 1, agentic: 2, graphrag: 1 },
  },

  // Multi-hop
  {
    id: "2.1",
    dimension: "multi_hop",
    title: "LCEL chaining RunnablePassthrough + ChatPromptTemplate",
    expected: "graphrag",
    scores: { rag: 1, agentic: 3, graphrag: 2 },
  },
  {
    id: "2.2",
    dimension: "multi_hop",
    title: "LangGraph agent with 3-retry tool calls — required components",
    expected: "graphrag",
    scores: { rag: 1, agentic: 1, graphrag: 2 },
  },
  {
    id: "2.3",
    dimension: "multi_hop",
    title: "ConversationBufferMemory deprecation + MemorySaver",
    expected: "graphrag",
    scores: { rag: 1, agentic: 3, graphrag: 3 },
  },
  {
    id: "2.4",
    dimension: "multi_hop",
    title: "LangSmith @traceable ↔ LangChain callbacks",
    expected: "graphrag",
    scores: { rag: 1, agentic: 1, graphrag: 2 },
  },
  {
    id: "2.5",
    dimension: "multi_hop",
    title: "LangServe deployment + frontend client",
    expected: "agentic",
    scores: { rag: 1, agentic: 1, graphrag: 1 },
  },

  // Cross-doc
  {
    id: "3.1",
    dimension: "cross_doc",
    title: "AgentExecutor vs LangGraph agent — which to choose",
    expected: "agentic",
    scores: { rag: 1, agentic: 3, graphrag: 3 },
  },
  {
    id: "3.2",
    dimension: "cross_doc",
    title: "Vector stores supported + best for production",
    expected: "agentic",
    scores: { rag: 1, agentic: 3, graphrag: 1 },
  },
  {
    id: "3.3",
    dimension: "cross_doc",
    title: "Web-search agent — LangChain vs LangGraph approach",
    expected: "agentic",
    scores: { rag: 1, agentic: 3, graphrag: 2 },
  },
  {
    id: "3.4",
    dimension: "cross_doc",
    title: "Document Loaders + Retrievers — roles and integration",
    expected: "tie",
    scores: { rag: 1, agentic: 3, graphrag: 3 },
  },
  {
    id: "3.5",
    dimension: "cross_doc",
    title: "Official RAG chunking + historical evolution",
    expected: "agentic",
    scores: { rag: 1, agentic: 3, graphrag: 3 },
  },
];

export interface OperationalMetric {
  paradigm: Paradigm;
  dimension: Dimension;
  latencyMs: number | null;
  toolCallsMean: number | null;
  successRate: string;
  latencyNote?: string;
}

export const OPERATIONAL_METRICS: OperationalMetric[] = [
  // RAG (hybrid retrieval, single-shot Gemini Flash)
  { paradigm: "rag", dimension: "single_hop", latencyMs: 4874, toolCallsMean: null, successRate: "5/5" },
  { paradigm: "rag", dimension: "multi_hop", latencyMs: 5752, toolCallsMean: null, successRate: "5/5" },
  { paradigm: "rag", dimension: "cross_doc", latencyMs: 7058, toolCallsMean: null, successRate: "5/5" },

  // Agentic (create_react_agent + 2 tools)
  {
    paradigm: "agentic",
    dimension: "single_hop",
    latencyMs: 56346,
    toolCallsMean: 1.6,
    successRate: "5/5",
    latencyNote: "Skewed by Q 1.2 hanging ~250 s on a Gemini API stall. Without that outlier, mean ≈ 7.7 s.",
  },
  { paradigm: "agentic", dimension: "multi_hop", latencyMs: 10938, toolCallsMean: 1.8, successRate: "5/5" },
  { paradigm: "agentic", dimension: "cross_doc", latencyMs: 9901, toolCallsMean: 2.0, successRate: "5/5" },

  // GraphRAG (LightRAG + Gemini Flash, 1,471-doc knowledge graph)
  { paradigm: "graphrag", dimension: "single_hop", latencyMs: 11058, toolCallsMean: null, successRate: "5/5" },
  { paradigm: "graphrag", dimension: "multi_hop", latencyMs: 13874, toolCallsMean: null, successRate: "5/5" },
  { paradigm: "graphrag", dimension: "cross_doc", latencyMs: 12641, toolCallsMean: null, successRate: "5/5" },
];

export interface ScenarioRec {
  emoji: string;
  scenario: string;
  recommendation: string;
  rationale: string;
}

export const SCENARIO_RECOMMENDATIONS: ScenarioRec[] = [
  {
    emoji: "💬",
    scenario: "Customer FAQ / high-QPS retrieval",
    recommendation: "RAG",
    rationale:
      "Single-hop scores nearly tied (8 vs 7), but RAG is ~2× faster on multi-hop / cross-doc and runs at a fraction of the per-query cost. Latency floor matters more than ceiling correctness for FAQ workloads.",
  },
  {
    emoji: "🛠️",
    scenario: "Technical-docs assistant / developer tools",
    recommendation: "Agentic",
    rationale:
      "Multi-hop and cross-doc both go to Agentic by wide margins (9 vs 5 and 15 vs 5). Developer questions are cross-doc by nature; the agent's multi-search loop reliably synthesises across pages.",
  },
  {
    emoji: "⚖️",
    scenario: "Compliance / legal / medical",
    recommendation: "GraphRAG",
    rationale:
      "Multi-hop 10/15 is the highest of any paradigm — GraphRAG narrowly beats Agentic on multi-hop reasoning (10 vs 9), confirming the pre-experiment hypothesis. Compliance domains demand relationship traceability that graph traversal makes auditable.",
  },
  {
    emoji: "⚡",
    scenario: "High-concurrency real-time",
    recommendation: "RAG + intent routing",
    rationale:
      "Only RAG fits the latency budget. The realistic move is to sniff for cross-doc / multi-hop intent and route those to a slower Agentic backend; serve simple lookups from RAG.",
  },
];

// M3 completed — kept as null so the page can hide the banner.
// Historical context (kept for narrative): build took multiple sessions
// due to Gemini Tier 1 daily-quota cap; full story in README.
export const M3_STATUS: null | {
  processed: number;
  total: number;
  pendingRetry: number;
  reasonForPause: string;
  resumeAction: string;
} = null;

// Aggregate helper.
export interface AggregateRow {
  paradigm: Paradigm;
  single_hop: number | null;
  multi_hop: number | null;
  cross_doc: number | null;
}

export function computeAggregates(): AggregateRow[] {
  return PARADIGMS.map((paradigm) => {
    const row: AggregateRow = {
      paradigm,
      single_hop: null,
      multi_hop: null,
      cross_doc: null,
    };
    for (const dim of DIMENSIONS) {
      const dimScores = QUESTIONS.filter((q) => q.dimension === dim).map((q) => q.scores[paradigm]);
      if (dimScores.every((s) => s !== null)) {
        row[dim] = dimScores.reduce((a, b) => (a as number) + (b as number), 0) as number;
      }
    }
    return row;
  });
}
