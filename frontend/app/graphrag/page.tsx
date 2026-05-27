import type { Metadata } from "next";

import QueryPanel from "../_components/QueryPanel";

export const metadata: Metadata = {
  title: "GraphRAG · Q&A Paradigm Lab",
  description:
    "LightRAG knowledge-graph extraction + multi-hop traversal + Gemini Flash generation.",
};

export default function Page() {
  return (
    <div className="space-y-8">
      <section className="space-y-2">
        <h2 className="text-2xl font-semibold tracking-tight">GraphRAG</h2>
        <p className="text-sm leading-relaxed text-foreground/70">
          A <strong>LightRAG</strong>-built knowledge graph over the LangChain docs
          (~66k entities, ~125k relations from 1,471 source files) drives a hybrid
          query: entity-graph traversal fused with vector retrieval over the same
          chunks, then <strong>Gemini 2.5 Flash</strong> synthesises the final
          answer. The retrieved-chunks panel below shows the merged entity /
          relation / chunk context block LightRAG surfaced.
        </p>
        <p className="text-xs leading-relaxed text-foreground/55">
          Quick stats from the LLM-as-judge eval:{" "}
          <strong>10/15 on multi-hop</strong> (the highest of any paradigm —
          beats Agentic 9/15) but only{" "}
          <strong>6/15 on single-hop</strong> (entity reasoning overkill for
          simple fact lookup). See the{" "}
          <a className="underline" href="/matrix">
            decision matrix
          </a>{" "}
          for the full breakdown.
        </p>
      </section>

      <QueryPanel paradigm="graphrag" />
    </div>
  );
}
