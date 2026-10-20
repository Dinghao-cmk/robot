# COMP4034 — TurtleBot3 正方形行驶（开环 / 闭环）

一个自包含的 ROS 2 仿真项目：**克隆下来，在 Ubuntu 上一条命令就能跑**。

- ROS 2 Humble + Gazebo + TurtleBot3（全部跑在 Docker 容器里）
- 图形界面通过 noVNC 显示在浏览器（无需本机装 ROS / Gazebo）
- `practical_1`：开环（计时）与闭环（里程计实测）两版，参数切换

---

## 前提

只需要 **Docker**（Ubuntu 原生，不是 Docker Desktop）：

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2
sudo systemctl start docker
sudo usermod -aG docker $USER      # 执行后重新登录（或重启）
```

首次启动会拉取镜像（几个 GB），需要能访问 `ghcr.io`。

---

## 快速开始

```bash
git clone <本仓库地址>
cd comp4034-robot
bash start.sh
```

等它打印 `✅ 就绪！`，然后浏览器打开：

**http://localhost:8080/vnc.html** → 点 **Connect**

你会看到 RViz 窗口：灰色的是机器人，红色的是它走过的轨迹。

---

## 运行代码

```bash
bash run_p1.sh             # 开环（计时）
bash run_p1.sh closed      # 闭环（用 odom 修正漂移）
bash run_p1.sh closed 60   # 闭环，跑 60 秒
```

**开环 vs 闭环**

| | 直线结束条件 | 转弯结束条件 |
|---|---|---|
| 开环 | 走满 5 秒 | 转满 `turn_time` 秒 |
| 闭环 | 实测距离 ≥ 1 m | 实测角度 ≥ 90° |

开环会漂移（正方形合不拢）；闭环用 `/odom` 实测修正，正方形能闭合。

---

## 项目结构

```
comp4034-robot/
├── docker-compose.yml   # noVNC + ROS2/Gazebo 两个容器
├── start.sh             # 一键启动环境
├── run_p1.sh            # 跑开环 / 闭环
├── rviz/                # RViz 配置 + 轨迹记录节点
├── src/practical_1/     # 你的 ROS 2 包（代码在 practical_1/practical_1.py）
└── README.md
```

---

## 代码在哪

`src/practical_1/practical_1/practical_1.py`

核心：一个 `Practical1` 节点 + 状态机（straight / turn / stop），
用参数 `closed_loop` 切换开环 / 闭环。

---

## 常见问题

| 现象 | 解决 |
|---|---|
| `docker: command not found` | 没装 Docker，见上面"前提" |
| `permission denied` | `sudo usermod -aG docker $USER` 后**重新登录** |
| 首次启动很慢 | 正常，在拉镜像（几 GB） |
| 浏览器打不开 8080 | 等 `start.sh` 打印"就绪"；或 `docker compose ps` 看容器是否在跑 |
| 看不到机器人 | 看 **RViz** 窗口（不是 Gazebo），滚轮可以放大 |
| 机器人不动 | `docker logs ros2-dev` 看报错；确认 Gazebo 已启动 |
| 想彻底重来 | `docker compose down -v`（会清掉编译缓存） |

---

## 停止

```bash
docker compose down
```
