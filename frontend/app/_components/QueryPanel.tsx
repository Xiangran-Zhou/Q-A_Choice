"use client";

import { useState } from "react";

import {
  BackendError,
  queryParadigm,
  type Paradigm,
  type QueryResponse,
} from "@/lib/api";

interface Props {
  paradigm: Paradigm;
  /** Sample questions users can click to populate the input. */
  sampleQuestions?: string[];
  /** What to call the evidence section ("Retrieved chunks", "Tool calls", etc). */
  evidenceLabel?: string;
}

const DEFAULT_SAMPLES: Record<Paradigm, string[]> = {
  rag: [
    "What is the default value of the temperature parameter in ChatOpenAI?",
    "How many traces does the LangSmith free plan include per month?",
    "What is the default chunk_size of RecursiveCharacterTextSplitter?",
  ],
  agentic: [
    "I want to build a LangGraph agent that automatically retries 3 times when tool calls fail. What components do I need?",
    "ConversationBufferMemory is deprecated. What replaces it, and how does it relate to LangGraph's MemorySaver?",
    "What is the relationship between LangSmith's @traceable decorator and LangChain's callbacks system?",
  ],
  graphrag: [
    "How does LangGraph's interrupt function work?",
    "What is the relationship between AgentExecutor and the LangGraph agent migration?",
  ],
};

function fmtLatency(ms: number) {
  if (ms < 1000) return `${ms} ms`;
  return `${(ms / 1000).toFixed(1)} s`;
}

export default function QueryPanel({
  paradigm,
  sampleQuestions,
  evidenceLabel,
}: Props) {
  const samples = sampleQuestions ?? DEFAULT_SAMPLES[paradigm];

  const [question, setQuestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<BackendError | null>(null);

  async function handleSubmit(e?: React.FormEvent) {
    e?.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || isLoading) return;
    setIsLoading(true);
    setError(null);
    setResponse(null);
    try {
      const result = await queryParadigm(paradigm, trimmed);
      setResponse(result);
    } catch (err) {
      if (err instanceof BackendError) {
        setError(err);
      } else {
        setError(
          new BackendError(
            { kind: "unknown_error", message: String(err) },
            0,
          ),
        );
      }
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Question form */}
      <form onSubmit={handleSubmit} className="space-y-3">
        <label className="block">
          <span className="mb-1.5 block text-sm font-medium text-foreground/80">
            Ask a question about the LangChain documentation
          </span>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={isLoading}
            placeholder="e.g. How does LangGraph's interrupt function work?"
            rows={2}
            className="w-full rounded-md border border-foreground/20 bg-background px-3 py-2 text-sm shadow-sm transition-colors placeholder:text-foreground/40 focus:border-foreground/40 focus:outline-none focus:ring-2 focus:ring-foreground/10 disabled:opacity-50"
            onKeyDown={(e) => {
              if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
                handleSubmit();
              }
            }}
          />
        </label>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="submit"
            disabled={isLoading || !question.trim()}
            className="rounded-md bg-foreground px-4 py-1.5 text-sm font-medium text-background transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {isLoading ? "Asking…" : "Ask"}
          </button>
          <span className="text-xs text-foreground/40">
            ⌘ + Enter to submit
          </span>
        </div>
        {samples.length > 0 && (
          <div className="flex flex-wrap gap-2 pt-1">
            <span className="text-xs text-foreground/50 mr-1 self-center">
              try:
            </span>
            {samples.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setQuestion(s)}
                disabled={isLoading}
                className="rounded-full border border-foreground/15 px-3 py-1 text-xs text-foreground/70 transition-colors hover:bg-foreground/5 disabled:opacity-40"
              >
                {s.length > 70 ? s.slice(0, 67) + "…" : s}
              </button>
            ))}
          </div>
        )}
      </form>

      {/* Error state */}
      {error && <ErrorBanner error={error} />}

      {/* Loading state */}
      {isLoading && !response && (
        <div className="rounded-lg border border-foreground/15 bg-foreground/5 p-4 text-sm text-foreground/60">
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 animate-pulse rounded-full bg-foreground/40" />
            Querying the {paradigm} graph…
          </div>
        </div>
      )}

      {/* Response */}
      {response && !isLoading && (
        <ResponseView response={response} evidenceLabel={evidenceLabel} />
      )}
    </div>
  );
}

