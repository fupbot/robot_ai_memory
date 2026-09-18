"""Builds/updates the Task Attempt concept for task_started / task_ended events from
TaskLifecycleTrigger. Tracks the in-progress concept per goal_id internally (rather
than relying on session.current_task_path) so a task_ended event always closes out
the correct file even if another task has since started — see the goal-overlap note
in requirements.md's known-limitations discussion."""
from __future__ import annotations

from pathlib import Path

from okf_robotics_core import TaskAttempt

from ..buffer import WriteOp
from ..session import CaptureSession
from .base import Encoder

_GENERATED_BY = "okf_robotics_capture/0.1.0"


class TaskAttemptEncoder(Encoder):
    def __init__(self):
        self._open: dict[str, tuple[Path, TaskAttempt]] = {}

    def encode(self, event, session: CaptureSession) -> list[WriteOp]:
        if event.kind == "task_started":
            goal_id = event.fields["goal_id"]
            path = session.next_task_path()
            concept = TaskAttempt(
                title=f"Task attempt {session.task_counter}",
                resource=session.environment_resource,
                status="draft",
                sources=[{"resource": f"ros-goal://{goal_id}"}],
                generated={"by": _GENERATED_BY, "at": event.stamp},
                body=f"Started at {event.stamp}.\n",
            )
            self._open[goal_id] = (path, concept)
            return [
                WriteOp("write_concept", path, concept.to_markdown()),
                WriteOp(
                    "append_log",
                    session.mission_dir,
                    f"Task attempt {session.task_counter} started.",
                ),
            ]

        if event.kind == "task_ended":
            goal_id = event.fields["goal_id"]
            entry = self._open.pop(goal_id, None)
            if entry is None:
                return []
            path, concept = entry
            concept.status = "stable"
            outcome = event.fields.get("outcome")
            concept.body += f"Ended at {event.stamp}: {outcome}.\n"
            return [
                WriteOp("write_concept", path, concept.to_markdown()),
                WriteOp(
                    "append_log", session.mission_dir, f"Task attempt ended: {outcome}."
                ),
            ]

        return []
