"use client";

import { useState } from "react";

import {
  BackendError,
  queryParadigm,
  type Paradigm,
  type QueryResponse,
} from "@/lib/api";

type ColumnStatus = "idle" | "loading" | "done" | "error";

interface ColumnState {
  paradigm: Paradigm;
  status: ColumnStatus;
  response?: QueryResponse;
  error?: BackendError;
}

const SAMPLE_QUESTIONS = [
  "I want to build a LangGraph agent that automatically retries 3 times when tool calls fail. What components do I need?",
  "What is the default value of the temperature parameter in ChatOpenAI?",
  "Document Loaders and Retrievers in LangChain — what does each do and how do they work together?",
];

function toBackendError(err: unknown): BackendError {
  if (err instanceof BackendError) return err;
  return new BackendError(
    { kind: "unknown_error", message: String(err) },
    0,
  );
}

function fmtLatency(ms: number) {
  if (ms < 1000) return `${ms} ms`;
  return `${(ms / 1000).toFixed(1)} s`;
}

export default function CompareGrid() {
  const [question, setQuestion] = useState("");
  const [submitted, setSubmitted] = useState<string | null>(null);
  const [rag, setRag] = useState<ColumnState>({ paradigm: "rag", status: "idle" });
  const [agentic, setAgentic] = useState<ColumnState>({
    paradigm: "agentic",
    status: "idle",
  });

  async function handleSubmit(e?: React.FormEvent) {
    e?.preventDefault();
    const q = question.trim();
    if (!q) return;
    if (rag.status === "loading" || agentic.status === "loading") return;

    setSubmitted(q);
    setRag({ paradigm: "rag", status: "loading" });
    setAgentic({ paradigm: "agentic", status: "loading" });

    // Fire both in parallel — that's the whole point of this page.
    queryParadigm("rag", q)
      .then((r) =>
        setRag({ paradigm: "rag", status: "done", response: r }),
      )
      .catch((err) =>
        setRag({
          paradigm: "rag",
          status: "error",
          error: toBackendError(err),
        }),
      );

    queryParadigm("agentic", q)
      .then((r) =>
        setAgentic({
          paradigm: "agentic",
          status: "done",
          response: r,
        }),
      )
      .catch((err) =>
        setAgentic({
          paradigm: "agentic",
          status: "error",
          error: toBackendError(err),
        }),
      );
  }

  const isLoading = rag.status === "loading" || agentic.status === "loading";

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="space-y-3">
        <label className="block">
          <span className="mb-1.5 block text-sm font-medium text-foreground/80">
            Ask the same question to all three paradigms
          </span>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={isLoading}
            rows={2}
            placeholder="e.g. How does LangGraph's interrupt function work?"
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
            {isLoading ? "Asking all paradigms…" : "Ask all"}
          </button>
          <span className="text-xs text-foreground/40">⌘ + Enter to submit</span>
        </div>
        <div className="flex flex-wrap gap-2 pt-1">
          <span className="text-xs text-foreground/50 mr-1 self-center">try:</span>
          {SAMPLE_QUESTIONS.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setQuestion(s)}
              disabled={isLoading}
              className="rounded-full border border-foreground/15 px-3 py-1 text-xs text-foreground/70 transition-colors hover:bg-foreground/5 disabled:opacity-40"
            >
              {s.length > 65 ? s.slice(0, 62) + "…" : s}
            </button>
          ))}
        </div>
      </form>

      {submitted && (
        <div className="rounded-md border border-foreground/15 bg-foreground/5 px-3 py-2 text-xs text-foreground/60">
          Asking: <span className="text-foreground/80">{submitted}</span>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <ParadigmColumn title="Traditional RAG" tagline="Hybrid retrieval + single shot" state={rag} />
        <ParadigmColumn title="Agentic Search" tagline="ReAct loop + two tools" state={agentic} />
        <ParadigmColumn
          title="GraphRAG"
          tagline="Knowledge graph + multi-hop"
          state={{ paradigm: "graphrag", status: "idle" }}
          pendingNote="Knowledge-graph build still running for M3. This column will join the comparison once the LightRAG store is complete."
        />
      </div>
    </div>
  );
}

interface ColumnProps {
  title: string;
  tagline: string;
  state: ColumnState;
  pendingNote?: string;
}

