export default function Page() {
  return (
    <div className="space-y-3">
      <h2 className="text-2xl font-semibold tracking-tight">Traditional RAG</h2>
      <p className="text-foreground/70">
        Vector retrieval (Chroma) + BM25 hybrid, single-shot generation with
        Gemini Flash Lite.
      </p>
      <p className="text-sm text-foreground/50">
        Coming soon — backend stub is wired up; the chat interface and retrieved-chunks
        panel land in the next milestone.
      </p>
    </div>
  );
}
