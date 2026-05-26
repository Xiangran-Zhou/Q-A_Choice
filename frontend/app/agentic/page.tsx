import type { Metadata } from "next";

import QueryPanel from "../_components/QueryPanel";

export const metadata: Metadata = {
  title: "Agentic Search · Q&A Paradigm Lab",
  description:
    "LangGraph create_react_agent + two retrieval tools, multi-turn tool use, synthesised answer.",
};

export default function Page() {
  return (
    <div className="space-y-8">
      <section className="space-y-2">
        <h2 className="text-2xl font-semibold tracking-tight">Agentic Search</h2>
        <p className="text-sm leading-relaxed text-foreground/70">
          A <strong>LangGraph ReAct agent</strong> driving <strong>Gemini 2.5 Flash</strong> with
          two tools: <code className="rounded bg-foreground/5 px-1.5 py-0.5 text-xs">search_docs_vector</code>{" "}
          (the same hybrid retriever the RAG page uses) and{" "}
          <code className="rounded bg-foreground/5 px-1.5 py-0.5 text-xs">read_doc_file</code>{" "}
          (drill into a specific <code>.mdx</code> by path). The tool-call timeline below
          shows the &ldquo;where it looked&rdquo; trail for each answer — the moves that
          separate Agentic from single-shot RAG.
        </p>
      </section>

      <QueryPanel paradigm="agentic" />
    </div>
  );
}
