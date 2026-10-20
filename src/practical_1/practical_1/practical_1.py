#!/usr/bin/env python3
import math

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry


class Practical1(Node):

    def __init__(self):
        super().__init__('practical_1_node')

        # Publisher: send velocity commands to /cmd_vel (the "throttle")
        self.publisher_ = self.create_publisher(Twist, 'cmd_vel', 10)

        # Subscriber: receive /odom (used by closed loop; kept in open loop too)
        self.create_subscription(Odometry, 'odom', self.odom_callback, 10)

        # Timer: runs every 0.1 s (the "brain")
        self.timer_period = 0.1
        self.timer = self.create_timer(self.timer_period, self.timer_callback)

        # Command-line parameter: whether to use closed loop
        self.declare_parameter('closed_loop', False)
        self.use_closed_loop = self.get_parameter('closed_loop').value

        # Speed parameters
        self.linear_speed = 0.2        # forward speed, m/s
        self.angular_speed = 1.57      # turning speed, rad/s

        # Timing parameters (open loop)
        self.straight_time = 5.0       # 1 m / 0.2 m/s = 5 s
        self.turn_time = 0.999         # 90 deg turn (tuned)
        self.elapsed = 0.0             # time spent in the current leg

        # Measured values (closed loop, updated in odom_callback)
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0

        # State machine
        self.state = 'straight'        # 'straight' / 'turn' / 'stop'
        self.legs_done = 0             # sides completed so far
        self.total_legs = 4            # four sides in total

        # Reference points for each leg (closed loop)
        self.x0 = 0.0                  # start point of the current straight leg
        self.y0 = 0.0
        self.yaw0 = 0.0                # heading at the start of the current turn
        self.initialized = False       # record the real start on the first odometry

    def odom_callback(self, msg):
        # Position: read directly
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y

        # Orientation: convert the quaternion (x, y, z, w) to a yaw angle
        q = msg.pose.pose.orientation
        self.yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                              1.0 - 2.0 * (q.y * q.y + q.z * q.z))

        # On the first odometry message, save the current position as the start
        # of the first straight leg (the robot may not start at the origin).
        if not self.initialized:
            self.x0 = self.x
            self.y0 = self.y
            self.initialized = True

    def timer_callback(self):
        msg = Twist()
        self.elapsed += self.timer_period     # accumulate time first

        # ================== straight ==================
        if self.state == 'straight':
            msg.linear.x = self.linear_speed

            # End condition: closed loop checks distance, open loop checks time
            if self.use_closed_loop:
                done = math.hypot(self.x - self.x0, self.y - self.y0) >= 1.0
            else:
                done = self.elapsed >= self.straight_time

            if done:
                self.elapsed = 0.0
                self.yaw0 = self.yaw          # remember the turn's start heading
                self.state = 'turn'

        # ================== turn ==================
        elif self.state == 'turn':
            if self.use_closed_loop:
                # Closed loop: turn until 90 deg is reached. Normalise the angle
                # difference first (handles wrapping at +/-180 deg).
                diff = math.atan2(math.sin(self.yaw - self.yaw0),
                                  math.cos(self.yaw - self.yaw0))
                remaining = math.pi / 2 - abs(diff)
                if remaining <= -0.01:        # 90 deg reached (small tuning offset)
                    self._finish_turn()
                else:
                    # Slow down near the target to avoid overshooting
                    msg.angular.z = max(0.15, min(self.angular_speed,
                                                  3.0 * remaining))
            else:
                # Open loop: turn for turn_time seconds
                msg.angular.z = self.angular_speed
                if self.elapsed >= self.turn_time:
                    self._finish_turn()

        # ================== stop ==================
        else:
            msg.linear.x = 0.0
            msg.angular.z = 0.0

        self.publisher_.publish(msg)
        self.get_logger().info(
            'mode=%-6s state=%-8s x=%.2f y=%.2f yaw=%.1f'
            % ('closed' if self.use_closed_loop else 'open',
               self.state, self.x, self.y, math.degrees(self.yaw)))

    def _finish_turn(self):
        """End of a turn: count the side, remember the next leg's start, choose next state."""
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
