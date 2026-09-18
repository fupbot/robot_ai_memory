"""Bundle: an OKF directory tree of concept documents plus index.md/log.md files.

Pure filesystem I/O, no ROS dependency — see requirements.md's Package architecture.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from . import frontmatter
from .concepts.base import RESERVED_FILENAMES, Concept
from .concepts.types import concept_class_for

OKF_VERSION = "0.2"


class Bundle:
    """A single OKF bundle rooted at `root`."""

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def write_concept(self, relative_path: str | Path, concept: Concept) -> Path:
        """Write a concept document, creating parent directories as needed."""
        path = self.root / relative_path
        if path.name in RESERVED_FILENAMES:
            raise ValueError(f"{path.name!r} is a reserved filename, not a concept document")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(concept.to_markdown(), encoding="utf-8")
        return path

    def read_concept(self, relative_path: str | Path) -> Concept:
        """Read a concept document, dispatching to the known subclass for its `type`
        if one is registered (see concepts/types.py), else the generic Concept."""
        path = self.root / relative_path
        text = path.read_text(encoding="utf-8")
        data, _ = frontmatter.parse(text)
        return concept_class_for(data.get("type", "")).from_markdown(text)

    def walk(self) -> list[Path]:
        """All concept document paths in the bundle, relative to root, excluding
        reserved filenames."""
        return sorted(
            p.relative_to(self.root)
            for p in self.root.rglob("*.md")
            if p.name not in RESERVED_FILENAMES
        )

    def append_log(
        self, relative_dir: str | Path, entry: str, *, at: dt.datetime | None = None
    ) -> Path:
        """Prepend a dated entry to the log.md in `relative_dir` ("." for bundle
        root), matching the spec's newest-first, ISO-date-heading convention."""
        at = at or dt.datetime.now(dt.timezone.utc)
        log_path = self.root / relative_dir / "log.md"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        new_entry = f"## {at.date().isoformat()}\n\n{entry.strip()}\n\n"
        existing = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
        log_path.write_text(new_entry + existing, encoding="utf-8")
        return log_path

    def ensure_root_index(self) -> Path:
        """Create the bundle-root index.md with `okf_version` frontmatter if absent."""
        index_path = self.root / "index.md"
        if not index_path.exists():
            index_path.parent.mkdir(parents=True, exist_ok=True)
            index_path.write_text(
                frontmatter.serialize({"okf_version": OKF_VERSION}, "# Bundle index\n"),
                encoding="utf-8",
            )
        return index_path
