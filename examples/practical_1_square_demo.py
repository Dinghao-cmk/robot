#!/usr/bin/env python3
"""
【学习示范 · 不要提交】

这是"让机器人走边长 1 米的正方形"的一个示范实现，放在 ref/ 里只为你理解思路。
你自己的 practical_1.py 请自己写，并且要能解释每一行。

思路：一个"状态机"。
定时器每 0.1 秒触发一次，每次根据"当前处于哪个状态"发布不同的速度：

    直行5秒  →  转1秒  →  直行5秒  →  转1秒
    →  直行5秒  →  转1秒  →  直行5秒  →  转1秒  →  停

共 4 条边 + 4 个 90° 转弯。
- 直行：linear.x = 0.2 m/s，走 1 米需要 1 / 0.2 = 5 秒
- 转弯：angular.z = π/2 rad/s，转 90°(π/2 rad) 需要 1 秒
- 用 'elapsed' 记录"当前这段已经过了多久"，'legs_done' 记录"已走完几条边"
"""

import math

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist


class SquareDemo(Node):

    def __init__(self):
        super().__init__('square_demo')

        # 发布者：往 /cmd_vel 发速度指令
        self.publisher_ = self.create_publisher(Twist, 'cmd_vel', 10)

        # 每 0.1 秒决策一次
        self.timer_period = 0.1
        self.timer = self.create_timer(self.timer_period, self.timer_callback)

        # 速度参数
        self.linear_speed = 0.2             # m/s
        self.angular_speed = math.pi / 2    # rad/s ≈ 1.5708

        # 每段要持续的时间 = 距离 / 速度
        self.straight_time = 1.0 / self.linear_speed            # 1m → 5s
        self.turn_time = 0.963  # 90° → 1s

        # 状态机变量
        self.state = 'straight'   # 'straight' / 'turn' / 'stop'
        self.elapsed = 0.0        # 当前这段已经过了多久
        self.legs_done = 0        # 已经走完几条边
        self.total_legs = 4       # 一共走 4 条边

    def timer_callback(self):
        msg = Twist()
        self.elapsed += self.timer_period     # 先累加时间

        if self.state == 'straight':
            msg.linear.x = self.linear_speed  # 直行：只给前进速度
            if self.elapsed >= self.straight_time:
                self.state = 'turn'           # 走够 1 米 → 准备转弯
                self.elapsed = 0.0

        elif self.state == 'turn':
            msg.angular.z = self.angular_speed   # 转弯：只给角速度
            if self.elapsed >= self.turn_time:
                self.legs_done += 1              # 一条边走完
                self.elapsed = 0.0
                if self.legs_done >= self.total_legs:
                    self.state = 'stop'          # 4 条边走完 → 停
                else:
                    self.state = 'straight'      # 否则继续走下一条边

        else:  # 'stop'
            msg.linear.x = 0.0
            msg.angular.z = 0.0

        self.publisher_.publish(msg)
        self.get_logger().info(
            'state=%-8s linear.x=%.2f angular.z=%.2f'
            % (self.state, msg.linear.x, msg.angular.z))


def main(args=None):
    rclpy.init(args=args)
    node = SquareDemo()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
