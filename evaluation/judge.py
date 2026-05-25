"""LLM-as-judge: score each candidate answer 0-3 against the source docs.

Reads `evaluation/results/<paradigm>_<dimension>.json`, scores every
candidate answer with `gemini-2.5-pro` (one notch above the Flash
generator, the standard LLM-as-judge guard against self-preference),
and writes an augmented report to
`evaluation/results/scored_<paradigm>_<dimension>.json`.

The judge has one tool — `read_doc_file` (reused from
`qa_lab.graphs.agentic_tools`) — so it can verify specific factual
claims against the real `.mdx` files rather than relying purely on
training knowledge.

Scoring is intentionally **blind**: the judge prompt never reveals
which paradigm produced an answer. The judge sees only the question,
the source hint, the sources the answering system reported (if any),
and the candidate answer itself.

Each judged result gains a `judge` field:

    {
        "score": 0-3,
        "reasoning": "1-2 sentence explanation",
        "verified_sources": ["src/oss/...mdx", ...],
        "elapsed_ms": <int>,
    }

Empty / sentinel answers are short-circuited to score 0 without
calling the judge model — they are unambiguous failures.

Usage (from the project root):

    cd backend
    uv run python ../evaluation/judge.py --paradigm rag --dimension single_hop
    uv run python ../evaluation/judge.py --all
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

from dotenv import find_dotenv, load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

from qa_lab.graphs.agentic_tools import read_doc_file

JUDGE_MODEL = "gemini-2.5-pro"
RESULTS_DIR = Path(__file__).resolve().parent / "results"

EMPTY_ANSWER_SENTINEL = "[agent ended without producing a final answer]"

PARADIGMS: tuple[str, ...] = ("rag", "agentic", "graphrag")
DIMENSIONS: tuple[str, ...] = ("single_hop", "multi_hop", "cross_doc")

JUDGE_SYSTEM = """\
You are a senior technical evaluator for a LangChain documentation
Q&A system. For each candidate answer to a question, score it on this
0-3 rubric:

- 3 = Fully correct. Accurate, complete, with appropriate source citations.
- 2 = Mostly correct. Core claim right, missing details or citations.
- 1 = Partially correct. Has errors or important omissions.
- 0 = Wrong, hallucinated, or empty.

Process for each question:
1. Read the question carefully.
2. Read the candidate answer.
3. If the candidate cites source paths or makes specific technical
   claims (class names, parameter defaults, version numbers, etc.),
   use the `read_doc_file` tool to verify against the actual docs.
   The expected source hint in the input tells you where to start.
4. Decide on a score 0-3.

Specific rules:
- If the answer is empty or the literal string "[agent ended without
  producing a final answer]", that is automatically 0 — but you will
  not see those (they are handled before reaching you).
- If the candidate says "context does not contain..." or similar,
  verify whether the answer is actually in the docs. If the answer is
  findable, the candidate failed to find it → score 1. If the answer
  is genuinely not in the corpus → score 2 (honest gap > fabrication).
- Be strict on factual claims. A number, version, class name, or
  parameter default that does not match the docs is wrong.
- Only list a path in `verified_sources` if you actually called
  read_doc_file on it. Do not list paths you only inferred.

Output format — your FINAL message MUST end with a JSON code block in
exactly this shape and nothing else after it:

