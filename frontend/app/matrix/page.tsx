import type { Metadata } from "next";

import {
  computeAggregates,
  DIMENSION_LABELS,
  DIMENSIONS,
  M3_STATUS,
  OPERATIONAL_METRICS,
  PARADIGM_LABELS,
  PARADIGMS,
  QUESTIONS,
  SCENARIO_RECOMMENDATIONS,
  type Dimension,
  type Paradigm,
} from "./data";

export const metadata: Metadata = {
  title: "Decision matrix · Q&A Paradigm Lab",
  description:
    "Side-by-side LLM-as-judge scores across RAG, Agentic, and GraphRAG paradigms on 15 evaluation questions.",
};

const SCORE_STYLES: Record<string, string> = {
  "3": "bg-green-500/15 text-green-700 dark:text-green-300 border-green-500/30",
  "2": "bg-amber-500/15 text-amber-700 dark:text-amber-300 border-amber-500/30",
  "1": "bg-orange-500/15 text-orange-700 dark:text-orange-300 border-orange-500/30",
  "0": "bg-red-500/15 text-red-700 dark:text-red-300 border-red-500/30",
  tbd: "bg-foreground/5 text-foreground/40 border-foreground/15",
};

function ScoreBadge({ score }: { score: number | null }) {
  if (score === null) {
    return (
      <span
        className={`inline-flex h-7 w-8 items-center justify-center rounded-md border text-xs font-medium ${SCORE_STYLES.tbd}`}
        title="Pending (M3 in progress)"
      >
        —
      </span>
    );
  }
  return (
    <span
      className={`inline-flex h-7 w-8 items-center justify-center rounded-md border text-sm font-semibold ${SCORE_STYLES[String(score)]}`}
    >
      {score}
    </span>
  );
}

function ExpectedTag({ expected }: { expected: "rag" | "agentic" | "graphrag" | "tie" }) {
  const label = expected === "tie" ? "tie" : PARADIGM_LABELS[expected];
  return (
    <span className="inline-block rounded-full border border-foreground/15 bg-foreground/5 px-2 py-0.5 text-[10px] uppercase tracking-wider text-foreground/60">
      expected: {label}
    </span>
  );
}

