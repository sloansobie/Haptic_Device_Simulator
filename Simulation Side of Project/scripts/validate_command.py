#!/usr/bin/env python3
import argparse
import math
import sys
import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64MultiArray


class CommandValidator(Node):
    def __init__(self, command_topic: str):
        super().__init__('hapticdevice_command_validator')
        self._latest_joint_state = None
        self._sub = self.create_subscription(JointState, '/joint_states', self._joint_state_cb, 10)
        self._pub = self.create_publisher(Float64MultiArray, command_topic, 10)

    def _joint_state_cb(self, msg: JointState):
        self._latest_joint_state = msg

    def wait_for_joint_state(self, timeout: float):
        deadline = time.time() + timeout
        while time.time() < deadline:
            rclpy.spin_once(self, timeout_sec=0.5)
            if self._latest_joint_state is not None:
                return self._latest_joint_state
        return None

    def publish_command(self, data):
        msg = Float64MultiArray()
        msg.data = data
        self._pub.publish(msg)


def select_test_command(before: JointState, requested, min_delta: float):
    current = {name: pos for name, pos in zip(before.name, before.position)}
    joints = ['joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6']
    requested_distance = sum(abs(current.get(name, 0.0) - value) for name, value in zip(joints, requested))
    if requested_distance > min_delta:
        return requested
    return [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]


def state_distance(before: JointState, after: JointState) -> float:
    shared = set(before.name) & set(after.name)
    if not shared:
        return 0.0
    before_map = {name: pos for name, pos in zip(before.name, before.position)}
    after_map = {name: pos for name, pos in zip(after.name, after.position)}
    return sum(abs(after_map[name] - before_map[name]) for name in shared)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--command-topic', default='/arm_position_controller/commands')
    parser.add_argument(
        '--command',
        nargs=6,
        type=float,
        default=[0.3, 0.2, 0.04, 0.1, -0.2, 0.1],
    )
    parser.add_argument('--timeout', type=float, default=15.0)
    parser.add_argument('--min-delta', type=float, default=1e-4)
    args = parser.parse_args()

    rclpy.init()
    node = CommandValidator(args.command_topic)
    try:
        before = node.wait_for_joint_state(args.timeout)
        if before is None:
            node.get_logger().error('No /joint_states message received before command.')
            return 1

        command = select_test_command(before, args.command, args.min_delta)
        for _ in range(5):
            node.publish_command(command)
            rclpy.spin_once(node, timeout_sec=0.2)

        deadline = time.time() + args.timeout
        while time.time() < deadline:
            rclpy.spin_once(node, timeout_sec=0.5)
            after = node._latest_joint_state
            if after is not None and state_distance(before, after) > args.min_delta:
                node.get_logger().info('Command validation passed.')
                return 0

        node.get_logger().error('Joint states did not change enough after command publish.')
        return 1
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    sys.exit(main())
