"""search_bundle: full-text search over the OKF bundle, optionally filtered by
concept type/tags. Thin wrapper around okf_robotics_core's GrepSearchBackend — no
ranking or reasoning here, that's left to the calling LLM."""
from __future__ import annotations

from okf_robotics_core.bundle import Bundle
from okf_robotics_core.search.grep_backend import GrepSearchBackend


def search_bundle(
    bundle: Bundle,
    query: str,
    *,
    type_filter: str | None = None,
    tags: list[str] | None = None,
) -> list[dict]:
    backend = GrepSearchBackend(bundle)
    results = backend.search(query, type_filter=type_filter, tags=tags)
    return [
        {"path": str(r.path), "line": r.line_number, "snippet": r.snippet}
        for r in results
    ]
