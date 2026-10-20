import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry, Path
from geometry_msgs.msg import PoseStamped


class OdomPath(Node):
    def __init__(self):
        super().__init__('odom_path')
        self.path = Path()
        self.path.header.frame_id = 'odom'
        self.pub = self.create_publisher(Path, 'robot_path', 10)
        self.create_subscription(Odometry, 'odom', self.cb, 10)
        self.create_timer(0.5, self.publish)

    def cb(self, msg):
        ps = PoseStamped()
        ps.header.stamp = msg.header.stamp
        ps.header.frame_id = 'odom'
        ps.pose = msg.pose.pose
        self.path.poses.append(ps)
        if len(self.path.poses) > 20000:
            self.path.poses = self.path.poses[-20000:]

    def publish(self):
        self.path.header.stamp = self.get_clock().now().to_msg()
        self.pub.publish(self.path)


def main():
    rclpy.init()
    n = OdomPath()
    try:
        rclpy.spin(n)
    except KeyboardInterrupt:
        pass
    finally:
        n.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
