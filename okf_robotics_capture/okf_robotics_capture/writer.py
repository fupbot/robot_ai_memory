"""BundleWriter: the only place in okf_robotics_capture that performs disk I/O for
concept/log writes. Called exclusively from the background flush thread in
capture_node.py — never from a ROS subscription callback. See requirements.md's
Safety section.
"""
from __future__ import annotations

from okf_robotics_core.bundle import Bundle

from .buffer import HotMemoryBuffer, WriteOp


class BundleWriter:
    def __init__(self, bundle: Bundle):
        self.bundle = bundle

    def flush(self, buffer: HotMemoryBuffer) -> int:
        """Drain `buffer` and persist every queued op. Returns the number written."""
        ops = buffer.drain()
        for op in ops:
            self._apply(op)
        return len(ops)

    def _apply(self, op: WriteOp) -> None:
        if op.kind == "write_concept":
            path = self.bundle.root / op.path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(op.content, encoding="utf-8")
        elif op.kind == "append_log":
            self.bundle.append_log(op.path, op.content)
        else:
            raise ValueError(f"unknown WriteOp kind: {op.kind!r}")
