"""HotMemoryBuffer: the non-blocking side of the capture pipeline.

`put()` is called from the ROS subscription callback and must never block or fail
under load — see requirements.md's Safety section (chosen approach: non-blocking with
buffering, not drop-on-backpressure). A bounded in-memory queue absorbs bursts; if it
fills up, overflow spills to a disk directory instead of being dropped or blocking the
caller, mirroring hermes-okf's hot-buffer/cold-archive pattern (see requirements.md's
Schema design notes, "Prior art directly validating earlier decisions").
"""
from __future__ import annotations

import json
import queue
import time
import uuid
from dataclasses import dataclass
from pathlib import Path


@dataclass
class WriteOp:
    kind: str  # "write_concept" | "append_log"
    # write_concept: the concept file's bundle-relative path.
    # append_log: the bundle-relative directory whose log.md gets the entry ("." for
    # bundle root).
    path: Path
    # write_concept: the full rendered markdown text to write.
    # append_log: the log entry text.
    content: str


class HotMemoryBuffer:
    def __init__(self, max_size: int, spill_dir: Path):
        self._queue: "queue.Queue[WriteOp]" = queue.Queue(maxsize=max_size)
        self.spill_dir = Path(spill_dir)

    def put(self, op: WriteOp) -> None:
        """Never blocks: enqueues in-memory if there's room, else spills to disk."""
        try:
            self._queue.put_nowait(op)
        except queue.Full:
            self._spill(op)

    def _spill(self, op: WriteOp) -> None:
        self.spill_dir.mkdir(parents=True, exist_ok=True)
        spill_path = self.spill_dir / f"{time.time_ns()}-{uuid.uuid4().hex}.json"
        spill_path.write_text(
            json.dumps({"kind": op.kind, "path": str(op.path), "content": op.content}),
            encoding="utf-8",
        )

    def drain(self) -> list[WriteOp]:
        """Flush-thread only: returns every op queued since the last drain (in-memory
        first, then any spilled-to-disk overflow)."""
        ops: list[WriteOp] = []
        while True:
            try:
                ops.append(self._queue.get_nowait())
            except queue.Empty:
                break
        ops.extend(self._drain_spill())
        return ops

    def _drain_spill(self) -> list[WriteOp]:
        if not self.spill_dir.exists():
            return []
        ops = []
        for spill_path in sorted(self.spill_dir.glob("*.json")):
            data = json.loads(spill_path.read_text(encoding="utf-8"))
            ops.append(WriteOp(data["kind"], Path(data["path"]), data["content"]))
            spill_path.unlink()
        return ops
