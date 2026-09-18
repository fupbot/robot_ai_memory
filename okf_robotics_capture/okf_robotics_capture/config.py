"""Load and validate okf_robotics_capture's YAML configuration.

No rclpy dependency — pure YAML parsing, so this is unit-testable without ROS
installed. See requirements.md's ROS2 distro compatibility section: topic names and
message types live here rather than being hardcoded in capture_node.py, so this
package isn't tied to one nav2 version.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class Watch:
    topic: str
    msg_type: str
    trigger: str


@dataclass
class CaptureConfig:
    bundle_root: Path
    environment_resource: str | None = None
    flush_period_sec: float = 2.0
    buffer_max_size: int = 1000
    buffer_spill_dir: Path | None = None  # resolved to bundle_root/.spill in from_dict
    watches: list[Watch] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "CaptureConfig":
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict) -> "CaptureConfig":
        bundle_root = Path(data["bundle_root"]).expanduser()
        spill_dir = data.get("buffer_spill_dir")
        return cls(
            bundle_root=bundle_root,
            environment_resource=data.get("environment_resource"),
            flush_period_sec=float(data.get("flush_period_sec", 2.0)),
            buffer_max_size=int(data.get("buffer_max_size", 1000)),
            buffer_spill_dir=(
                Path(spill_dir).expanduser() if spill_dir else bundle_root / ".spill"
            ),
            watches=[Watch(**w) for w in data.get("watches", [])],
        )
