from pathlib import Path

import pytest

from okf_robotics_core.bundle import Bundle
from okf_robotics_core.concepts.types import MissionRun, TaskAttempt


def test_write_and_read_concept_round_trip(tmp_path):
    bundle = Bundle(tmp_path)
    concept = TaskAttempt(title="Attempt 1", body="Went fine.\n")
    bundle.write_concept("missions/run1/tasks/task-001.md", concept)

    restored = bundle.read_concept("missions/run1/tasks/task-001.md")
    assert isinstance(restored, TaskAttempt)
    assert restored.title == "Attempt 1"
    assert restored.body == "Went fine.\n"


def test_write_concept_rejects_reserved_filename(tmp_path):
    bundle = Bundle(tmp_path)
    with pytest.raises(ValueError):
        bundle.write_concept("missions/run1/log.md", TaskAttempt())


def test_walk_excludes_reserved_filenames(tmp_path):
    bundle = Bundle(tmp_path)
    bundle.write_concept("a.md", MissionRun(title="Run"))
    (tmp_path / "index.md").write_text("---\nokf_version: '0.2'\n---\n")
    (tmp_path / "log.md").write_text("## 2026-09-18\n\nsomething\n")

    assert bundle.walk() == [Path("a.md")]


def test_append_log_prepends_newest_entry(tmp_path):
    bundle = Bundle(tmp_path)
    bundle.append_log(".", "First event.")
    bundle.append_log(".", "Second event.")

    log_text = (tmp_path / "log.md").read_text()
    assert log_text.index("Second event.") < log_text.index("First event.")


def test_ensure_root_index_creates_file_once(tmp_path):
    bundle = Bundle(tmp_path)
    path = bundle.ensure_root_index()
    assert path.exists()
    contents = path.read_text()
    bundle.ensure_root_index()
    assert path.read_text() == contents
