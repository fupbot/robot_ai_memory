"""Encoder: deterministic template turning a detected Event into WriteOps for the
buffer. No inference, no LLM — see requirements.md's Encoding approach section.
Encoding is pure CPU/string work; only writer.py touches disk, and only from the
background flush thread — see requirements.md's Safety section.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..buffer import WriteOp
from ..session import CaptureSession
from ..triggers.base import Event


class Encoder(ABC):
    @abstractmethod
    def encode(self, event: Event, session: CaptureSession) -> list[WriteOp]:
        """Turn `event` into zero or more WriteOps, updating `session` in place as
        needed (e.g. registering a new Task Attempt's path for later linking)."""
        raise NotImplementedError
