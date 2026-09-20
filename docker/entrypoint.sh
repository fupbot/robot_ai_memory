#!/bin/bash
set -e

source "/opt/ros/${ROS_DISTRO}/setup.bash"

# The repo is bind-mounted at /workspace/src/robot_ai_memory, so dependencies
# declared in package.xml are (re-)resolved on every start to pick up edits
# made on the host since the image was built.
if [ -d /workspace/src ]; then
  rosdep install --from-paths /workspace/src --ignore-src -r -y
fi

if [ -f /workspace/install/setup.bash ]; then
  source /workspace/install/setup.bash
fi

exec "$@"
