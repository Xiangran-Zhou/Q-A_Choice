export default function Page() {
  return (
    <div className="space-y-3">
      <h2 className="text-2xl font-semibold tracking-tight">Decision matrix</h2>
      <p className="text-foreground/70">
        Evaluation results across single-hop, multi-hop, and cross-document scenarios,
        plus per-scenario selection recommendations: when to reach for RAG, when for
        Agentic, when for GraphRAG.
      </p>
      <p className="text-sm text-foreground/50">
        Coming soon — populated once the 20-question evaluation is scored.
      </p>
    </div>
  );
}
