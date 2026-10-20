#!/usr/bin/env python3
import math

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry


class Practical1(Node):

    def __init__(self):
        super().__init__('practical_1_node')

        self.publisher_ = self.create_publisher(Twist, 'cmd_vel', 10)

        self.create_subscription(Odometry, 'odom', self.odom_callback, 10)

        self.timer_period = 0.1
        self.timer = self.create_timer(self.timer_period, self.timer_callback)

        self.declare_parameter('closed_loop', False)
        self.use_closed_loop = self.get_parameter('closed_loop').value

        self.linear_speed = 0.2        
        self.angular_speed = 1.57      

        self.straight_time = 5.0   
        self.turn_time = 0.963       
        self.elapsed = 0.0           

        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0

        self.state = 'straight'     
        self.legs_done = 0        
        self.total_legs = 4      

        self.x0 = 0.0               
        self.y0 = 0.0
        self.yaw0 = 0.0              
        self.initialized = False       

    def odom_callback(self, msg):
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y

        q = msg.pose.pose.orientation
        self.yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                              1.0 - 2.0 * (q.y * q.y + q.z * q.z))
      
        if not self.initialized:
            self.x0 = self.x
            self.y0 = self.y
            self.initialized = True

    def timer_callback(self):
        msg = Twist()
        self.elapsed += self.timer_period   

        if self.state == 'straight':
            msg.linear.x = self.linear_speed

            if self.use_closed_loop:
                done = math.hypot(self.x - self.x0, self.y - self.y0) >= 1.0
            else:
                done = self.elapsed >= self.straight_time

            if done:
                self.elapsed = 0.0
                self.yaw0 = self.yaw          
                self.state = 'turn'

        elif self.state == 'turn':
            if self.use_closed_loop:
                diff = math.atan2(math.sin(self.yaw - self.yaw0),
                                  math.cos(self.yaw - self.yaw0))
                remaining = math.pi / 2 - abs(diff)
                if remaining <= -0.01:      
                    self._finish_turn()
                else:
                    msg.angular.z = max(0.15, min(self.angular_speed,
                                                  3.0 * remaining))
            else:
                msg.angular.z = self.angular_speed
                if self.elapsed >= self.turn_time:
                    self._finish_turn()

        else:
            msg.linear.x = 0.0
            msg.angular.z = 0.0

        self.publisher_.publish(msg)
        self.get_logger().info(
            'mode=%-6s state=%-8s x=%.2f y=%.2f yaw=%.1f'
            % ('closed' if self.use_closed_loop else 'open',
               self.state, self.x, self.y, math.degrees(self.yaw)))

    def _finish_turn(self):
        self.legs_done += 1
        self.elapsed = 0.0
        self.x0 = self.x
        self.y0 = self.y
        if self.legs_done >= self.total_legs:
            self.state = 'stop'
        else:
            self.state = 'straight'


def main(args=None):
    rclpy.init(args=args)
    node = Practical1()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
