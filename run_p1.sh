#!/usr/bin/env bash
# ============================================================
#  跑 practical_1（开环 / 闭环）
#  用法：
#    ./run_p1.sh             开环（默认）
#    ./run_p1.sh closed      闭环
#    ./run_p1.sh closed 60   闭环，跑 60 秒
# ============================================================
set -uo pipefail
cd "$(dirname "$0")"

SRC='source /opt/ros/humble/setup.bash; source /home/ros2_ws/install/setup.bash'
MODE="${1:-open}"
RUN_SECONDS="${2:-30}"

EXTRA=""
LABEL="open loop"
if [ "$MODE" = "closed" ]; then
  EXTRA="--ros-args -p closed_loop:=true"
  LABEL="closed loop"
fi

echo ">>> [1/2] 编译 practical_1"
docker exec ros2-dev bash -lc "$SRC; cd /home/ros2_ws && colcon build --symlink-install --packages-select practical_1 2>&1 | tail -3"

echo ">>> [2/2] 运行【${LABEL}】${RUN_SECONDS} 秒（去浏览器看 RViz）"
docker exec ros2-dev bash -lc "$SRC; timeout ${RUN_SECONDS} ros2 run practical_1 practical_1 ${EXTRA} 2>&1 | tail -12"

echo ">>> 结束"
