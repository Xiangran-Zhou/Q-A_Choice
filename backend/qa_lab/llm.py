"""Shared LLM clients used by all three paradigm graphs.

Centralizing the model choice here keeps the comparison fair: every
paradigm uses the same generator (Gemini Flash Lite) and the same
embedding model, so observed differences reflect the paradigm rather
than the model.

The model id can be overridden via the `GEMINI_MODEL` environment
variable in case Google ships a new version and the default falls
out of date.
"""

from __future__ import annotations

import os

from langchain_google_genai import ChatGoogleGenerativeAI

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash-lite"
DEFAULT_TEMPERATURE = 0.0


def get_chat_model(
    *,
    model: str | None = None,
    temperature: float = DEFAULT_TEMPERATURE,
) -> ChatGoogleGenerativeAI:
    """Return a configured Gemini chat model.

    Reads `GEMINI_MODEL` from the environment if `model` is not given,
    falling back to `DEFAULT_GEMINI_MODEL`.
    """
    return ChatGoogleGenerativeAI(
        model=model or os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL),
        temperature=temperature,
    )
