"""EventTrigger: decides whether an incoming message is an event boundary worth
recording. Called synchronously from the subscription callback in capture_node.py, so
implementations must be cheap — no I/O, no blocking (see requirements.md's Safety
section: the capture node must never block the hot path). Message fields are passed
in as a plain dict (already converted from the ROS message), so triggers have no
rclpy dependency and are unit-testable without ROS installed.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Event:
    """A detected event boundary, ready for encoding."""

    kind: str  # e.g. "task_started", "task_ended", "replan", "failure"
    topic: str
    msg_type: str
    stamp: str  # ISO 8601
    fields: dict = field(default_factory=dict)


class EventTrigger(ABC):
    @abstractmethod
    def check(self, topic: str, msg_type: str, fields: dict, stamp: str) -> Event | None:
        """Return an Event if `fields` (the incoming message as a plain dict)
        represents an event boundary, else None."""
        raise NotImplementedError

    def reset(self) -> None:
        """Called when a new task starts, so per-task trigger state (e.g. "have I
        seen the initial plan yet") doesn't leak across tasks. No-op by default."""
        return None
