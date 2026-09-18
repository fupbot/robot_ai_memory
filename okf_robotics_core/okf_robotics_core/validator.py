"""Permissive OKF conformance checking.

Per spec, consumers MUST NOT reject a bundle for: missing optional frontmatter
fields, unknown `type` values, unknown extra frontmatter keys, broken cross-links, or
missing index.md files. The only genuine conformance failures are unparseable
frontmatter and a missing/empty `type` field. Everything else below is reported as a
warning — a useful lint signal, never a rejection.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import frontmatter
from .bundle import Bundle
from .links import extract_links, resolve_link


@dataclass
class Issue:
    severity: str  # "error" | "warning"
    path: Path
    message: str


def validate(bundle: Bundle) -> list[Issue]:
    """Validate every concept document in `bundle`."""
    issues: list[Issue] = []
    concept_paths = bundle.walk()
    known_paths = set(concept_paths)

    for rel_path in concept_paths:
        text = (bundle.root / rel_path).read_text(encoding="utf-8")
        try:
            data, body = frontmatter.parse(text)
        except frontmatter.FrontmatterError as exc:
            issues.append(Issue("error", rel_path, f"unparseable frontmatter: {exc}"))
            continue

        if not data.get("type"):
            issues.append(Issue("error", rel_path, "missing required 'type' field"))

        for link in extract_links(body):
            target = resolve_link(rel_path, link)
            if target is not None and target not in known_paths:
                issues.append(Issue("warning", rel_path, f"broken link to '{link}'"))

    return issues
