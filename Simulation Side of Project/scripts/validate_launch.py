#!/usr/bin/env python3
import argparse
import sys
import time

import rclpy
from controller_manager_msgs.srv import ListControllers
from rclpy.node import Node


class LaunchValidator(Node):
    def __init__(self, controller_manager: str, command_topic: str):
        super().__init__('hapticdevice_launch_validator')
        self._client = self.create_client(
            ListControllers,
            f'{controller_manager.rstrip("/")}/list_controllers',
        )
        self._command_topic = command_topic

    def wait_for_manager(self, timeout: float) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self._client.wait_for_service(timeout_sec=1.0):
                return True
        return False

    def get_controllers(self):
        req = ListControllers.Request()
        future = self._client.call_async(req)
        rclpy.spin_until_future_complete(self, future, timeout_sec=5.0)
        if not future.done() or future.result() is None:
            return {}
        return {controller.name: controller.state for controller in future.result().controller}

    def has_command_subscriber(self) -> bool:
        return self.count_subscribers(self._command_topic) > 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--controller-manager', default='/controller_manager')
    parser.add_argument('--command-topic', default='/arm_position_controller/commands')
    parser.add_argument('--timeout', type=float, default=30.0)
    args = parser.parse_args()

    rclpy.init()
    node = LaunchValidator(args.controller_manager, args.command_topic)
    try:
        if not node.wait_for_manager(args.timeout):
            node.get_logger().error('controller_manager service not available.')
            return 1

        expected = {
            'joint_state_broadcaster': 'active',
            'arm_position_controller': 'active',
        }

        deadline = time.time() + args.timeout
        while time.time() < deadline:
            controllers = node.get_controllers()
            states_ok = all(controllers.get(name) == expected_state for name, expected_state in expected.items())
            subscriber_ok = node.has_command_subscriber()
            if states_ok and subscriber_ok:
                node.get_logger().info('Launch validation passed.')
                return 0
            rclpy.spin_once(node, timeout_sec=0.5)
            time.sleep(0.5)

        controllers = node.get_controllers()
        for name, expected_state in expected.items():
            actual = controllers.get(name)
            if actual != expected_state:
                node.get_logger().error(f'{name} expected {expected_state}, got {actual!r}.')
                return 1
        if not node.has_command_subscriber():
            node.get_logger().error(f'No subscriber on {args.command_topic}.')
            return 1
        return 1
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    sys.exit(main())
