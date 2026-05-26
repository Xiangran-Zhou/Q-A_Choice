import type { Metadata } from "next";

import CompareGrid from "../_components/CompareGrid";

export const metadata: Metadata = {
  title: "Side-by-side · Q&A Paradigm Lab",
  description:
    "One question, three paradigms answering in parallel. The page that makes the trade-offs visible.",
};

export default function Page() {
  return (
    <div className="space-y-6">
      <section className="space-y-2">
        <h2 className="text-2xl font-semibold tracking-tight">
          Side-by-side comparison
        </h2>
        <p className="max-w-3xl text-sm leading-relaxed text-foreground/70">
          One input fires all three paradigms in parallel. Watch the latency
          pills race, scan the three answers, and click into each column for
          tool calls or retrieved sources. The page where the trade-offs stop
          being abstract — see how a single multi-hop question gets handled
          very differently by each paradigm.
        </p>
      </section>

      <CompareGrid />
    </div>
  );
}
