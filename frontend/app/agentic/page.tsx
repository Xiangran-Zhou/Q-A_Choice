export default function Page() {
  return (
    <div className="space-y-3">
      <h2 className="text-2xl font-semibold tracking-tight">Agentic Search</h2>
      <p className="text-foreground/70">
        LangGraph agent with document-search tools (Mintlify API + filesystem) and
        multi-turn tool use, adapted from <code>chat-langchain</code>.
      </p>
      <p className="text-sm text-foreground/50">
        Coming soon — backend stub is wired up; the chat interface and tool-call
        timeline panel land in the next milestone.
      </p>
    </div>
  );
}
