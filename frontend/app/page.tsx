import Link from "next/link";

const tabs = [
  {
    href: "/rag",
    title: "Traditional RAG",
    description: "Vector retrieval (Chroma) + BM25 hybrid, single-shot generation.",
  },
  {
    href: "/agentic",
    title: "Agentic Search",
    description: "LangGraph agent with document-search tools and multi-turn tool use.",
  },
  {
    href: "/graphrag",
    title: "GraphRAG",
    description: "Knowledge-graph extraction + multi-hop traversal + generation.",
  },
  {
    href: "/compare",
    title: "Side-by-side",
    description: "All three paradigms answering the same question, simultaneously.",
  },
  {
    href: "/matrix",
    title: "Decision matrix",
    description: "Evaluation results and per-scenario selection recommendations.",
  },
] as const;

export default function Home() {
  return (
    <div className="space-y-10">
      <section className="space-y-3">
        <h1 className="text-3xl font-semibold tracking-tight">Q&amp;A Paradigm Lab</h1>
        <p className="max-w-2xl leading-relaxed text-foreground/70">
          A side-by-side comparison of three AI document-Q&amp;A paradigms answering the
          same questions against the same corpus. Pick a tab above to explore each
          paradigm individually, run them in parallel, or jump straight to the decision
          matrix.
        </p>
      </section>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {tabs.map((tab) => (
          <Link
            key={tab.href}
            href={tab.href}
            className="rounded-lg border border-foreground/15 p-4 transition-colors hover:bg-foreground/5"
          >
            <div className="font-medium">{tab.title}</div>
            <div className="mt-1 text-sm text-foreground/60">{tab.description}</div>
          </Link>
        ))}
      </section>

      <section className="text-xs text-foreground/50">
        Status: skeleton — pages are placeholders until backend integration lands.
      </section>
    </div>
  );
}
