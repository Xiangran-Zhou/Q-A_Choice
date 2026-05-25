"""Agentic Search paradigm graph (stub).

The full implementation will be adapted from `chat-langchain`'s
`docs_graph`: a LangGraph agent with two document-search tools
(Mintlify API + filesystem) and multi-turn tool use. The Guardrails
middleware will be removed; Summarization and Retry middlewares will
be retained. This stub returns a fixed placeholder until the agent
loop is wired up.
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
            "[agentic_graph stub] Agent loop not implemented yet. "
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
