from .base import Encoder
from .failure_encoder import FailureEncoder
from .mission_encoder import MissionEncoder
from .replan_encoder import ReplanEncoder
from .task_attempt_encoder import TaskAttemptEncoder

# Maps a watch's `trigger` config value to the encoder that consumes its Events.
# "mission" isn't driven by a watch — capture_node.py invokes MissionEncoder directly
# on node startup/shutdown.
ENCODERS = {
    "mission": MissionEncoder,
    "task_lifecycle": TaskAttemptEncoder,
    "replan": ReplanEncoder,
    "diagnostics": FailureEncoder,
}

__all__ = [
    "Encoder",
    "MissionEncoder",
    "TaskAttemptEncoder",
    "ReplanEncoder",
    "FailureEncoder",
    "ENCODERS",
]
