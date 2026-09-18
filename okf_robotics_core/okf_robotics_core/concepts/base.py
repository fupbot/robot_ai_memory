"""Concept: the in-memory representation of a single OKF concept document."""
from __future__ import annotations

from dataclasses import dataclass, field

from .. import frontmatter

# Per spec: these two filenames are reserved (directory listing / update history)
# and must not be used for concept documents.
RESERVED_FILENAMES = {"index.md", "log.md"}

# Frontmatter keys with a dedicated Concept field. Anything else round-trips through
# `extra` untouched — the spec explicitly allows arbitrary extra frontmatter keys
# (e.g. okf-agent-memory's `code_refs`, this project's `config_refs`), so Concept
# never needs to know the full set of keys any consumer might add.
_KNOWN_KEYS = {
    "type",
    "title",
    "description",
    "resource",
    "tags",
    "sources",
    "generated",
    "verified",
    "status",
    "stale_after",
}


@dataclass
class Concept:
    """One OKF concept document: known frontmatter fields, an `extra` catch-all for
    unrecognized frontmatter keys, and the free-form markdown body."""

    type: str
    title: str | None = None
    description: str | None = None
    resource: str | None = None
    tags: list[str] = field(default_factory=list)
    sources: list[dict] = field(default_factory=list)
    generated: dict | None = None
    verified: list[dict] = field(default_factory=list)
    status: str | None = None
    stale_after: str | None = None
    extra: dict = field(default_factory=dict)
    body: str = ""

    def to_frontmatter(self) -> dict:
        data: dict = {"type": self.type}
        if self.title is not None:
            data["title"] = self.title
        if self.description is not None:
            data["description"] = self.description
        if self.resource is not None:
            data["resource"] = self.resource
        if self.tags:
            data["tags"] = self.tags
        if self.sources:
            data["sources"] = self.sources
        if self.generated is not None:
            data["generated"] = self.generated
        if self.verified:
            data["verified"] = self.verified
        if self.status is not None:
            data["status"] = self.status
        if self.stale_after is not None:
            data["stale_after"] = self.stale_after
        data.update(self.extra)
        return data

    def to_markdown(self) -> str:
        return frontmatter.serialize(self.to_frontmatter(), self.body)

    @classmethod
    def from_markdown(cls, text: str) -> "Concept":
        data, body = frontmatter.parse(text)
        if not data.get("type"):
            raise frontmatter.FrontmatterError(
                "frontmatter is missing the required 'type' field"
            )
        extra = {k: v for k, v in data.items() if k not in _KNOWN_KEYS}
        return cls(
            type=data["type"],
            title=data.get("title"),
            description=data.get("description"),
            resource=data.get("resource"),
            tags=data.get("tags") or [],
            sources=data.get("sources") or [],
            generated=data.get("generated"),
            verified=data.get("verified") or [],
            status=data.get("status"),
            stale_after=data.get("stale_after"),
            extra=extra,
            body=body,
        )
