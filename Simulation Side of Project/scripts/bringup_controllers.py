#!/usr/bin/env python3
import argparse
import subprocess
import sys
import time

import rclpy
from builtin_interfaces.msg import Duration
from controller_manager_msgs.srv import ListControllers, SwitchController
from rclpy.node import Node


class ControllerProbe(Node):
    def __init__(self, controller_manager: str):
        super().__init__('hapticdevice_controller_probe')
        base = controller_manager.rstrip("/")
        self._client = self.create_client(
            ListControllers,
            f'{base}/list_controllers',
        )
        self._switch_client = self.create_client(
            SwitchController,
            f'{base}/switch_controller',
        )

    def wait_for_manager(self, timeout: float) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            list_ready = self._client.wait_for_service(timeout_sec=1.0)
            switch_ready = self._switch_client.wait_for_service(timeout_sec=1.0)
            if list_ready and switch_ready:
                return True
        return False

    def get_state(self, controller_name: str, timeout: float = 5.0):
        request = ListControllers.Request()
        future = self._client.call_async(request)
        rclpy.spin_until_future_complete(self, future, timeout_sec=timeout)
        result = future.result()
        if result is None:
            return None
        for controller in result.controller:
            if controller.name == controller_name:
                return controller.state
        return None

    def wait_for_state(self, controller_name: str, states, timeout: float):
        deadline = time.time() + timeout
        while time.time() < deadline:
            state = self.get_state(controller_name)
            if state in states:
                return state
            time.sleep(0.5)
        return self.get_state(controller_name)

    def activate(self, controller_name: str, timeout: float) -> bool:
        request = SwitchController.Request()
        request.activate_controllers = [controller_name]
        request.strictness = 2
        request.activate_asap = True
        request.timeout = Duration(sec=int(timeout), nanosec=int((timeout % 1) * 1e9))
        future = self._switch_client.call_async(request)
        rclpy.spin_until_future_complete(self, future, timeout_sec=timeout)
        result = future.result()
        return bool(result and result.ok)


def run_spawner(
    controller_name: str,
    controller_manager: str,
    controllers_file: str,
    timeout: float,
    probe: ControllerProbe,
    *,
    inactive: bool = False,
) -> None:
    cmd = [
        'ros2',
        'run',
        'controller_manager',
        'spawner',
        controller_name,
        '--controller-manager',
        controller_manager,
        '--param-file',
        controllers_file,
        '--controller-manager-timeout',
        str(timeout),
        '--service-call-timeout',
        str(timeout),
        '--switch-timeout',
        str(timeout),
    ]
    if inactive:
        cmd.append('--inactive')
    result = subprocess.run(cmd, check=False, text=True, capture_output=True)
    target_states = {'inactive', 'active'} if inactive else {'active', 'inactive'}
    state = probe.wait_for_state(controller_name, target_states, timeout)
    if result.returncode == 0 and state in target_states:
        return
    if state in target_states:
        return

    if result.stdout:
        sys.stderr.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)
    raise subprocess.CalledProcessError(result.returncode, cmd)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--controller-manager', default='/controller_manager')
    parser.add_argument('--controllers-file', required=True)
    parser.add_argument('--timeout', type=float, default=120.0)
    args, _ = parser.parse_known_args()

    rclpy.init()
    probe = ControllerProbe(args.controller_manager)
    try:
        if not probe.wait_for_manager(args.timeout):
            print('controller_manager service not available.', file=sys.stderr)
            return 1

        run_spawner(
            'joint_state_broadcaster',
            args.controller_manager,
            args.controllers_file,
            args.timeout,
            probe,
        )
        if probe.wait_for_state('joint_state_broadcaster', {'active'}, args.timeout) != 'active':
            if not probe.activate('joint_state_broadcaster', args.timeout):
                print('Failed to activate joint_state_broadcaster.', file=sys.stderr)
                return 1
            if probe.wait_for_state('joint_state_broadcaster', {'active'}, args.timeout) != 'active':
                print('joint_state_broadcaster did not reach active.', file=sys.stderr)
                return 1
        run_spawner(
            'arm_position_controller',
            args.controller_manager,
            args.controllers_file,
            args.timeout,
            probe,
            inactive=True,
        )
        if probe.wait_for_state('arm_position_controller', {'inactive', 'active'}, args.timeout) not in {'inactive', 'active'}:
            print('arm_position_controller did not reach an inactive/active state.', file=sys.stderr)
            return 1
        if probe.wait_for_state('arm_position_controller', {'active'}, 1.0) != 'active':
            if not probe.activate('arm_position_controller', args.timeout):
                print('Failed to activate arm_position_controller.', file=sys.stderr)
                return 1
            if probe.wait_for_state('arm_position_controller', {'active'}, args.timeout) != 'active':
                print('arm_position_controller did not reach active.', file=sys.stderr)
                return 1
        return 0
    except subprocess.CalledProcessError as exc:
        return exc.returncode or 1
    finally:
        probe.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    sys.exit(main())
