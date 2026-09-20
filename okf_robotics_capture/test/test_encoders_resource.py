from okf_robotics_capture.encoders.failure_encoder import FailureEncoder
from okf_robotics_capture.encoders.replan_encoder import ReplanEncoder
from okf_robotics_capture.session import CaptureSession
from okf_robotics_capture.triggers.base import Event

ENV = "map://test_world"


def _session():
    session = CaptureSession.start("m", ENV)
    session.next_task_path()
    return session


def test_replan_event_carries_environment_resource():
    event = Event("replan", "/plan", "nav_msgs/msg/Path", "2026-01-01T00:00:00+00:00", {})
    ops = ReplanEncoder().encode(event, _session())
    assert f"resource: {ENV}" in ops[0].content


def test_failure_note_carries_environment_resource():
    event = Event(
        "failure", "/diagnostics", "x", "2026-01-01T00:00:00+00:00",
        {"name": "motor", "message": "stalled"},
    )
    ops = FailureEncoder().encode(event, _session())
    assert f"resource: {ENV}" in ops[0].content
