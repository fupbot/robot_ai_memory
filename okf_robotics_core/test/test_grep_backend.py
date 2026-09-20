from pathlib import Path

from okf_robotics_core.bundle import Bundle
from okf_robotics_core.concepts.types import EnvironmentObservation, TaskAttempt
from okf_robotics_core.search.grep_backend import GrepSearchBackend


def test_search_finds_matching_body_text(tmp_path):
    bundle = Bundle(tmp_path)
    bundle.write_concept("t1.md", TaskAttempt(body="The robot replanned near the doorway.\n"))
    bundle.write_concept("t2.md", TaskAttempt(body="Nothing interesting happened.\n"))

    backend = GrepSearchBackend(bundle)
    results = backend.search("doorway")
    assert [r.path for r in results] == [Path("t1.md")]


def test_search_respects_type_filter(tmp_path):
    bundle = Bundle(tmp_path)
    bundle.write_concept("t1.md", TaskAttempt(body="shared keyword\n"))
    bundle.write_concept("e1.md", EnvironmentObservation(body="shared keyword\n"))

    backend = GrepSearchBackend(bundle)
    results = backend.search("keyword", type_filter="Task Attempt")
    assert [r.path for r in results] == [Path("t1.md")]


def test_search_with_no_matches_returns_empty(tmp_path):
    bundle = Bundle(tmp_path)
    bundle.write_concept("t1.md", TaskAttempt(body="hello\n"))
    backend = GrepSearchBackend(bundle)
    assert backend.search("nonexistent-term") == []


def test_search_is_case_insensitive(tmp_path):
    bundle = Bundle(tmp_path)
    bundle.write_concept("t1.md", TaskAttempt(body="Replanned near the doorway.\n"))

    results = GrepSearchBackend(bundle).search("replanned")
    assert [r.path for r in results] == [Path("t1.md")]
