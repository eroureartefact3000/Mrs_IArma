"""Build the search document for a board.

The search document is the text we embed for similarity search. We optimise it
for retrieving *conceptually similar mechanics*, not similar brands.

Composition (decided with the user, 2026-05-29):
    one_liner
    Mechanisms: ...
    Idea: ...
    Insight: ...

We deliberately omit campaign / brand / metrics / press / agency — those are
board-specific noise that would degrade retrieval quality.
"""
from typing import Any


def build_search_document(record: dict[str, Any]) -> str:
    """Return the searchable text for a board record.

    Falls back from `extracted.<field>` to `inferred.<field>` for fields that can
    legitimately live in either pass (idea, insight).
    """
    extracted = record.get("extracted") or {}
    inferred = record.get("inferred") or {}

    one_liner = (inferred.get("one_liner") or "").strip()
    mechanisms = inferred.get("creative_mechanisms") or []
    idea = (extracted.get("idea") or inferred.get("idea") or "").strip()
    insight = (extracted.get("insight") or inferred.get("insight") or "").strip()

    parts: list[str] = []
    if one_liner:
        parts.append(one_liner)
    if mechanisms:
        parts.append("Mechanisms: " + ", ".join(mechanisms))
    if idea:
        parts.append(f"Idea: {idea}")
    if insight:
        parts.append(f"Insight: {insight}")

    return "\n".join(parts)
