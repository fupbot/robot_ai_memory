"""CaptureSession: mission/task bookkeeping for a single capture_node run.

Pure Python (no rclpy) — owns the mission directory name, the running task counter,
and the current task's bundle path so encoders can link Replan/Failure events back to
the Task Attempt they happened during. See requirements.md's proposed bundle layout.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path


def _mission_slug(at: dt.datetime, name: str) -> str:
    # Windows-safe ISO 8601 timestamp — reused verbatim from hermes-okf's convention,
    # see requirements.md's Schema design notes ("Prior art directly validating
    # earlier decisions").
    ts = at.strftime("%Y-%m-%dT%H-%M-%SZ")
    return f"{ts}-{name}"


@dataclass
class CaptureSession:
    mission_dir: Path
    environment_resource: str | None = None
    started_at: str = ""
    task_counter: int = 0
    current_task_path: Path | None = None
    event_counters: dict = field(default_factory=dict)

    @classmethod
    def start(
        cls,
        mission_name: str,
        environment_resource: str | None = None,
        *,
        at: dt.datetime | None = None,
    ) -> "CaptureSession":
        at = at or dt.datetime.now(dt.timezone.utc)
        return cls(
            mission_dir=Path("missions") / _mission_slug(at, mission_name),
            environment_resource=environment_resource,
            started_at=at.isoformat(),
        )

    @property
    def mission_concept_path(self) -> Path:
        return self.mission_dir / "mission.md"

    def next_task_path(self) -> Path:
        self.task_counter += 1
        path = self.mission_dir / "tasks" / f"task-{self.task_counter:03d}.md"
        self.current_task_path = path
        return path

    def next_event_path(self, kind: str) -> Path:
        self.event_counters[kind] = self.event_counters.get(kind, 0) + 1
        return self.mission_dir / "events" / f"{kind}-{self.event_counters[kind]:03d}.md"
