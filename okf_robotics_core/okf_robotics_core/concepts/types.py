"""Robotics-specific OKF concept types (see requirements.md's Schema design notes).

Each is a thin Concept subclass that only fixes the default `type` string — the spec
tolerates unknown `type` values from any consumer, so these exist for convenience
(construction, isinstance checks, dispatch) rather than because the format requires
registering types anywhere.
"""
from __future__ import annotations

from dataclasses import dataclass

from .base import Concept


@dataclass
class MissionRun(Concept):
    type: str = "Mission Run"


@dataclass
class TaskAttempt(Concept):
    type: str = "Task Attempt"


@dataclass
class ReplanEvent(Concept):
    type: str = "Replan Event"


@dataclass
class FailureNote(Concept):
    type: str = "Failure/Recovery Note"


@dataclass
class EnvironmentObservation(Concept):
    type: str = "Environment Observation"


@dataclass
class ParamChange(Concept):
    type: str = "Param/Planner Change"


CONCEPT_TYPES: dict[str, type[Concept]] = {
    "Mission Run": MissionRun,
    "Task Attempt": TaskAttempt,
    "Replan Event": ReplanEvent,
    "Failure/Recovery Note": FailureNote,
    "Environment Observation": EnvironmentObservation,
    "Param/Planner Change": ParamChange,
}


def concept_class_for(type_name: str) -> type[Concept]:
    """Return the known subclass for a `type` string, or the generic Concept if the
    type isn't one of ours (e.g. it came from a different OKF-producing tool)."""
    return CONCEPT_TYPES.get(type_name, Concept)
