import pytest

from okf_robotics_core import frontmatter


def test_round_trip():
    text = frontmatter.serialize({"type": "Task Attempt", "tags": ["nav"]}, "Body text.\n")
    data, body = frontmatter.parse(text)
    assert data == {"type": "Task Attempt", "tags": ["nav"]}
    assert body == "Body text.\n"


def test_missing_delimiter_raises():
    with pytest.raises(frontmatter.FrontmatterError):
        frontmatter.parse("no frontmatter here")


def test_invalid_yaml_raises():
    with pytest.raises(frontmatter.FrontmatterError):
        frontmatter.parse("---\n[unbalanced\n---\nbody")


def test_non_mapping_frontmatter_raises():
    with pytest.raises(frontmatter.FrontmatterError):
        frontmatter.parse("---\n- a\n- b\n---\nbody")


def test_unterminated_block_raises():
    with pytest.raises(frontmatter.FrontmatterError):
        frontmatter.parse("---\ntype: X\n")
