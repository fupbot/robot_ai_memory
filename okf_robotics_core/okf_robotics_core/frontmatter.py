"""Parse and serialize OKF markdown documents: a YAML frontmatter block plus a
markdown body, delimited by '---' lines per the OKF spec (v0.2)."""
from __future__ import annotations

import yaml

FRONTMATTER_DELIMITER = "---"


class FrontmatterError(ValueError):
    """Raised when a document's frontmatter block is missing or not parseable YAML."""


def parse(text: str) -> tuple[dict, str]:
    """Split `text` into (frontmatter_dict, body).

    Raises FrontmatterError if the document doesn't start with a '---' block, the
    block is never closed, or its contents aren't a YAML mapping.
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != FRONTMATTER_DELIMITER:
        raise FrontmatterError("document does not start with a '---' frontmatter block")

    for i in range(1, len(lines)):
        if lines[i].strip() == FRONTMATTER_DELIMITER:
            raw_frontmatter = "".join(lines[1:i])
            body = "".join(lines[i + 1 :])
            try:
                data = yaml.safe_load(raw_frontmatter) or {}
            except yaml.YAMLError as exc:
                raise FrontmatterError(f"invalid YAML frontmatter: {exc}") from exc
            if not isinstance(data, dict):
                raise FrontmatterError("frontmatter block must be a YAML mapping")
            return data, body.lstrip("\n")

    raise FrontmatterError("unterminated '---' frontmatter block")


def serialize(frontmatter: dict, body: str) -> str:
    """Render a (frontmatter_dict, body) pair back into OKF markdown text."""
    raw_frontmatter = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True)
    if body and not body.endswith("\n"):
        body += "\n"
    return f"{FRONTMATTER_DELIMITER}\n{raw_frontmatter}{FRONTMATTER_DELIMITER}\n\n{body}"
