"""Vector-search API for the RAG.

One numpy index per category (e.g. `data/outdoor_index.npy` for Outdoor).
Indexes are lazy-loaded the first time they're queried, cached after that.

Usage:
    from pipeline.search import search
    hits = search("ambient billboard that becomes a product", category="Outdoor", k=5)
    for h in hits:
        print(h["score"], h["campaign"], h["one_liner"])

Voyage embeddings are unit-normalised, so cosine similarity reduces to a dot
product, which numpy matrix-multiplies in a few ms even for thousands of vectors.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from .category_registry import require_enabled_category
from .embeddings import embed_query


class IndexNotBuilt(RuntimeError):
    """Raised when a category's index files are missing on disk."""


# Backwards-compat constants — kept so older callers (CLI smoke scripts, the
# api `/api/health` endpoint) keep working. They point to the default (Outdoor)
# category's files.
def _default_index_paths() -> tuple[Path, Path]:
    cfg = require_enabled_category("Outdoor")
    assert cfg.index_path is not None and cfg.meta_path is not None
    return cfg.index_path, cfg.meta_path


DEFAULT_EMBEDDINGS, DEFAULT_META = _default_index_paths()


# ---------------------------------------------------------------------------
# Per-category lazy index
# ---------------------------------------------------------------------------


class _Index:
    """Lazy-loaded vector index for one category."""

    def __init__(self, embeddings_path: Path, meta_path: Path) -> None:
        self._embeddings_path = embeddings_path
        self._meta_path = meta_path
        self._matrix: np.ndarray | None = None
        self._meta: list[dict[str, Any]] | None = None

    def _ensure_loaded(self) -> None:
        if self._matrix is not None and self._meta is not None:
            return
        if not self._embeddings_path.exists() or not self._meta_path.exists():
            raise IndexNotBuilt(
                f"Missing index files for this category."
                f"\n  Expected: {self._embeddings_path}\n  Expected: {self._meta_path}"
            )
        self._matrix = np.load(self._embeddings_path)
        meta: list[dict[str, Any]] = []
        with self._meta_path.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                meta.append(json.loads(line))
        self._meta = meta

    def search(
        self,
        query_text: str,
        k: int = 5,
        tier_filter: set[str] | None = None,
        exclude_ids: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        self._ensure_loaded()
        assert self._matrix is not None and self._meta is not None

        query_vec = np.asarray(embed_query(query_text), dtype=np.float32)
        sims = self._matrix @ query_vec  # unit-normalised → cosine = dot product

        candidate_indices = np.arange(len(self._meta))
        if tier_filter is not None:
            mask = np.array([m["tier"] in tier_filter for m in self._meta])
            candidate_indices = candidate_indices[mask]
        if exclude_ids is not None and exclude_ids:
            mask = np.array([m["id"] not in exclude_ids for m in self._meta])
            candidate_indices = np.intersect1d(candidate_indices, np.arange(len(self._meta))[mask])

        if len(candidate_indices) == 0:
            return []

        candidate_sims = sims[candidate_indices]
        top_local = np.argsort(-candidate_sims)[:k]
        top_global = candidate_indices[top_local]

        return [
            {
                "score": float(sims[i]),
                "row": int(i),
                **self._meta[i],
            }
            for i in top_global
        ]


# ---------------------------------------------------------------------------
# Registry-driven cache: one _Index per category key
# ---------------------------------------------------------------------------

_INDEX_CACHE: dict[str, _Index] = {}


def _get_index(category: str) -> _Index:
    """Return the lazy index for `category`, building it on first access."""
    if category not in _INDEX_CACHE:
        cfg = require_enabled_category(category)
        assert cfg.index_path is not None and cfg.meta_path is not None
        _INDEX_CACHE[category] = _Index(cfg.index_path, cfg.meta_path)
    return _INDEX_CACHE[category]


# ---------------------------------------------------------------------------
# Public search API
# ---------------------------------------------------------------------------


def search(
    query_text: str,
    *,
    category: str = "Outdoor",
    k: int = 5,
    tier_filter: set[str] | None = None,
    exclude_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Run a similarity search against a category's RAG index.

    Args:
        query_text: any natural-language query — board summary, idea description, etc.
        category: which category's index to search against (default: "Outdoor")
        k: number of results to return
        tier_filter: if given, only return boards whose tier is in this set
                     (e.g. {"Grand Prix", "Gold", "Silver", "Bronze"})
        exclude_ids: ids to exclude (useful when ranking a board already in the index)

    Returns:
        A list of dicts (one per hit) ordered by similarity descending. Each
        dict has score, row, id, tier, category, campaign, brand, one_liner,
        weighted_score, search_doc, full_record.

    Raises:
        UnknownCategory / CategoryNotEnabled if the category isn't ready.
        IndexNotBuilt if the on-disk index files are missing.
    """
    return _get_index(category).search(
        query_text, k=k, tier_filter=tier_filter, exclude_ids=exclude_ids
    )
