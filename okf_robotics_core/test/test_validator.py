from okf_robotics_core.bundle import Bundle
from okf_robotics_core.concepts.types import EnvironmentObservation, TaskAttempt
from okf_robotics_core.validator import validate


def test_valid_bundle_has_no_errors(tmp_path):
    bundle = Bundle(tmp_path)
    bundle.write_concept("environments/house.md", EnvironmentObservation(title="House"))
    bundle.write_concept(
        "missions/run1/tasks/task-001.md",
        TaskAttempt(body="See [environment](/environments/house.md).\n"),
    )
    issues = validate(bundle)
    assert issues == []


def test_missing_type_is_an_error(tmp_path):
    bundle = Bundle(tmp_path)
    (tmp_path / "bad.md").write_text("---\ntitle: no type\n---\nbody\n")
    issues = validate(bundle)
    assert len(issues) == 1
    assert issues[0].severity == "error"


def test_broken_link_is_a_warning_not_an_error(tmp_path):
    bundle = Bundle(tmp_path)
    bundle.write_concept(
        "missions/run1/tasks/task-001.md",
        TaskAttempt(body="See [nowhere](/environments/missing.md).\n"),
    )
    issues = validate(bundle)
    assert len(issues) == 1
    assert issues[0].severity == "warning"


def test_unknown_type_value_is_not_flagged(tmp_path):
    bundle = Bundle(tmp_path)
    (tmp_path / "odd.md").write_text("---\ntype: Something Nobody Registered\n---\nbody\n")
    issues = validate(bundle)
    assert issues == []