function ParadigmColumn({ title, tagline, state, pendingNote }: ColumnProps) {
  const isPending = pendingNote && state.status === "idle";

  return (
    <div className="flex h-full min-h-[340px] flex-col rounded-lg border border-foreground/15">
      {/* Header */}
      <div className="border-b border-foreground/10 px-4 py-3">
        <div className="flex items-center justify-between gap-2">
          <div className="font-semibold">{title}</div>
          <StatusPill state={state} />
        </div>
        <div className="mt-0.5 text-xs text-foreground/55">{tagline}</div>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto px-4 py-3 text-sm">
        {isPending ? (
          <p className="text-xs leading-relaxed text-foreground/55">
            {pendingNote}
          </p>
        ) : state.status === "idle" ? (
          <p className="text-xs text-foreground/40">Waiting for a question.</p>
        ) : state.status === "loading" ? (
          <LoadingDots />
        ) : state.status === "error" && state.error ? (
          <ColumnError error={state.error} />
        ) : state.status === "done" && state.response ? (
          <ColumnAnswer response={state.response} />
        ) : null}
      </div>
    </div>
  );
}

function StatusPill({ state }: { state: ColumnState }) {
  if (state.status === "loading") {
    return (
      <span className="rounded-full bg-foreground/10 px-2 py-0.5 text-[10px] uppercase tracking-wider text-foreground/60">
        running
      </span>
    );
  }
  if (state.status === "error") {
    const isQuota = state.error?.detail.kind === "upstream_quota_exhausted";
    return (
      <span
        className={`rounded-full px-2 py-0.5 text-[10px] uppercase tracking-wider ${
          isQuota
            ? "bg-amber-500/15 text-amber-700 dark:text-amber-300"
            : "bg-red-500/15 text-red-700 dark:text-red-300"
        }`}
      >
        {isQuota ? "quota" : "error"}
      </span>
    );
  }
  if (state.status === "done" && state.response) {
    return (
      <span className="rounded-full bg-foreground/10 px-2 py-0.5 text-[10px] font-mono tabular-nums uppercase tracking-wider text-foreground/60">
        {fmtLatency(state.response.latency_ms)}
      </span>
    );
  }
  return (
    <span className="rounded-full bg-foreground/5 px-2 py-0.5 text-[10px] uppercase tracking-wider text-foreground/40">
      idle
    </span>
  );
}

function LoadingDots() {
  return (
    <div className="flex items-center gap-1 text-xs text-foreground/55">
      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-foreground/40" />
      <span
        className="h-1.5 w-1.5 animate-bounce rounded-full bg-foreground/40"
        style={{ animationDelay: "0.15s" }}
      />
      <span
        className="h-1.5 w-1.5 animate-bounce rounded-full bg-foreground/40"
        style={{ animationDelay: "0.3s" }}
      />
    </div>
  );
}

function ColumnError({ error }: { error: BackendError }) {
  const isQuota = error.detail.kind === "upstream_quota_exhausted";
  return (
    <div className={`rounded border p-2 text-xs leading-relaxed ${
      isQuota
        ? "border-amber-500/30 bg-amber-500/5 text-amber-700 dark:text-amber-300"
        : "border-red-500/30 bg-red-500/5 text-red-700 dark:text-red-300"
    }`}>
      <div className="font-semibold">
        {isQuota ? "Gemini quota exhausted" : "Backend error"}
      </div>
      <div className="mt-1 text-foreground/70">{error.detail.message}</div>
    </div>
  );
}

function ColumnAnswer({ response }: { response: QueryResponse }) {
  const hasChunks = response.retrieved_chunks.length > 0;
  const hasToolCalls = response.tool_calls.length > 0;

  return (
    <div className="space-y-3">
      <p className="whitespace-pre-wrap text-xs leading-relaxed">
        {response.answer || "(empty answer)"}
      </p>

      {hasToolCalls && (
        <details>
          <summary className="cursor-pointer select-none text-[11px] font-medium text-foreground/60">
            Tool calls ({response.tool_calls.length})
          </summary>
          <ol className="mt-2 space-y-1.5 text-[11px] text-foreground/70">
            {response.tool_calls.map((tc, i) => (
              <li key={i} className="font-mono">
                [{i + 1}] {tc.name}
              </li>
            ))}
          </ol>
        </details>
      )}

      {hasChunks && (
        <details>
          <summary className="cursor-pointer select-none text-[11px] font-medium text-foreground/60">
            Retrieved sources ({response.retrieved_chunks.length})
          </summary>
          <ul className="mt-2 space-y-1 text-[11px] text-foreground/60">
            {response.retrieved_chunks.map((c, i) => (
              <li key={i} className="font-mono">
                [{i + 1}] {c.source}
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}
