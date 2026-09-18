from pathlib import Path

from okf_robotics_core.links import extract_links, resolve_link


def test_extract_links_skips_external():
    body = "See [a](./a.md) and [b](/b.md) and [ext](https://example.com)."
    assert extract_links(body) == ["./a.md", "/b.md"]


def test_resolve_absolute_link():
    target = resolve_link(Path("missions/run1/tasks/task-001.md"), "/environments/house.md")
    assert target == Path("environments/house.md")


def test_resolve_relative_link():
    target = resolve_link(Path("missions/run1/tasks/task-001.md"), "../mission.md")
    assert target == Path("missions/run1/mission.md")


def test_resolve_link_with_anchor_strips_anchor():
    target = resolve_link(Path("a.md"), "./b.md#t=134.2s")
    assert target == Path("b.md")
