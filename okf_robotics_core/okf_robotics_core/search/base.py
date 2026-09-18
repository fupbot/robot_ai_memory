"""Abstract search interface so `okf_robotics_core` can swap backends (grep for v1,
FTS5/SQLite later) without changing callers — see requirements.md's Search section."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SearchResult:
    path: Path
    line_number: int
    snippet: str


class SearchBackend(ABC):
    @abstractmethod
    def search(
        self,
        query: str,
        *,
        type_filter: str | None = None,
        tags: list[str] | None = None,
    ) -> list[SearchResult]:
        """Search concept document bodies for `query`, optionally restricted to
        concepts whose frontmatter `type` matches `type_filter` and/or whose `tags`
        overlap `tags`."""
        raise NotImplementedError
