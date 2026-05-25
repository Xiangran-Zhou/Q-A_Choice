"""Aggregate the per-run reports under `evaluation/results/` into a summary.

For each paradigm × dimension combination that has a report, prints:

- N questions in the dimension
- Mean latency (ms)
- Mean number of tool calls (only meaningful for paradigms with tools)
- Success rate (fraction of questions that returned a non-empty, non-sentinel answer)

Run after `run_one_paradigm.py` to refresh the numbers that feed
`decision_matrix.md`. The script reads only the JSON reports — it does
not call any LLM and is safe to run repeatedly.

Usage (from the project root):

    cd backend
    uv run python ../evaluation/compute_metrics.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import mean

RESULTS_DIR = Path(__file__).resolve().parent / "results"

PARADIGMS: tuple[str, ...] = ("rag", "agentic", "graphrag")
DIMENSIONS: tuple[str, ...] = ("single_hop", "multi_hop", "cross_doc")

EMPTY_ANSWER_SENTINEL = "[agent ended without producing a final answer]"


def _load_reports() -> dict[tuple[str, str], dict]:
    """Return `{(paradigm, dimension): report}` for every results file."""
    out: dict[tuple[str, str], dict] = {}
    if not RESULTS_DIR.exists():
        return out
    for path in sorted(RESULTS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        p = data.get("paradigm")
        d = data.get("dimension")
        if p in PARADIGMS and d in DIMENSIONS:
            out[(p, d)] = data
    return out


def _summarize(report: dict) -> dict:
    """Per-report stats: N, latency mean, tool-call mean, success rate."""
    results = [r for r in report.get("results", []) if "error" not in r]
    latencies = [r["latency_ms"] for r in results if "latency_ms" in r]
    tool_call_counts = [
        len(r.get("tool_calls", [])) for r in results if "tool_calls" in r
    ]
    n_total = len(results)
    n_succeeded = sum(
        1
        for r in results
        if r.get("answer") and r["answer"] != EMPTY_ANSWER_SENTINEL
    )
    has_tools = any(c > 0 for c in tool_call_counts) if tool_call_counts else False
    return {
        "n": n_total,
        "n_succeeded": n_succeeded,
        "latency_mean_ms": round(mean(latencies)) if latencies else None,
        "tool_calls_mean": (
            round(mean(tool_call_counts), 1) if has_tools else None
        ),
    }


def _fmt_cell(stats: dict | None) -> tuple[str, str, str, str]:
    """Render one (paradigm, dimension) cell into table-ready strings."""
    if stats is None:
        return ("–", "–", "–", "–")
    n = str(stats["n"])
    latency = (
        f"{stats['latency_mean_ms']:,} ms"
        if stats["latency_mean_ms"] is not None
        else "–"
    )
    tool_calls = (
        f"{stats['tool_calls_mean']:.1f}"
        if stats["tool_calls_mean"] is not None
        else "–"
    )
    success = f"{stats['n_succeeded']}/{stats['n']}"
    return (n, latency, tool_calls, success)


def main() -> int:
    reports = _load_reports()
    if not reports:
        print(
            f"No reports found in {RESULTS_DIR}. "
            f"Run evaluation/run_one_paradigm.py first.",
            file=sys.stderr,
        )
        return 1

    print(f"# Evaluation metrics\n\nSource: `{RESULTS_DIR.relative_to(Path.cwd().parent) if RESULTS_DIR.is_relative_to(Path.cwd().parent) else RESULTS_DIR}`\n")

    for paradigm in PARADIGMS:
        print(f"## {paradigm}\n")
        print("| Dimension   | N | Latency mean | Tool calls mean | Success rate |")
        print("|-------------|---|--------------|-----------------|--------------|")
        for dim in DIMENSIONS:
            report = reports.get((paradigm, dim))
            stats = _summarize(report) if report else None
            n, lat, tc, success = _fmt_cell(stats)
            print(f"| {dim:11s} | {n} | {lat} | {tc} | {success} |")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
