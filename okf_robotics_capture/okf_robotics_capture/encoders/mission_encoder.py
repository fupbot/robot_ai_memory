"""Builds/finalizes the Mission Run concept for a session. Driven directly by
capture_node's own start/shutdown lifecycle via synthetic Events (not by an incoming
ROS message) — see requirements.md's proposed bundle layout."""
from __future__ import annotations

from pathlib import Path

from okf_robotics_core import MissionRun

from ..buffer import WriteOp
from ..session import CaptureSession
from .base import Encoder

_GENERATED_BY = "okf_robotics_capture/0.1.0"


class MissionEncoder(Encoder):
    def encode(self, event, session: CaptureSession) -> list[WriteOp]:
        if event.kind == "mission_started":
            concept = MissionRun(
                title=session.mission_dir.name,
                resource=session.environment_resource,
                status="draft",
                generated={"by": _GENERATED_BY, "at": event.stamp},
                body=f"Mission started at {event.stamp}.\n",
            )
            return [
                WriteOp("write_concept", session.mission_concept_path, concept.to_markdown()),
                WriteOp(
                    "append_log", Path("."), f"Mission **{session.mission_dir.name}** started."
                ),
            ]

        if event.kind == "mission_ended":
            concept = MissionRun(
                title=session.mission_dir.name,
                resource=session.environment_resource,
                status="stable",
                generated={"by": _GENERATED_BY, "at": event.stamp},
                body=f"Mission started at {session.started_at}, ended at {event.stamp}.\n",
            )
            return [
                WriteOp("write_concept", session.mission_concept_path, concept.to_markdown()),
                WriteOp(
                    "append_log", Path("."), f"Mission **{session.mission_dir.name}** ended."
                ),
                WriteOp("append_log", session.mission_dir, f"Mission ended at {event.stamp}."),
            ]

        return []
