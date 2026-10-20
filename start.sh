#!/usr/bin/env bash
# ============================================================
#  一键启动整个仿真环境（Linux / Ubuntu）
#  前提：已安装 Docker（sudo apt install docker.io docker-compose-v2）
#  用法：./start.sh
# ============================================================
set -uo pipefail
cd "$(dirname "$0")"

SRC='source /opt/ros/humble/setup.bash; source /home/ros2_ws/install/setup.bash'
PREFIX=/home/ros2_ws/install/turtlebot3_gazebo/share/turtlebot3_gazebo

if ! command -v docker >/dev/null 2>&1; then
  echo "❌ 没装 Docker。请先运行："
  echo "   sudo apt update && sudo apt install -y docker.io docker-compose-v2"
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "❌ Docker 没运行，或当前用户没有权限。试试："
  echo "   sudo systemctl start docker"
  echo "   sudo usermod -aG docker \$USER   # 然后重新登录"
  exit 1
fi

echo "[1/5] 启动容器（首次会拉镜像，几个 GB，请耐心）..."
docker compose up -d
sleep 5

echo "[2/5] 首次编译工作区（第一次需要几分钟）..."
docker exec ros2-dev bash -lc 'if [ ! -f /home/ros2_ws/install/setup.bash ]; then bash /usr/local/bin/setup.sh; fi'

echo "[3/5] 启动 Gazebo ..."
docker exec ros2-dev bash -lc "pkill -9 -f gzserver; pkill -9 -f gzclient; pkill -9 -f 'ros2 launch'; sleep 1; true" >/dev/null 2>&1 || true
docker exec -d ros2-dev bash -lc "$SRC; ros2 launch turtlebot3_gazebo empty_world.launch.py > /tmp/launch.log 2>&1"
sleep 45

echo "[4/5] 确认机器人已就位 ..."
if ! docker exec ros2-dev bash -lc "grep -q 'Successfully spawned' /tmp/launch.log"; then
  echo "    (首次没成功，补放一次)"
  docker exec ros2-dev bash -lc "$SRC; ros2 run gazebo_ros spawn_entity.py -entity waffle -file $PREFIX/models/turtlebot3_waffle/model.sdf -x 0 -y 0 -z 0.01 2>&1 | tail -1"
fi

echo "[5/5] 启动 RViz（看机器人和轨迹）..."
docker cp rviz/odom_path.py ros2-dev:/tmp/odom_path.py
docker cp rviz/path.rviz ros2-dev:/tmp/path.rviz
docker exec -d ros2-dev bash -lc "$SRC; python3 /tmp/odom_path.py > /tmp/path.log 2>&1"
docker exec -d ros2-dev bash -lc "$SRC; rviz2 -d /tmp/path.rviz > /tmp/rviz.log 2>&1"

echo ""
echo "✅ 就绪！"
echo "   浏览器打开：http://localhost:8080/vnc.html  然后点 Connect"
echo "   看 RViz 窗口：灰色的是机器人，红线是走过的轨迹"
