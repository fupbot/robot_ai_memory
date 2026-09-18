"""okf_robotics_mcp's MCP server — the only module in this package that imports the
`mcp` SDK. Exposes read-only query tools over an OKF bundle so a planner's own LLM can
ask "what happened last time in this environment"; this server never itself invokes
an LLM — see requirements.md's Encoding approach section.

Bundle location is read from the OKF_ROBOTICS_BUNDLE_ROOT environment variable rather
than a YAML config file, since MCP servers are typically launched directly by the
host (Claude, an IDE), not via `ros2 run` — see requirements.md's Package
architecture section.
"""
from __future__ import annotations

import os

from okf_robotics_core.bundle import Bundle

from . import tools

try:
    # mcp >= 2.0 (July 2026): FastMCP was renamed to MCPServer, moved out of
    # mcp.server.fastmcp. See requirements.md/notes for context — this shim exists
    # because pip installs 2.x by default as of this writing, but 1.x is still in use.
    from mcp.server import MCPServer as _Server
except ImportError:
    from mcp.server.fastmcp import FastMCP as _Server

mcp = _Server("okf-robotics")

_bundle_root = os.environ.get("OKF_ROBOTICS_BUNDLE_ROOT", "~/okf_robotics_bundle")
bundle = Bundle(_bundle_root)


@mcp.tool()
def search(
    query: str, type_filter: str | None = None, tags: list[str] | None = None
) -> list[dict]:
    """Full-text search over the OKF bundle's concept bodies, optionally filtered by
    concept `type` (e.g. "Task Attempt") and/or tags."""
    return tools.search_bundle(bundle, query, type_filter=type_filter, tags=tags)


@mcp.tool()
def get_concept(path: str) -> dict:
    """Fetch one concept document in full, plus the paths it links to and the paths
    that link to it."""
    return tools.get_concept(bundle, path)


@mcp.tool()
def graph_neighbors(path: str, depth: int = 1) -> dict:
    """Bounded-depth traversal of the markdown-link graph starting from `path`."""
    return tools.graph_neighbors(bundle, path, depth=depth)


@mcp.tool()
def environment_history(environment_resource: str) -> list[str]:
    """Every concept recorded as having happened at `environment_resource` (e.g.
    "map://gazebo_house_world") — the core "what happened last time here" query."""
    return tools.environment_history(bundle, environment_resource)


@mcp.tool()
def recent(relative_dir: str = ".", limit: int | None = None) -> str:
    """Read a bundle directory's log.md, newest-first."""
    return tools.recent(bundle, relative_dir=relative_dir, limit=limit)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
