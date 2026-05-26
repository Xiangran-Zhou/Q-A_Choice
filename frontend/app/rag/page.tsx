import type { Metadata } from "next";

import QueryPanel from "../_components/QueryPanel";

export const metadata: Metadata = {
  title: "Traditional RAG · Q&A Paradigm Lab",
  description:
    "Hybrid retrieval (Chroma vector + BM25) + single-shot Gemini Flash generation.",
};

export default function Page() {
  return (
    <div className="space-y-8">
      <section className="space-y-2">
        <h2 className="text-2xl font-semibold tracking-tight">Traditional RAG</h2>
        <p className="text-sm leading-relaxed text-foreground/70">
          Hybrid retrieval over a local <strong>Chroma</strong> index of the LangChain
          docs (28k chunks), fused with <strong>BM25</strong> over the same chunks
          via reciprocal rank fusion, then a single-shot <strong>Gemini 2.5 Flash</strong> call.
          The retrieved chunks shown below are the evidence the model saw.
        </p>
      </section>

      <QueryPanel paradigm="rag" />
    </div>
  );
}