```json
{
  "score": <0, 1, 2, or 3>,
  "reasoning": "<one or two short sentences explaining the score>",
  "verified_sources": ["<source path 1>", "<source path 2>"]
}
```
"""


# ---------------------------------------------------------------- helpers


JSON_BLOCK_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)
JSON_BARE_RE = re.compile(r"\{[^{}]*\"score\"[^{}]*\}", re.DOTALL)


def _build_judge():
    """Construct the judge agent (lazy — needs GOOGLE_API_KEY at call time)."""
    model = ChatGoogleGenerativeAI(model=JUDGE_MODEL, temperature=0.0)
    return create_react_agent(
        model=model,
        tools=[read_doc_file],
        prompt=JUDGE_SYSTEM,
    )


def _format_question_for_judge(result: dict) -> str:
    """Blind prompt: question + sources + answer. No paradigm reveal."""
    sources_list = "\n".join(f"- {s}" for s in result.get("retrieved_sources", []))
    if not sources_list:
        sources_list = "(none reported by the answering system)"

    return (
        f"Question (id={result['id']}, dimension={result['dimension']}):\n"
        f"{result['question_en']}\n\n"
        f"Expected source hint (what the answer SHOULD reference):\n"
        f"{result.get('source_hint', '(none)')}\n\n"
        f"Sources the answering system reported it retrieved:\n"
        f"{sources_list}\n\n"
        f"Candidate answer:\n{result['answer']}\n\n"
        f"Score this candidate using the rubric. Use read_doc_file to "
        f"verify specific claims against the actual documentation, then "
        f"emit the JSON block as specified."
    )


def _msg_text(msg: AIMessage) -> str:
    content = msg.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and "text" in block:
                parts.append(str(block["text"]))
            else:
                parts.append(str(block))
        return "".join(parts)
    return str(content)


def _parse_judge_output(messages: list[Any]) -> dict | None:
    """Pull the structured score block from the last AIMessage."""
    for msg in reversed(messages):
        if not isinstance(msg, AIMessage):
            continue
        text = _msg_text(msg)
        if not text:
            continue
        match = JSON_BLOCK_RE.search(text)
        if match is None:
            match = JSON_BARE_RE.search(text)
        if match:
            try:
                parsed = json.loads(match.group(1) if match.lastindex else match.group(0))
            except json.JSONDecodeError:
                continue
            if "score" in parsed:
                return parsed
    return None


def _short_circuit_score(result: dict) -> dict | None:
    """Auto-score obvious failures without spending a judge call."""
    answer = result.get("answer") or ""
    if not answer.strip() or answer == EMPTY_ANSWER_SENTINEL:
        return {
            "score": 0,
            "reasoning": "Empty answer or '[agent ended without producing a final answer]' sentinel — automatic 0.",
            "verified_sources": [],
            "elapsed_ms": 0,
            "short_circuited": True,
        }
    return None


# ---------------------------------------------------------------- core


def judge_one(judge_agent, result: dict) -> dict:
    """Run the judge on one result record. Returns the augmented record."""
    short = _short_circuit_score(result)
    if short is not None:
        return {**result, "judge": short}

    prompt = _format_question_for_judge(result)
    t0 = time.time()
    try:
        response = judge_agent.invoke({"messages": [HumanMessage(content=prompt)]})
    except Exception as exc:  # noqa: BLE001 — judge failure on one item shouldn't kill the run
        return {
            **result,
            "judge": {
                "score": None,
                "reasoning": f"Judge call raised: {exc}",
                "verified_sources": [],
                "elapsed_ms": int((time.time() - t0) * 1000),
            },
        }
    elapsed_ms = int((time.time() - t0) * 1000)
    parsed = _parse_judge_output(response.get("messages", []))

    if parsed is None:
        return {
            **result,
            "judge": {
                "score": None,
                "reasoning": "Could not parse judge JSON output.",
                "verified_sources": [],
                "elapsed_ms": elapsed_ms,
            },
        }

    return {
        **result,
        "judge": {
            "score": parsed.get("score"),
            "reasoning": parsed.get("reasoning", ""),
            "verified_sources": parsed.get("verified_sources", []),
            "elapsed_ms": elapsed_ms,
        },
    }


def judge_file(input_path: Path) -> Path:
    """Judge every result in input_path; write to scored_<input_path.name>."""
    print(f"\nLoading {input_path.name} ...")
    report = json.loads(input_path.read_text())
    results = report.get("results", [])

    print(f"Building judge ({JUDGE_MODEL}) ...")
    judge_agent = _build_judge()

    scored_results: list[dict] = []
    for i, result in enumerate(results, 1):
        if "error" in result:
            scored_results.append(
                {
                    **result,
                    "judge": {
                        "score": 0,
                        "reasoning": "Original run errored — score 0.",
                        "verified_sources": [],
                        "elapsed_ms": 0,
                    },
                }
            )
            continue

        print(f"  [{i}/{len(results)}] {result['id']} ...", end=" ", flush=True)
        scored = judge_one(judge_agent, result)
        score = scored["judge"]["score"]
        reasoning = (scored["judge"].get("reasoning") or "")[:90]
        print(f"score={score}  ({reasoning})")
        scored_results.append(scored)

    output_name = f"scored_{input_path.name}"
    output_path = input_path.parent / output_name

    scored_report = {
        **report,
        "scored_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "judge_model": JUDGE_MODEL,
        "results": scored_results,
    }

    output_path.write_text(json.dumps(scored_report, indent=2, ensure_ascii=False))
    print(f"  Wrote {output_path.name}")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paradigm", choices=list(PARADIGMS), default=None)
    parser.add_argument("--dimension", choices=list(DIMENSIONS), default=None)
    parser.add_argument(
        "--all",
        action="store_true",
        help="Judge every unscored results file under evaluation/results/.",
    )
    args = parser.parse_args()

    load_dotenv(find_dotenv(usecwd=True))

    if args.all:
        targets = sorted(
            p
            for p in RESULTS_DIR.glob("*.json")
            if not p.name.startswith("scored_")
        )
    elif args.paradigm and args.dimension:
        targets = [RESULTS_DIR / f"{args.paradigm}_{args.dimension}.json"]
    else:
        print(
            "ERROR: provide --paradigm AND --dimension, or --all.",
            file=sys.stderr,
        )
        return 1

    if not targets:
        print(f"No unscored reports found in {RESULTS_DIR}.")
        return 0

    for input_path in targets:
        if not input_path.exists():
            print(f"WARN: {input_path} not found, skipping.")
            continue
        judge_file(input_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
