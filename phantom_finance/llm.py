"""Offline-safe LLM categorization adapter."""

from __future__ import annotations

import os
from typing import Callable, Iterable, Optional

from . import categorize

RouterFn = Callable[[str], str]

PROMPT = (
    "Reply with EXACTLY ONE category from this list (or the literal word none): "
    "{categories}. Transaction: {description}."
)


def known_categories() -> set[str]:
    return set(categorize.DEFAULT_RULES.values()) | {"income", "transfer"}


def default_router() -> Optional[RouterFn]:
    """Locate the phantom-mesh model router if importable; offline-safe.
    Returns None when disabled or unavailable so categorization stays pure-rules.
    """
    if os.environ.get("PHANTOM_FINANCE_LLM", "").strip().lower() in {
        "off",
        "0",
        "false",
        "none",
        "",
    }:
        return None
    try:
        from phantom_mesh import router as mesh_router  # type: ignore
    except Exception:
        return None
    complete = getattr(mesh_router, "complete", None)
    return complete if callable(complete) else None


def make_categorizer(
    router: Optional[RouterFn] = None,
    categories: Optional[Iterable[str]] = None,
) -> categorize.LlmCategorizer:
    resolved = router if router is not None else default_router()
    allowed = set(categories) if categories is not None else known_categories()

    def _llm(description: str) -> Optional[str]:
        if resolved is None:
            return None
        try:
            answer = resolved(
                PROMPT.format(
                    categories=", ".join(sorted(allowed)),
                    description=description,
                )
            )
        except Exception:
            return None
        if not answer:
            return None
        guess = answer.strip().lower().splitlines()[0].strip() if answer.strip() else ""
        return guess if guess in allowed else None

    return _llm
