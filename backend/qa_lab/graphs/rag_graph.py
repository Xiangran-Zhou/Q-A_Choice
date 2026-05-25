"""Traditional RAG paradigm graph (stub).

The full implementation will perform hybrid retrieval (Chroma vector
search + BM25) against an index of the LangChain documentation and
feed the top-k chunks to the generator model. This stub returns a
fixed placeholder so the graph wiring can be exercised end-to-end
before any real retrieval lands.
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
            "[rag_graph stub] Real retrieval not implemented yet. "
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
