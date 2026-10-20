#!/usr/bin/env python3
"""
=====================================================================
【闭环版 · 学习示范 · 不要提交】
=====================================================================

一句话理解整份代码：
  机器人每 0.1 秒被"叫醒"一次（timer_callback）。
  每次醒来就问自己："我现在处于哪一步？这一步走完了没有？"
  判断"走完没有"靠的是 /odom 实测（位置 + 朝向），而不是数秒数 —— 这就是"闭环"。

整个程序像一台只有 3 个档位的机器：
  'straight'（直行） → 'turn'（转弯） → 'straight' → … 重复 4 遍 → 'stop'

=====================================================================
"""

import math          # 数学函数：atan2、hypot、sin、cos、pi

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist     # 速度指令（我们发给 /cmd_vel）
from nav_msgs.msg import Odometry       # 里程计（我们从 /odom 收）


class ClosedLoopDemo(Node):

    def __init__(self):
        # 给节点起个名字，之后 ros2 node list 里能看到它
        super().__init__('closed_loop_demo')

        # ---- 1. 发布者：往 /cmd_vel 发速度指令（这是"油门"）----
        self.publisher_ = self.create_publisher(Twist, 'cmd_vel', 10)

        # ---- 2. 订阅者：收 /odom，每收到一帧就调用一次 odom_callback ----
        self.create_subscription(Odometry, 'odom', self.odom_callback, 10)

        # ---- 3. 定时器：每 0.1 秒调用一次 timer_callback（"大脑"）----
        self.timer_period = 0.1
        self.timer = self.create_timer(self.timer_period, self.timer_callback)

        # ---- 4. 速度参数 ----
        self.linear_speed = 0.2        # 直行速度：米/秒
        self.angular_speed = 1.57      # 转弯角速度：弧度/秒（≈90°/秒）

        # ---- 5. 实测值（由 odom_callback 持续刷新）----
        #     这些是"机器人此刻在哪、朝哪"的实时数据
        self.x = 0.0                   # 当前 x 坐标
        self.y = 0.0                   # 当前 y 坐标
        self.yaw = 0.0                 # 当前朝向角（弧度，范围 -π ~ π）

        # ---- 6. 状态机 + 每一段的"起点参照" ----
        self.state = 'straight'        # 当前状态：'straight' / 'turn' / 'stop'
        self.legs_done = 0             # 已经走完几条边
        self.total_legs = 4            # 一共走 4 条边（正方形）

        self.x0 = 0.0                  # 当前这条直线的起点 x
        self.y0 = 0.0                  # 当前这条直线的起点 y
        self.yaw0 = 0.0                # 当前这个转弯的起点朝向

        self.initialized = False       # 还没收到第一帧 odom

    # ============================================================
    # odom_callback：每收到一帧 /odom 就执行一次
    # 作用：把里程计数据"翻译"成三个好用的数 —— x、y、yaw
    # ============================================================
    def odom_callback(self, msg):
        # 位置：直接读出来就行
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y

        # 朝向：odom 给的是"四元数"(x, y, z, w)，不是直观角度，要换算成 yaw
        q = msg.pose.pose.orientation
        # 下面这行是"四元数 → yaw"的标准公式，背下来直接用即可
        self.yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                              1.0 - 2.0 * (q.y * q.y + q.z * q.z))

        # 第一次收到 odom 时，把当前位置记成"第一条直线的起点"。
        # 为什么：机器人不一定从 (0,0) 出发；如果写死 0，第一条边会算错。
        if not self.initialized:
            self.x0 = self.x
            self.y0 = self.y
            self.initialized = True

    # ============================================================
    # timer_callback：每 0.1 秒执行一次 —— 整个程序的"大脑"
    # 作用：根据当前状态，决定"下一瞬间发什么速度"
    # ============================================================
    def timer_callback(self):
        msg = Twist()                  # 每次新建一个空的速度指令

        # ================== 状态 1：直行 ==================
        if self.state == 'straight':
            msg.linear.x = self.linear_speed        # 发前进速度

            # 闭环判定：从这条直线的起点 (x0, y0) 到现在 (x, y)，
            #           距离够 1 米了吗？
            # math.hypot(dx, dy) = √(dx² + dy²)，就是"勾股定理求距离"
            if math.hypot(self.x - self.x0, self.y - self.y0) >= 1.0:
                # 走够 1 米了 → 记下"转弯的起点朝向"，然后切到转弯
                self.yaw0 = self.yaw
                self.state = 'turn'

        # ================== 状态 2：转弯 ==================
        elif self.state == 'turn':
            # 先算：从转弯起点 yaw0 转到现在 yaw，一共转了多少角度？
            # 不能直接相减：角度会跨 ±180°（例如 179° 到 -179° 实际只差 2°，
            # 但直接相减得到 -358°）。atan2(sin, cos) 这一手就是把角度差
            # 拉回 [-180°, 180°]，避免这个坑。
            diff = math.atan2(math.sin(self.yaw - self.yaw0),
                              math.cos(self.yaw - self.yaw0))

            # 还差多少弧度才到 90°（π/2）
            remaining = math.pi / 2 - abs(diff)

            if remaining <= -0.01:
                # 转够了（-0.01 = 转过 90° 再多转约 0.6° 才停，
                #          是你调的：觉得转弯偏小就把它改更负）→ 这条边完成
                self.legs_done += 1
                # 记下"下一条直线的起点"
                self.x0 = self.x
                self.y0 = self.y
                # 4 条边都走完就停；否则继续直行
                if self.legs_done >= self.total_legs:
                    self.state = 'stop'
                else:
                    self.state = 'straight'
            else:
                # 还没转够：发角速度继续转。
                # 小技巧：快接近 90° 时减速（min 那部分），避免"冲过头"；
                #         max(0.15, ...) 保证最慢也有 0.15，不至于停死。
                msg.angular.z = max(0.15, min(self.angular_speed,
                                              3.0 * remaining))

        # ================== 状态 3：停止 ==================
        else:
            msg.linear.x = 0.0
            msg.angular.z = 0.0

        # 把这条速度指令发出去（机器人收到才动）
        self.publisher_.publish(msg)

        # 打印当前状态，方便在终端里观察
        self.get_logger().info(
            'state=%-8s x=%.2f y=%.2f yaw=%.1f'
            % (self.state, self.x, self.y, math.degrees(self.yaw)))


def main(args=None):
    rclpy.init(args=args)
    node = ClosedLoopDemo()
    rclpy.spin(node)        # 一直运行，直到被 Ctrl+C 打断
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
