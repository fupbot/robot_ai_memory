import pytest

from okf_robotics_capture.triggers.diagnostics_trigger import DiagnosticsTrigger


def _check(level):
    fields = {"status": [{"level": level, "name": "motor", "message": "stalled"}]}
    return DiagnosticsTrigger().check("/diagnostics", "x", fields, "t")


@pytest.mark.parametrize("level", [2, 3, b"\x02", "\x02", "\x03"])
def test_error_levels_fire_in_every_representation(level):
    assert _check(level).kind == "failure"


@pytest.mark.parametrize("level", [0, 1, b"\x00", "\x00", "\x01"])
def test_non_error_levels_do_not_fire(level):
    assert _check(level) is None
