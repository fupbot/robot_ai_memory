"""Grep-based v1 search backend — zero extra dependencies, matches OKF's "readable by
cat" philosophy. See requirements.md's Search (v1) section for the portability
rationale."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .. import frontmatter
from ..bundle import Bundle
from .base import SearchBackend, SearchResult


class GrepSearchBackend(SearchBackend):
    """Filters candidate files by frontmatter (type/tags) first, then full-text
    searches only those files using `rg` if available, falling back to `grep -n`."""

    def __init__(self, bundle: Bundle):
        self.bundle = bundle

    def _candidate_paths(
        self, type_filter: str | None, tags: list[str] | None
    ) -> list[Path]:
        paths = []
        for rel_path in self.bundle.walk():
            if type_filter is None and not tags:
                paths.append(rel_path)
                continue
            text = (self.bundle.root / rel_path).read_text(encoding="utf-8")
            try:
                data, _ = frontmatter.parse(text)
            except frontmatter.FrontmatterError:
                continue
            if type_filter is not None and data.get("type") != type_filter:
                continue
            if tags and not set(tags) & set(data.get("tags") or []):
                continue
            paths.append(rel_path)
        return paths

    def search(
        self,
        query: str,
        *,
        type_filter: str | None = None,
        tags: list[str] | None = None,
    ) -> list[SearchResult]:
        candidates = self._candidate_paths(type_filter, tags)
        if not candidates:
            return []
        if not query:
            return [SearchResult(p, 0, "") for p in candidates]

        executable = "rg" if shutil.which("rg") else "grep"
        # -H forces the filename prefix even with a single candidate file, which
        # both grep and rg otherwise omit — required for the "path:line:snippet"
        # parsing below to work regardless of how many files match the filters.
        args = [executable, "-H", "-n", "-i", "--", query] + [
            str(self.bundle.root / p) for p in candidates
        ]
        result = subprocess.run(args, capture_output=True, text=True)
        # grep/rg exit 1 means "no matches", not a failure; only >1 is a real error.
        if result.returncode not in (0, 1):
            raise RuntimeError(f"{executable} failed: {result.stderr.strip()}")

        matches = []
        for line in result.stdout.splitlines():
            path_str, line_no, snippet = line.split(":", 2)
            matches.append(
                SearchResult(
                    Path(path_str).relative_to(self.bundle.root),
                    int(line_no),
                    snippet,
                )
            )
        return matches
