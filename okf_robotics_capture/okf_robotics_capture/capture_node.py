"""okf_robotics_capture's ROS2 node — the only module in this package that imports
rclpy. Subscribes to the topics declared in capture_params.yaml, routes each message
through the matching trigger -> encoder pair, and hands the result to a non-blocking
buffer drained by an independent background thread.

Safety: disk I/O only ever happens in `_flush_loop`, which runs on its own
`threading.Thread` — not on the rclpy executor thread that processes subscription
callbacks. A slow flush can therefore never delay message reception, matching
requirements.md's Safety & real-time behavior section (non-blocking, buffered, not
drop-on-backpressure — the same hot-buffer/async-flush pattern hermes-okf uses).
"""
from __future__ import annotations

import datetime as dt
import threading
from pathlib import Path

import rclpy
from ament_index_python.packages import get_package_share_directory
from rclpy.node import Node
from rosidl_runtime_py import message_to_ordereddict
from rosidl_runtime_py.utilities import get_message

from okf_robotics_core.bundle import Bundle

from .buffer import HotMemoryBuffer
from .config import CaptureConfig
from .encoders import ENCODERS, MissionEncoder
from .session import CaptureSession
from .triggers import TRIGGERS
from .triggers.base import Event
from .writer import BundleWriter


class CaptureNode(Node):
    def __init__(self):
        super().__init__("okf_robotics_capture")

        self.declare_parameter("config_path", "")
        self.declare_parameter("mission_name", "session")
        config_path = self.get_parameter("config_path").get_parameter_value().string_value
        mission_name = self.get_parameter("mission_name").get_parameter_value().string_value
        if not config_path:
            config_path = str(
                Path(get_package_share_directory("okf_robotics_capture"))
                / "config"
                / "capture_params.yaml"
            )

        self.config = CaptureConfig.from_yaml(config_path)
        self.bundle = Bundle(self.config.bundle_root)
        self.buffer = HotMemoryBuffer(self.config.buffer_max_size, self.config.buffer_spill_dir)
        self.writer = BundleWriter(self.bundle)
        self.session = CaptureSession.start(mission_name, self.config.environment_resource)

        self._mission_encoder = MissionEncoder()
        self._triggers = []

        for watch in self.config.watches:
            trigger_cls = TRIGGERS.get(watch.trigger)
            encoder_cls = ENCODERS.get(watch.trigger)
            if trigger_cls is None or encoder_cls is None:
                self.get_logger().warning(
                    f"unknown trigger '{watch.trigger}', skipping watch on {watch.topic}"
                )
                continue
            trigger = trigger_cls()
            encoder = encoder_cls()
            self._triggers.append(trigger)
            msg_cls = get_message(watch.msg_type)
            self.create_subscription(
                msg_cls,
                watch.topic,
                self._make_callback(watch.topic, watch.msg_type, trigger, encoder),
                10,
            )

        self._emit_mission_event("mission_started")

        # Independent background thread, not a ROS timer — see module docstring.
        self._stop_event = threading.Event()
        self._flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
        self._flush_thread.start()

    def _make_callback(self, topic, msg_type, trigger, encoder):
        def callback(msg):
            # A capture node must never take itself down over one bad message.
            try:
                fields = message_to_ordereddict(msg)
                stamp = dt.datetime.now(dt.timezone.utc).isoformat()
                event = trigger.check(topic, msg_type, fields, stamp)
                if event is None:
                    return
                if event.kind == "task_started":
                    for other in self._triggers:
                        if other is not trigger:
                            other.reset()
                for op in encoder.encode(event, self.session):
                    self.buffer.put(op)
            except Exception as exc:
                self.get_logger().error(f"Failed to process message on {topic}: {exc!r}")

        return callback

    def _emit_mission_event(self, kind: str) -> None:
        stamp = dt.datetime.now(dt.timezone.utc).isoformat()
        event = Event(kind, "", "", stamp, {})
        for op in self._mission_encoder.encode(event, self.session):
            self.buffer.put(op)

    def _flush_loop(self) -> None:
        while not self._stop_event.wait(self.config.flush_period_sec):
            self.writer.flush(self.buffer)

    def destroy_node(self):
        self._emit_mission_event("mission_ended")
        self._stop_event.set()
        self._flush_thread.join(timeout=5.0)
        self.writer.flush(self.buffer)  # catch anything queued during shutdown
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = CaptureNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