function PerDimensionTable({ dimension }: { dimension: Dimension }) {
  const rows = QUESTIONS.filter((q) => q.dimension === dimension);
  const subtotal = (paradigm: Paradigm) => {
    const scores = rows.map((r) => r.scores[paradigm]);
    if (scores.every((s) => s !== null)) {
      return scores.reduce((a, b) => (a as number) + (b as number), 0);
    }
    return null;
  };
  return (
    <div className="overflow-x-auto rounded-lg border border-foreground/15">
      <table className="w-full border-collapse text-sm">
        <thead className="bg-foreground/5 text-left">
          <tr>
            <th className="py-2 pl-4 pr-2 font-medium w-12">ID</th>
            <th className="py-2 px-2 font-medium">Question</th>
            {PARADIGMS.map((p) => (
              <th key={p} className="py-2 px-2 text-center font-medium w-20">
                {PARADIGM_LABELS[p]}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((q) => (
            <tr key={q.id} className="border-t border-foreground/10">
              <td className="py-3 pl-4 pr-2 tabular-nums font-mono text-foreground/60">{q.id}</td>
              <td className="py-3 px-2">
                <div className="flex flex-col gap-1">
                  <span>{q.title}</span>
                  <ExpectedTag expected={q.expected} />
                </div>
              </td>
              {PARADIGMS.map((p) => (
                <td key={p} className="py-3 px-2 text-center">
                  <ScoreBadge score={q.scores[p]} />
                </td>
              ))}
            </tr>
          ))}
          <tr className="border-t border-foreground/15 bg-foreground/5 font-medium">
            <td className="py-2 pl-4 pr-2" />
            <td className="py-2 px-2">Subtotal (out of 15)</td>
            {PARADIGMS.map((p) => {
              const s = subtotal(p);
              return (
                <td key={p} className="py-2 px-2 text-center tabular-nums">
                  {s === null ? <span className="text-foreground/40">—</span> : `${s}/15`}
                </td>
              );
            })}
          </tr>
        </tbody>
      </table>
    </div>
  );
}

function formatLatency(ms: number | null) {
  if (ms === null) return "—";
  if (ms < 1000) return `${ms} ms`;
  return `${(ms / 1000).toFixed(1)} s`;
}

function OperationalMetricsTable() {
  const metricByKey = new Map(
    OPERATIONAL_METRICS.map((m) => [`${m.paradigm}-${m.dimension}`, m]),
  );

  return (
    <div className="overflow-x-auto rounded-lg border border-foreground/15">
      <table className="w-full border-collapse text-sm">
        <thead className="bg-foreground/5 text-left">
          <tr>
            <th className="py-2 pl-4 pr-2 font-medium">Paradigm</th>
            <th className="py-2 px-2 font-medium">Metric</th>
            {DIMENSIONS.map((d) => (
              <th key={d} className="py-2 px-2 text-right font-medium">
                {DIMENSION_LABELS[d]}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {PARADIGMS.map((p) => {
            const showRows: Array<"latency" | "toolcalls" | "success"> = ["latency"];
            // Only show tool-call row if at least one metric for this paradigm has one.
            const hasTools = DIMENSIONS.some(
              (d) => metricByKey.get(`${p}-${d}`)?.toolCallsMean != null,
            );
            if (hasTools) showRows.push("toolcalls");
            showRows.push("success");

            const hasAnyData = DIMENSIONS.some((d) => metricByKey.has(`${p}-${d}`));
            if (!hasAnyData) {
              return (
                <tr key={p} className="border-t border-foreground/10">
                  <td className="py-3 pl-4 pr-2 font-semibold">{PARADIGM_LABELS[p]}</td>
                  <td className="py-3 px-2 text-foreground/50" colSpan={DIMENSIONS.length + 1}>
                    Pending — M3 build in progress
                  </td>
                </tr>
              );
            }

            return showRows.map((kind, idx) => (
              <tr key={`${p}-${kind}`} className="border-t border-foreground/10">
                <td className="py-2.5 pl-4 pr-2 align-top font-semibold">
                  {idx === 0 ? PARADIGM_LABELS[p] : ""}
                </td>
                <td className="py-2.5 px-2 text-foreground/60">
                  {kind === "latency" && "Latency (mean)"}
                  {kind === "toolcalls" && "Tool calls (mean)"}
                  {kind === "success" && "Success rate"}
                </td>
                {DIMENSIONS.map((d) => {
                  const m = metricByKey.get(`${p}-${d}`);
                  if (!m) {
                    return (
                      <td key={d} className="py-2.5 px-2 text-right text-foreground/40">
                        —
                      </td>
                    );
                  }
                  if (kind === "latency") {
                    return (
                      <td key={d} className="py-2.5 px-2 text-right tabular-nums">
                        {formatLatency(m.latencyMs)}
                        {m.latencyNote && (
                          <span
                            className="ml-1 cursor-help text-amber-500"
                            title={m.latencyNote}
                          >
                            ⚠
                          </span>
                        )}
                      </td>
                    );
                  }
                  if (kind === "toolcalls") {
                    return (
                      <td key={d} className="py-2.5 px-2 text-right tabular-nums">
                        {m.toolCallsMean != null ? m.toolCallsMean.toFixed(1) : "—"}
                      </td>
                    );
                  }
                  return (
                    <td key={d} className="py-2.5 px-2 text-right tabular-nums">
                      {m.successRate}
                    </td>
                  );
                })}
              </tr>
            ));
          })}
        </tbody>
      </table>
    </div>
  );
}

function AggregateTable() {
  const rows = computeAggregates();
  return (
    <div className="overflow-x-auto rounded-lg border border-foreground/15">
      <table className="w-full border-collapse text-sm">
        <thead className="bg-foreground/5 text-left">
          <tr>
            <th className="py-2 pl-4 pr-2 font-medium">Paradigm</th>
            {DIMENSIONS.map((d) => (
              <th key={d} className="py-2 px-2 text-right font-medium">
                {DIMENSION_LABELS[d]}
              </th>
            ))}
            <th className="py-2 pl-2 pr-4 text-right font-medium">Overall</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const scoredDims = DIMENSIONS.filter((d) => row[d] !== null);
            const total = scoredDims.reduce((s, d) => s + (row[d] as number), 0);
            const maxPossible = scoredDims.length * 15;
            const pct = maxPossible > 0 ? Math.round((total / maxPossible) * 100) : null;
            return (
              <tr key={row.paradigm} className="border-t border-foreground/10">
                <td className="py-3 pl-4 pr-2 font-semibold">{PARADIGM_LABELS[row.paradigm]}</td>
                {DIMENSIONS.map((d) => (
                  <td key={d} className="py-3 px-2 text-right tabular-nums">
                    {row[d] !== null ? (
                      `${row[d]}/15`
                    ) : (
                      <span className="text-foreground/40">TBD</span>
                    )}
                  </td>
                ))}
                <td className="py-3 pl-2 pr-4 text-right tabular-nums font-semibold">
                  {pct !== null ? (
                    <>
                      {total}/{maxPossible}
                      <span className="ml-1 text-foreground/60 font-normal">({pct}%)</span>
                    </>
                  ) : (
                    <span className="text-foreground/40">TBD</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function ScoreLegend() {
  return (
    <div className="flex flex-wrap items-center gap-3 text-xs text-foreground/60">
      <span>Score legend:</span>
      {[
        { score: 3, label: "Fully correct" },
        { score: 2, label: "Mostly correct" },
        { score: 1, label: "Partially correct" },
        { score: 0, label: "Wrong / empty" },
      ].map(({ score, label }) => (
        <span key={score} className="inline-flex items-center gap-1.5">
          <ScoreBadge score={score} />
          <span>{label}</span>
        </span>
      ))}
      <span className="inline-flex items-center gap-1.5">
        <ScoreBadge score={null} />
        <span>Pending</span>
      </span>
    </div>
  );
}

export default function Page() {
  const m3Pct = Math.round((M3_STATUS.processed / M3_STATUS.total) * 100);

  return (
    <div className="space-y-10">
      {/* Header */}
      <section className="space-y-3">
        <h2 className="text-3xl font-semibold tracking-tight">Decision matrix</h2>
        <p className="max-w-3xl leading-relaxed text-foreground/70">
          15 evaluation questions × 3 paradigms × 0–3 LLM-as-judge scoring.
          Judge is <strong>Gemini 2.5 Pro</strong> (one notch above the generator)
          with <code className="rounded bg-foreground/5 px-1.5 py-0.5 text-xs">read_doc_file</code>{" "}
          tool access for source verification. Scoring is blind — the judge prompt
          never reveals which paradigm produced an answer.
        </p>
      </section>

      {/* M3 status banner */}
      <section className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-4 text-sm">
        <div className="flex items-baseline gap-3">
          <strong className="text-amber-700 dark:text-amber-300">M3 in progress</strong>
          <span className="text-foreground/70">
            GraphRAG knowledge-graph build at{" "}
            <span className="tabular-nums font-medium">
              {M3_STATUS.processed.toLocaleString()} / {M3_STATUS.total.toLocaleString()}
            </span>{" "}
            docs ({m3Pct}%).
          </span>
        </div>
        <p className="mt-2 text-foreground/60 leading-relaxed">
          Paused at {M3_STATUS.reasonForPause}. {M3_STATUS.resumeAction} GraphRAG
          column will populate once the build finishes. See the project{" "}
          <a href="https://github.com/Xiangran-Zhou/Q-A_Choice" className="underline">
            README
          </a>{" "}
          for full context on the quota-cap finding.
        </p>
      </section>

      {/* Aggregate scores */}
      <section className="space-y-3">
        <h3 className="text-xl font-semibold">Aggregate scores</h3>
        <p className="text-sm text-foreground/60">
          Total score per paradigm per dimension. Higher is better. Each dimension
          maxes out at 15 (5 questions × score of 3).
        </p>
        <AggregateTable />
        <p className="text-xs text-foreground/50">
          Standout signal: <strong>Agentic 15/15 on cross-doc</strong> — the
          ReAct loop's multi-search pattern reliably synthesises across pages
          where RAG's single retrieval misses framing.
        </p>
      </section>

      {/* Per-question breakdown */}
      <section className="space-y-6">
        <div>
          <h3 className="text-xl font-semibold">Per-question scores</h3>
          <p className="mt-1 text-sm text-foreground/60">
            One paradigm per column. The <em>expected</em> tag is the pre-experiment
            guess, included for honesty — many predictions did not match the judged
            outcome.
          </p>
        </div>
        <ScoreLegend />
        {DIMENSIONS.map((dim) => (
          <div key={dim} className="space-y-2">
            <h4 className="text-lg font-medium">{DIMENSION_LABELS[dim]}</h4>
            <PerDimensionTable dimension={dim} />
          </div>
        ))}
      </section>

      {/* Operational metrics */}
      <section className="space-y-3">
        <h3 className="text-xl font-semibold">Operational metrics</h3>
        <p className="text-sm text-foreground/60">
          Per-question averages from the un-scored evaluation runs. Hover ⚠ for
          per-row notes on outliers.
        </p>
        <OperationalMetricsTable />
      </section>

      {/* Scenario recommendations */}
      <section className="space-y-3">
        <h3 className="text-xl font-semibold">Scenario recommendations</h3>
        <p className="text-sm text-foreground/60">
          Selection guidance derived from the scores above, not from
          pre-experiment intuition — see how Scenario A flipped from
          &ldquo;obvious win for RAG&rdquo; to &ldquo;tied on quality, RAG wins on
          latency.&rdquo;
        </p>
        <div className="grid gap-4 md:grid-cols-2">
          {SCENARIO_RECOMMENDATIONS.map((rec) => (
            <div
              key={rec.scenario}
              className="rounded-lg border border-foreground/15 p-4"
            >
              <div className="flex items-baseline gap-2">
                <span className="text-xl" aria-hidden>
                  {rec.emoji}
                </span>
                <div className="flex-1">
                  <div className="text-sm font-medium">{rec.scenario}</div>
                  <div className="mt-0.5 text-sm font-semibold text-foreground">
                    → {rec.recommendation}
                  </div>
                </div>
              </div>
              <p className="mt-2 text-sm leading-relaxed text-foreground/70">
                {rec.rationale}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Methodology footer */}
      <section className="border-t border-foreground/10 pt-6 text-xs leading-relaxed text-foreground/50">
        <p>
          <strong className="text-foreground/70">Methodology:</strong> Generator
          is Gemini 2.5 Flash (upgraded from Flash Lite — see project README for
          rationale). Embeddings are OpenAI text-embedding-3-small. Judge is
          Gemini 2.5 Pro with read-only file access to{" "}
          <code className="rounded bg-foreground/5 px-1 py-0.5">raw_docs/</code>.
          Per-question judge reasoning is in{" "}
          <code className="rounded bg-foreground/5 px-1 py-0.5">
            evaluation/results/scored_*.json
          </code>{" "}
          in the repo.
        </p>
      </section>
    </div>
  );
}