function ErrorBanner({ error }: { error: BackendError }) {
  const isQuota = error.detail.kind === "upstream_quota_exhausted";
  const isNetwork = error.detail.kind === "network_error";

  const styles = isQuota
    ? "border-amber-500/30 bg-amber-500/5 text-amber-700 dark:text-amber-300"
    : "border-red-500/30 bg-red-500/5 text-red-700 dark:text-red-300";
  const title = isQuota
    ? "Gemini quota exhausted"
    : isNetwork
      ? "Backend unreachable"
      : "Backend error";

  return (
    <div className={`rounded-lg border p-4 text-sm ${styles}`}>
      <div className="font-semibold">{title}</div>
      <div className="mt-1 text-foreground/80">{error.detail.message}</div>
      {error.status > 0 && (
        <div className="mt-2 text-xs text-foreground/50">
          HTTP {error.status} · kind={error.detail.kind}
        </div>
      )}
    </div>
  );
}

function ResponseView({
  response,
  evidenceLabel,
}: {
  response: QueryResponse;
  evidenceLabel?: string;
}) {
  const hasChunks = response.retrieved_chunks.length > 0;
  const hasToolCalls = response.tool_calls.length > 0;

  return (
    <div className="space-y-4">
      {/* Answer card */}
      <div className="rounded-lg border border-foreground/15 p-4">
        <div className="mb-2 flex items-center justify-between text-xs text-foreground/50">
          <span>Answer</span>
          <span className="font-mono tabular-nums">
            {fmtLatency(response.latency_ms)} · {response.model}
          </span>
        </div>
        <p className="whitespace-pre-wrap text-sm leading-relaxed text-foreground/90">
          {response.answer || "(empty answer)"}
        </p>
      </div>

      {/* Evidence: retrieved chunks (RAG / GraphRAG) */}
      {hasChunks && (
        <details className="rounded-lg border border-foreground/15" open>
          <summary className="cursor-pointer select-none px-4 py-3 text-sm font-medium">
            {evidenceLabel ?? `Retrieved chunks (${response.retrieved_chunks.length})`}
          </summary>
          <div className="space-y-3 border-t border-foreground/10 px-4 py-3 text-sm">
            {response.retrieved_chunks.map((chunk, i) => (
              <div key={i} className="space-y-1">
                <div className="font-mono text-xs text-foreground/60">
                  [{i + 1}] {chunk.source}
                </div>
                <p className="whitespace-pre-wrap text-xs leading-relaxed text-foreground/70">
                  {chunk.content_preview}
                  {chunk.content_preview.length >= 500 && "…"}
                </p>
              </div>
            ))}
          </div>
        </details>
      )}

      {/* Evidence: tool calls (Agentic) */}
      {hasToolCalls && (
        <details className="rounded-lg border border-foreground/15" open>
          <summary className="cursor-pointer select-none px-4 py-3 text-sm font-medium">
            Tool calls ({response.tool_calls.length})
          </summary>
          <ol className="space-y-3 border-t border-foreground/10 px-4 py-3 text-sm">
            {response.tool_calls.map((call, i) => (
              <li key={i} className="space-y-1">
                <div className="font-mono text-xs text-foreground/60">
                  [{i + 1}] {call.name}
                </div>
                <pre className="overflow-x-auto rounded bg-foreground/5 p-2 text-xs">
                  {JSON.stringify(call.args, null, 2)}
                </pre>
              </li>
            ))}
          </ol>
        </details>
      )}

      {/* Neither: degenerate but possible (e.g. GraphRAG before build done) */}
      {!hasChunks && !hasToolCalls && (
        <div className="rounded-lg border border-foreground/15 bg-foreground/5 p-4 text-xs text-foreground/50">
          No evidence surfaced by this paradigm on this question.
        </div>
      )}
    </div>
  );
}
