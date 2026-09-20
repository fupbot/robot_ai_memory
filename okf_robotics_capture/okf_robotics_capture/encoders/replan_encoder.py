"""Builds a Replan Event concept, bundle-relative-linked back to the current Task
Attempt."""
from __future__ import annotations

from okf_robotics_core import ReplanEvent

from ..buffer import WriteOp
from ..session import CaptureSession
from .base import Encoder

_GENERATED_BY = "okf_robotics_capture/0.1.0"


class ReplanEncoder(Encoder):
    def encode(self, event, session: CaptureSession) -> list[WriteOp]:
        if event.kind != "replan" or session.current_task_path is None:
            return []
        path = session.next_event_path("replan")
        link = "/" + session.current_task_path.as_posix()
        concept = ReplanEvent(
            title="Replan",
            resource=session.environment_resource,
            generated={"by": _GENERATED_BY, "at": event.stamp},
            body=f"Replanned at {event.stamp} during [task attempt]({link}).\n",
        )
        return [
            WriteOp("write_concept", path, concept.to_markdown()),
            WriteOp("append_log", session.mission_dir, f"Replanned during [task attempt]({link})."),
        ]
