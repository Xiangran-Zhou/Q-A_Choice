export default function Page() {
  return (
    <div className="space-y-3">
      <h2 className="text-2xl font-semibold tracking-tight">GraphRAG</h2>
      <p className="text-foreground/70">
        Knowledge-graph extraction (LightRAG) + 1-3 hop graph traversal + generation.
      </p>
      <p className="text-sm text-foreground/50">
        Coming soon — backend stub is wired up; the chat interface and graph-traversal
        visualization land in the next milestone.
      </p>
    </div>
  );
}
