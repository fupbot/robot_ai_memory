"""Concept graph traversal and resource-matching over an okf_robotics_core.Bundle —
the query logic behind the MCP tools. No `mcp` SDK dependency, so this is testable
without it installed. No LLM reasoning here either: this module returns structured
data, the calling planner's LLM reasons over it — see requirements.md's Encoding
approach section.

Two different "find related concepts" strategies live here, deliberately:

- `neighbors()` walks markdown *links* in concept bodies (e.g. a Replan Event links to
  the Task Attempt it happened during — see okf_robotics_capture's replan_encoder.py).
- `environment_history()` matches on the `resource` *frontmatter field* instead,
  because that's how okf_robotics_capture actually associates a Task Attempt/Mission
  Run with an environment (a shared `resource` URI, not a markdown link to the
  Environment Observation concept) — see requirements.md's Schema design notes.
"""
from __future__ import annotations

from pathlib import Path

from okf_robotics_core import frontmatter
from okf_robotics_core.bundle import Bundle
from okf_robotics_core.links import build_backlink_graph, extract_links, resolve_link


def forward_links(bundle: Bundle, rel_path: Path) -> list[Path]:
    """The bundle-relative paths `rel_path`'s body links to."""
    text = (bundle.root / rel_path).read_text(encoding="utf-8")
    _, body = frontmatter.parse(text)
    return [
        target
        for link in extract_links(body)
        if (target := resolve_link(rel_path, link)) is not None
    ]


def neighbors(bundle: Bundle, rel_path: Path, *, depth: int = 1) -> dict[Path, set[Path]]:
    """Bounded-depth BFS over both forward links and backlinks from `rel_path`.

    Returns {path: set(paths one hop away from it)} for every path visited within
    `depth` hops of `rel_path` (inclusive of `rel_path` itself).
    """
    backlinks = build_backlink_graph(bundle)
    known = set(backlinks)

    visited = {rel_path}
    frontier = {rel_path}
    edges: dict[Path, set[Path]] = {}

    for _ in range(depth):
        next_frontier: set[Path] = set()
        for p in frontier:
            outgoing = {t for t in forward_links(bundle, p) if t in known}
            incoming = backlinks.get(p, set())
            edges[p] = outgoing | incoming
            next_frontier |= edges[p] - visited
        visited |= next_frontier
        frontier = next_frontier
        if not frontier:
            break

    return edges


def environment_history(bundle: Bundle, environment_resource: str) -> list[Path]:
    """Every concept in the bundle whose `resource` field matches
    `environment_resource` — i.e. everything capture recorded as having happened at
    this place. Sorted paths happen to sort chronologically too, since mission
    directories are named with a leading ISO 8601 timestamp."""
    matches = []
    for rel_path in bundle.walk():
        text = (bundle.root / rel_path).read_text(encoding="utf-8")
        try:
            data, _ = frontmatter.parse(text)
        except frontmatter.FrontmatterError:
            continue
        if data.get("resource") == environment_resource:
            matches.append(rel_path)
    return sorted(matches)
