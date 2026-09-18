from .base import Event, EventTrigger
from .diagnostics_trigger import DiagnosticsTrigger
from .replan_trigger import ReplanTrigger
from .task_lifecycle import TaskLifecycleTrigger

# Maps a watch's `trigger` config value to the class that implements it.
TRIGGERS = {
    "task_lifecycle": TaskLifecycleTrigger,
    "replan": ReplanTrigger,
    "diagnostics": DiagnosticsTrigger,
}

__all__ = [
    "Event",
    "EventTrigger",
    "TaskLifecycleTrigger",
    "ReplanTrigger",
    "DiagnosticsTrigger",
    "TRIGGERS",
]
