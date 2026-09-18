import pytest

from okf_robotics_core import frontmatter
from okf_robotics_core.concepts.base import Concept
from okf_robotics_core.concepts.types import TaskAttempt, concept_class_for


def test_round_trip_preserves_known_and_extra_fields():
    concept = TaskAttempt(
        title="Nav loop attempt 3",
        resource="map://gazebo_house_world",
        tags=["nav2"],
        extra={"config_refs": ["params/nav2_params_v3.md"]},
        body="It replanned once.\n",
    )
    restored = TaskAttempt.from_markdown(concept.to_markdown())
    assert restored.type == "Task Attempt"
    assert restored.title == "Nav loop attempt 3"
    assert restored.extra == {"config_refs": ["params/nav2_params_v3.md"]}
    assert restored.body == "It replanned once.\n"


def test_missing_type_raises():
    with pytest.raises(frontmatter.FrontmatterError):
        Concept.from_markdown("---\ntitle: no type here\n---\nbody")


def test_concept_class_for_unknown_type_falls_back_to_base():
    assert concept_class_for("Something Not In The Registry") is Concept


def test_concept_class_for_known_type():
    assert concept_class_for("Task Attempt") is TaskAttempt
