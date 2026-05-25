"""Run a single paradigm against a filtered subset of the evaluation set.

Reads `evaluation/questions.json`, filters by `--dimension` (default:
`single_hop`), invokes the chosen paradigm graph on every matching
question, and writes a structured JSON report to
`evaluation/results/<paradigm>_<dimension>.json` for later human
scoring.

Each result records:

- The question metadata (id, dimension, question text, expected winner,
  source hint)
- The paradigm's answer
- The sources the retriever surfaced (deduplicated, order preserved)
- Latency in milliseconds
- The model id actually used (so the report stays meaningful even if
  `GEMINI_MODEL` is overridden)

Usage (from the project root):

    cd backend
    uv run python ../evaluation/run_one_paradigm.py
    uv run python ../evaluation/run_one_paradigm.py --paradigm rag --dimension multi_hop
    uv run python ../evaluation/run_one_paradigm.py --dimension all --limit 3

The Agentic and GraphRAG graphs are still stubs — running them produces
the placeholder response. Only `--paradigm rag` is fully wired.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

from qa_lab.llm import DEFAULT_GEMINI_MODEL

PROJECT_ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_FILE = PROJECT_ROOT / "evaluation" / "questions.json"
DEFAULT_RESULTS_DIR = PROJECT_ROOT / "evaluation" / "results"

PARADIGM_MODULES: dict[str, str] = {
    "rag": "qa_lab.graphs.rag_graph",
    "agentic": "qa_lab.graphs.agentic_graph",
    "graphrag": "qa_lab.graphs.graphrag_graph",
}

DIMENSIONS = ("single_hop", "multi_hop", "cross_doc", "all")


def _load_questions(dimension: str, limit: int | None) -> list[dict]:
    with QUESTIONS_FILE.open() as f:
        payload = json.load(f)
    questions: list[dict] = payload["questions"]
    if dimension != "all":
        questions = [q for q in questions if q.get("dimension") == dimension]
    if limit is not None:
        questions = questions[:limit]
    return questions


def _import_graph(paradigm: str):
    module_path = PARADIGM_MODULES[paradigm]
    module = importlib.import_module(module_path)
    if not hasattr(module, "graph"):
        raise RuntimeError(f"{module_path} does not expose a `graph` attribute")
    return module.graph


def _dedup_sources(chunks: list) -> list[str]:
    """Return unique source paths in insertion order."""
    sources: list[str] = []
    seen: set[str] = set()
    for chunk in chunks:
        src = chunk.metadata.get("source", "(unknown)")
        if src not in seen:
            seen.add(src)
            sources.append(src)
    return sources


def _run_one(graph, question: dict) -> dict:
    """Invoke the graph on one question and assemble its result record."""
    initial_state = {
        "question": question["question_en"],
        "retrieved_chunks": [],
        "tool_calls": [],
        "answer": "",
    }
    t0 = time.time()
    final_state = graph.invoke(initial_state)
    latency_ms = int((time.time() - t0) * 1000)

    chunks = final_state.get("retrieved_chunks", []) or []
    return {
        "id": question["id"],
        "dimension": question["dimension"],
        "question_zh": question.get("question_zh", ""),
        "question_en": question["question_en"],
        "expected_winner": question.get("expected_winner"),
        "source_hint": question.get("source_hint", ""),
        "is_demo_star": question.get("is_demo_star", False),
        "answer": final_state.get("answer", ""),
        "retrieved_sources": _dedup_sources(chunks),
        "retrieved_count": len(chunks),
        "tool_calls": final_state.get("tool_calls", []) or [],
        "latency_ms": latency_ms,
    }


def _print_question_header(idx: int, total: int, question: dict) -> None:
    print(f"\n[{idx}/{total}] {question['id']} ({question['dimension']})")
    print(f"  EN: {question['question_en']}")
    if question.get("question_zh"):
        print(f"  ZH: {question['question_zh']}")
    print(f"  Expected winner: {question.get('expected_winner', '(unspecified)')}")
    if question.get("source_hint"):
        print(f"  Source hint: {question['source_hint']}")


def _print_result(result: dict) -> None:
    print(f"  Latency: {result['latency_ms']} ms")
    sources = result["retrieved_sources"]
    if sources:
        top = sources[0]
        more = f" (+{len(sources) - 1} more)" if len(sources) > 1 else ""
        print(f"  Top source: {top}{more}")
    tool_calls = result.get("tool_calls") or []
    if tool_calls:
        names = [tc.get("name", "?") for tc in tool_calls]
        print(f"  Tool calls ({len(tool_calls)}): {', '.join(names)}")
    answer = result["answer"]
    # Trim long answers for terminal readability; full text is in the JSON.
    if len(answer) > 400:
        answer = answer[:400].rstrip() + " ..."
    print(f"  Answer: {answer}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--paradigm",
        choices=list(PARADIGM_MODULES),
        default="rag",
        help="Which paradigm graph to run (default: rag).",
    )
    parser.add_argument(
        "--dimension",
        choices=DIMENSIONS,
        default="single_hop",
        help="Filter questions by dimension. Use 'all' for the full set.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Cap on the number of questions to run.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_RESULTS_DIR),
        help=f"Where to write results (default: {DEFAULT_RESULTS_DIR}).",
    )
    args = parser.parse_args()

    load_dotenv(find_dotenv(usecwd=True))

    questions = _load_questions(args.dimension, args.limit)
    if not questions:
        print(
            f"ERROR: no questions match dimension={args.dimension}",
            file=sys.stderr,
        )
        return 1

    print(f"Loading paradigm '{args.paradigm}' ({PARADIGM_MODULES[args.paradigm]}) ...")
    graph = _import_graph(args.paradigm)
    model_id = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
    print(
        f"Running {args.paradigm} on {len(questions)} question(s) "
        f"(dimension={args.dimension}, model={model_id})"
    )

    results: list[dict] = []
    for i, question in enumerate(questions, 1):
        _print_question_header(i, len(questions), question)
        try:
            result = _run_one(graph, question)
        except Exception as exc:  # noqa: BLE001 — eval should not crash on one bad question
            print(f"  ERROR: {exc}")
            results.append(
                {
                    "id": question["id"],
                    "dimension": question["dimension"],
                    "question_en": question["question_en"],
                    "error": str(exc),
                }
            )
            continue
        _print_result(result)
        results.append(result)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{args.paradigm}_{args.dimension}.json"

    report = {
        "paradigm": args.paradigm,
        "dimension": args.dimension,
        "run_at": datetime.now(timezone.utc).isoformat(),
        "model": model_id,
        "embedding_model": "text-embedding-3-small",
        "n_questions": len(questions),
        "n_succeeded": sum(1 for r in results if "error" not in r),
        "n_failed": sum(1 for r in results if "error" in r),
        "results": results,
    }

    with output_file.open("w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\nWrote report to {output_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
