"""Bundle-relative markdown link extraction and resolution.

Per spec, links are plain markdown; the bundle-relative absolute form ("/tables/x.md")
is recommended because it survives file moves, relative ("./x.md", "../x.md") is also
valid. Consumers MUST tolerate links to nonexistent targets — this module resolves
link text to paths but never asserts those paths exist.
"""
from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

from . import frontmatter

if TYPE_CHECKING:
    from .bundle import Bundle

_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def extract_links(body: str) -> list[str]:
    """Return the raw link targets in a concept's markdown body, skipping external
    (http/https/mailto) links."""
    links = []
    for target in _LINK_RE.findall(body):
        target = target.strip()
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        links.append(target)
    return links


def resolve_link(from_path: Path, link: str) -> Path | None:
    """Resolve a link found in the document at `from_path` to a bundle-relative path.

    Returns None for links this can't meaningfully resolve (e.g. anchor-only links).
    """
    link = link.split("#", 1)[0]
    if not link:
        return None

    if link.startswith("/"):
        resolved = PurePosixPath(link.lstrip("/"))
    else:
        resolved = PurePosixPath(from_path.parent.as_posix()) / link

    parts: list[str] = []
    for part in resolved.parts:
        if part == "..":
            if parts:
                parts.pop()
        elif part != ".":
            parts.append(part)
    return Path(*parts) if parts else None


def build_backlink_graph(bundle: "Bundle") -> dict[Path, set[Path]]:
    """Map each concept path in `bundle` to the set of concept paths that link to it."""
    graph: dict[Path, set[Path]] = {p: set() for p in bundle.walk()}
    for rel_path in list(graph):
        text = (bundle.root / rel_path).read_text(encoding="utf-8")
        _, body = frontmatter.parse(text)
        for link in extract_links(body):
            target = resolve_link(rel_path, link)
            if target in graph:
                graph[target].add(rel_path)
    return graph
