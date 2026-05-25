"""LangGraph implementations for the three Q&A paradigms.

Each module exposes a compiled `graph` and a `build_graph()` factory.
Per the project plan, the three modules deliberately do not share a
common base class — repeated code is fine when each paradigm's flow
is genuinely different.
"""
