"""graph_neighbors: bounded-depth traversal of the markdown-link graph starting from
a concept — e.g. "show me everything connected to this Task Attempt within 2 hops"."""
from __future__ import annotations

from pathlib import Path

from okf_robotics_core.bundle import Bundle

from ..graph import neighbors


def graph_neighbors(bundle: Bundle, path: str, *, depth: int = 1) -> dict:
    edges = neighbors(bundle, Path(path), depth=depth)
    return {str(p): sorted(str(t) for t in targets) for p, targets in edges.items()}
