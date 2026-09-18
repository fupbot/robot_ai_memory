"""get_concept: fetch one concept document in full, plus the paths it links to and
the paths that link to it (its immediate graph neighborhood)."""
from __future__ import annotations

from pathlib import Path

from okf_robotics_core.bundle import Bundle
from okf_robotics_core.links import build_backlink_graph

from ..graph import forward_links


def get_concept(bundle: Bundle, path: str) -> dict:
    rel_path = Path(path)
    concept = bundle.read_concept(rel_path)
    backlinks = build_backlink_graph(bundle).get(rel_path, set())
    forward = forward_links(bundle, rel_path)

    return {
        "path": str(rel_path),
        "type": concept.type,
        "title": concept.title,
        "description": concept.description,
        "resource": concept.resource,
        "tags": concept.tags,
        "status": concept.status,
        "sources": concept.sources,
        "body": concept.body,
        "links_to": sorted(str(p) for p in forward),
        "linked_from": sorted(str(p) for p in backlinks),
    }
