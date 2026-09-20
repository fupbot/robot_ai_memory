"""Generic failure detector using the standard diagnostic_msgs/msg/DiagnosticArray
topic (conventionally /diagnostics) — works with any robot's diagnostics, not tied to
one planner or nav2 version."""
from __future__ import annotations

from .base import Event, EventTrigger

_ERROR_LEVEL = 2  # diagnostic_msgs/msg/DiagnosticStatus.ERROR


def _level_as_int(level) -> int:
    # rosidl_runtime_py has represented the `byte` DiagnosticStatus.level field as a
    # raw int, a single-byte `bytes` object, or (Jazzy) a one-character str like
    # '\x02' across different distro versions — normalize defensively rather than
    # assume one (see requirements.md's ROS2 distro compatibility section).
    if isinstance(level, (bytes, bytearray)):
        return level[0]
    if isinstance(level, str) and len(level) == 1:
        return ord(level)
    return int(level)


class DiagnosticsTrigger(EventTrigger):
    def check(self, topic, msg_type, fields, stamp):
        for status in fields.get("status", []):
            if _level_as_int(status.get("level", 0)) >= _ERROR_LEVEL:
                return Event(
                    "failure",
                    topic,
                    msg_type,
                    stamp,
                    {"name": status.get("name"), "message": status.get("message")},
                )
        return None
