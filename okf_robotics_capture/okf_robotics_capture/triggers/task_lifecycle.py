"""Generic task start/end trigger based on the standard action_msgs/msg/GoalStatusArray
message every ROS2 action server publishes — not nav2-specific, works for any
action-based task (nav2, MoveIt, a custom action server)."""
from __future__ import annotations

from .base import Event, EventTrigger

# action_msgs/msg/GoalStatus status codes (stable across all supported distros).
_STATUS_EXECUTING = 2
_TERMINAL_STATUSES = {4, 5, 6}  # SUCCEEDED, CANCELED, ABORTED
_OUTCOME_BY_STATUS = {4: "succeeded", 5: "canceled", 6: "aborted"}


def _goal_id_key(entry: dict) -> str:
    uuid_bytes = entry.get("goal_info", {}).get("goal_id", {}).get("uuid", [])
    return "".join(f"{b:02x}" for b in uuid_bytes)


class TaskLifecycleTrigger(EventTrigger):
    def __init__(self):
        self._known_goal_status: dict[str, int] = {}

    def reset(self) -> None:
        self._known_goal_status.clear()

    def check(self, topic, msg_type, fields, stamp):
        for entry in fields.get("status_list", []):
            goal_id = _goal_id_key(entry)
            status = entry.get("status")
            previous = self._known_goal_status.get(goal_id)
            self._known_goal_status[goal_id] = status

            # Fires on the transition INTO EXECUTING, regardless of what the prior
            # status was (unseen, ACCEPTED, ...) — action servers typically publish
            # ACCEPTED before EXECUTING, so gating on "never seen before" would miss
            # the real start.
            if previous != _STATUS_EXECUTING and status == _STATUS_EXECUTING:
                return Event("task_started", topic, msg_type, stamp, {"goal_id": goal_id})

            if (
                previous is not None
                and previous not in _TERMINAL_STATUSES
                and status in _TERMINAL_STATUSES
            ):
                return Event(
                    "task_ended",
                    topic,
                    msg_type,
                    stamp,
                    {"goal_id": goal_id, "outcome": _OUTCOME_BY_STATUS[status]},
                )
        return None
