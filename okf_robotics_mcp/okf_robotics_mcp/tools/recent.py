"""recent: read a bundle directory's log.md, newest-first, exactly as written per the
OKF spec's log.md convention (see okf_robotics_core.bundle.Bundle.append_log)."""
from __future__ import annotations

from okf_robotics_core.bundle import Bundle


def recent(bundle: Bundle, *, relative_dir: str = ".", limit: int | None = None) -> str:
    log_path = bundle.root / relative_dir / "log.md"
    if not log_path.exists():
        return ""
    text = log_path.read_text(encoding="utf-8")
    if limit is None:
        return text

    # Entries are "## <date>\n\n<prose>\n\n" blocks, newest first (see
    # bundle.append_log) — split on the heading marker to take the first N.
    parts = text.split("\n## ")
    head, *rest = parts
    entries = ([head] if head.strip() else []) + [f"## {p}" for p in rest]
    return "\n".join(entries[:limit])
