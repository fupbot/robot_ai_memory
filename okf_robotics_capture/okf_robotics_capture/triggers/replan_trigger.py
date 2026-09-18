"""Fires when a new message arrives on a "plan" topic (e.g. nav_msgs/msg/Path
republished by a planner) after the first one for the current task — the first
message is the initial plan, not a replan. capture_node.py calls reset() on this
trigger whenever a task_started event fires, so the next message after a new task
begins is treated as the initial plan again."""
from __future__ import annotations

from .base import Event, EventTrigger


class ReplanTrigger(EventTrigger):
    def __init__(self):
        self._seen_initial_plan = False

    def reset(self) -> None:
        self._seen_initial_plan = False

    def check(self, topic, msg_type, fields, stamp):
        if not self._seen_initial_plan:
            self._seen_initial_plan = True
            return None
        return Event("replan", topic, msg_type, stamp, {})
