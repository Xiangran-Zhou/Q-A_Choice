"""GraphRAG paradigm graph (stub).

The full implementation will extract a knowledge graph from the
LangChain documentation (LightRAG as the primary choice, per the
project plan's 2-day timebox), traverse 1-3 hops from the entities
in each question, and feed the resulting subgraph to the generator
model. This stub returns a fixed placeholder until the graph build
and traversal land.
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    question: str
    answer: str


def _placeholder_node(state: State) -> State:
    return {
        "question": state["question"],
        "answer": (
            "[graphrag_graph stub] Graph traversal not implemented yet. "
            f"You asked: {state['question']!r}"
        ),
    }


def build_graph():
    builder = StateGraph(State)
    builder.add_node("placeholder", _placeholder_node)
    builder.add_edge(START, "placeholder")
    builder.add_edge("placeholder", END)
    return builder.compile()


graph = build_graph()


if __name__ == "__main__":
    result = graph.invoke({"question": "What is LangChain?", "answer": ""})
    print(result["answer"])
