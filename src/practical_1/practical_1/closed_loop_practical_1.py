#!/usr/bin/env python3
import math       

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist     
from nav_msgs.msg import Odometry      


class ClosedLoopDemo(Node):

    def __init__(self):
        super().__init__('closed_loop_demo')

        self.publisher_ = self.create_publisher(Twist, 'cmd_vel', 10)

        self.create_subscription(Odometry, 'odom', self.odom_callback, 10)

        self.timer_period = 0.1
        self.timer = self.create_timer(self.timer_period, self.timer_callback)

        self.linear_speed = 0.2      
        self.angular_speed = 1.57      

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

        if self.state == 'straight':
            msg.linear.x = self.linear_speed      

            if math.hypot(self.x - self.x0, self.y - self.y0) >= 1.0:
                self.yaw0 = self.yaw
                self.state = 'turn'

        elif self.state == 'turn':
            diff = math.atan2(math.sin(self.yaw - self.yaw0),
                              math.cos(self.yaw - self.yaw0))

            remaining = math.pi / 2 - abs(diff)

            if remaining <= 0.05:
                self.legs_done += 1
                self.x0 = self.x
                self.y0 = self.y
                if self.legs_done >= self.total_legs:
                    self.state = 'stop'
                else:
                    self.state = 'straight'
            else:
                msg.angular.z = max(0.15, min(self.angular_speed,
                                              3.0 * remaining))

        else:
            msg.linear.x = 0.0
            msg.angular.z = 0.0

        self.publisher_.publish(msg)

        self.get_logger().info(
            'state=%-8s x=%.2f y=%.2f yaw=%.1f'
            % (self.state, self.x, self.y, math.degrees(self.yaw)))


def main(args=None):
    rclpy.init(args=args)
    node = ClosedLoopDemo()
    rclpy.spin(node)     
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
