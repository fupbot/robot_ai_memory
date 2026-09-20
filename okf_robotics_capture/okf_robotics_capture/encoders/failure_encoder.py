"""Builds a Failure/Recovery Note concept from a diagnostics failure event, linked
back to the current Task Attempt when one is in progress."""
from __future__ import annotations

from okf_robotics_core import FailureNote

from ..buffer import WriteOp
from ..session import CaptureSession
from .base import Encoder

_GENERATED_BY = "okf_robotics_capture/0.1.0"


class FailureEncoder(Encoder):
    def encode(self, event, session: CaptureSession) -> list[WriteOp]:
        if event.kind != "failure":
            return []
        path = session.next_event_path("failure")
        body = f"{event.fields.get('name', 'unknown')}: {event.fields.get('message', '')}\n"
        if session.current_task_path is not None:
            link = "/" + session.current_task_path.as_posix()
            body += f"\nDuring [task attempt]({link}).\n"
        concept = FailureNote(
            title=event.fields.get("name") or "Failure",
            resource=session.environment_resource,
            generated={"by": _GENERATED_BY, "at": event.stamp},
            body=body,
        )
        log_line = f"Failure: {event.fields.get('name')} - {event.fields.get('message')}"
        return [
            WriteOp("write_concept", path, concept.to_markdown()),
            WriteOp("append_log", session.mission_dir, log_line),
        ]
