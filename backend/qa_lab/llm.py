"""Shared LLM clients used by all three paradigm graphs.

Centralising the model choice here keeps the comparison fair: every
paradigm uses the same generator (Gemini 2.5 Flash by default) and the
same embedding model, so observed differences reflect the paradigm
rather than the model.

Each paradigm can be bound to its own Google Cloud project (and therefore
its own daily quota) via paradigm-scoped environment variables:

    GOOGLE_API_KEY_RAG=...        # qa-lab-rag project key
    GOOGLE_API_KEY_AGENTIC=...    # qa-lab-agentic project key
    GOOGLE_API_KEY_GRAPHRAG=...   # qa-lab-graphrag project key
    GOOGLE_API_KEY=...            # fallback for anything not set above

Quotas on Gemini are per-project, not per-key — multiple keys inside
one project still share the same 10k/day cap on Tier 1. The three
paradigms therefore use keys from three *separate* projects so a
GraphRAG-heavy build day cannot starve the RAG or Agentic demos.

The model id can still be overridden globally via `GEMINI_MODEL`.
"""

from __future__ import annotations

import os

from langchain_google_genai import ChatGoogleGenerativeAI

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_TEMPERATURE = 0.0


def _resolve_paradigm_key(paradigm: str | None) -> str | None:
    """Return the Gemini API key for *paradigm*, falling back gracefully.

    Order of preference:
      1. `GOOGLE_API_KEY_<PARADIGM>` (e.g. `GOOGLE_API_KEY_RAG`)
      2. `GOOGLE_API_KEY` (project-wide fallback)

    Returns None only if neither is set — in which case
    `ChatGoogleGenerativeAI` will raise a helpful validation error.
    """
    if paradigm:
        scoped = os.getenv(f"GOOGLE_API_KEY_{paradigm.upper()}")
        if scoped:
            return scoped
    return os.getenv("GOOGLE_API_KEY")


def get_chat_model(
    *,
    paradigm: str | None = None,
    model: str | None = None,
    temperature: float = DEFAULT_TEMPERATURE,
) -> ChatGoogleGenerativeAI:
    """Return a Gemini chat model bound to the right project for *paradigm*.

    Args:
        paradigm: One of `"rag"`, `"agentic"`, `"graphrag"`. Selects the
            matching `GOOGLE_API_KEY_<PARADIGM>` env var so each paradigm
            consumes from its own GCP project quota. If None or if the
            scoped variable isn't set, falls back to `GOOGLE_API_KEY`.
        model: Override the model id; defaults to `GEMINI_MODEL` env var,
            then `DEFAULT_GEMINI_MODEL`.
        temperature: 0.0 by default for deterministic outputs.
    """
    return ChatGoogleGenerativeAI(
        model=model or os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL),
        temperature=temperature,
        google_api_key=_resolve_paradigm_key(paradigm),
    )
