"""environment_history: every concept whose `resource` matches a given environment
URI — the demo's core query, "what happened last time in this environment". See
graph.py's module docstring for why this matches on `resource` equality rather than
markdown-link graph traversal."""
from __future__ import annotations

from okf_robotics_core.bundle import Bundle

from .. import graph


def environment_history(bundle: Bundle, environment_resource: str) -> list[str]:
    return [str(p) for p in graph.environment_history(bundle, environment_resource)]
