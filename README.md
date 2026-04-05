# Haptic Device Arm in Gazebo with ROS 2 Control

This project launches the `hapticdevice_URDF` arm in Gazebo Sim and controls it through ROS 2 controllers.

The current setup is intended for:

- ROS 2 Humble
- Gazebo Sim / `ros_gz_sim`
- WSL on Windows

## What This Repo Contains

- [`urdf/hapticdevice_URDF.urdf`](c:\Users\sloan\OneDrive - UBC\UBC\Year 4.0\MECH 464\Project\urdf\hapticdevice_URDF.urdf): robot model and `ros2_control` configuration
- [`building_robot.sdf`](c:\Users\sloan\OneDrive - UBC\UBC\Year 4.0\MECH 464\Project\building_robot.sdf): minimal Gazebo world
- [`launch/gazebo_ros2_control.launch.py`](c:\Users\sloan\OneDrive - UBC\UBC\Year 4.0\MECH 464\Project\launch\gazebo_ros2_control.launch.py): main launch file
- [`config/hapticdevice_controllers.yaml`](c:\Users\sloan\OneDrive - UBC\UBC\Year 4.0\MECH 464\Project\config\hapticdevice_controllers.yaml): controller definitions
- [`scripts/bringup_controllers.py`](c:\Users\sloan\OneDrive - UBC\UBC\Year 4.0\MECH 464\Project\scripts\bringup_controllers.py): controller startup helper
- [`scripts/validate_launch.py`](c:\Users\sloan\OneDrive - UBC\UBC\Year 4.0\MECH 464\Project\scripts\validate_launch.py): launch smoke test
- [`scripts/validate_command.py`](c:\Users\sloan\OneDrive - UBC\UBC\Year 4.0\MECH 464\Project\scripts\validate_command.py): motion smoke test

## Required Packages

In WSL, install the ROS 2 / Gazebo packages used by this project:

```bash
source /opt/ros/humble/setup.bash
sudo apt update
sudo apt install -y \
  ros-humble-ros-gz-sim \
  ros-humble-ros2-control \
  ros-humble-ros2-controllers \
  ros-humble-gz-ros2-control
```

## Build

From a WSL terminal:

```bash
cd "/mnt/c/Users/sloan/OneDrive - UBC/UBC/Year 4.0/MECH 464/Project"
source /opt/ros/humble/setup.bash
rm -rf build install log
colcon build --packages-select hapticdevice_URDF
source install/setup.bash
```

## Launch

### Headless

This is the most reliable option in WSL:

```bash
cd "/mnt/c/Users/sloan/OneDrive - UBC/UBC/Year 4.0/MECH 464/Project"
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch hapticdevice_URDF gazebo_ros2_control.launch.py
```

### With GUI

```bash
cd "/mnt/c/Users/sloan/OneDrive - UBC/UBC/Year 4.0/MECH 464/Project"
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch hapticdevice_URDF gazebo_ros2_control.launch.py headless:=false
```

## Validate That The Launch Worked

Open a second WSL terminal:

```bash
cd "/mnt/c/Users/sloan/OneDrive - UBC/UBC/Year 4.0/MECH 464/Project"
source /opt/ros/humble/setup.bash
source install/setup.bash
python3 install/hapticdevice_URDF/lib/hapticdevice_URDF/validate_launch.py --timeout 20
```

Expected result:

```text
Launch validation passed.
```

This checks:

- `/controller_manager` is available
- `joint_state_broadcaster` is active
- `arm_position_controller` is active
- `/arm_position_controller/commands` has a subscriber

## Move The Arm

The arm is controlled through:

```text
/arm_position_controller/commands
```

Publish a 6-value joint command from a second WSL terminal:

```bash
cd "/mnt/c/Users/sloan/OneDrive - UBC/UBC/Year 4.0/MECH 464/Project"
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 topic pub /arm_position_controller/commands std_msgs/msg/Float64MultiArray "{data: [0.5, 0.0, 0.0, 0.0, 0.0, 0.0]}" --once
```

The command order is:

1. `joint1`
2. `joint2`
3. `joint3`
4. `joint4`
5. `joint5`
6. `joint6`

Examples:

Move only `joint1`:

```bash
ros2 topic pub /arm_position_controller/commands std_msgs/msg/Float64MultiArray "{data: [0.5, 0.0, 0.0, 0.0, 0.0, 0.0]}" --once
```

Move only `joint2`:

```bash
ros2 topic pub /arm_position_controller/commands std_msgs/msg/Float64MultiArray "{data: [0.0, 0.5, 0.0, 0.0, 0.0, 0.0]}" --once
```

Move the prismatic joint `joint3`:

```bash
ros2 topic pub /arm_position_controller/commands std_msgs/msg/Float64MultiArray "{data: [0.0, 0.0, 0.04, 0.0, 0.0, 0.0]}" --once
```

## Validate Motion

Run:

```bash
cd "/mnt/c/Users/sloan/OneDrive - UBC/UBC/Year 4.0/MECH 464/Project"
source /opt/ros/humble/setup.bash
source install/setup.bash
python3 install/hapticdevice_URDF/lib/hapticdevice_URDF/validate_command.py --timeout 20
```

Expected result:

```text
Command validation passed.
```

## Typical Workflow

Terminal 1:

```bash
cd "/mnt/c/Users/sloan/OneDrive - UBC/UBC/Year 4.0/MECH 464/Project"
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch hapticdevice_URDF gazebo_ros2_control.launch.py headless:=false
```

Terminal 2:

```bash
cd "/mnt/c/Users/sloan/OneDrive - UBC/UBC/Year 4.0/MECH 464/Project"
source /opt/ros/humble/setup.bash
source install/setup.bash
python3 install/hapticdevice_URDF/lib/hapticdevice_URDF/validate_launch.py --timeout 20
ros2 topic pub /arm_position_controller/commands std_msgs/msg/Float64MultiArray "{data: [0.3, 0.2, 0.04, 0.1, -0.2, 0.1]}" --once
```

## Troubleshooting

### The Gazebo window opens but is blank

Usually this means multiple Gazebo sessions are running at once.

Kill all old sessions:

```bash
pkill -9 -f 'ign gazebo' || true
pkill -9 -f 'ros2 launch hapticdevice_URDF gazebo_ros2_control.launch.py' || true
pkill -9 -f robot_state_publisher || true
pkill -9 -f bringup_controllers.py || true
pkill -9 -f 'controller_manager/spawner' || true
```

Then launch only one new GUI session:

```bash
ros2 launch hapticdevice_URDF gazebo_ros2_control.launch.py headless:=false
```

### `ros2 control list_controllers` crashes with `!rclpy.ok()`

This CLI can be flaky in WSL. Use the provided validator instead:

```bash
python3 install/hapticdevice_URDF/lib/hapticdevice_URDF/validate_launch.py --timeout 20
```

### `Waiting for at least 1 matching subscription(s)...`

The arm controller is not ready yet. Run the launch validator first:

```bash
python3 install/hapticdevice_URDF/lib/hapticdevice_URDF/validate_launch.py --timeout 20
```

Only publish commands after it passes.

### GUI mode does not appear at all

Check your WSL graphics environment:

```bash
echo $DISPLAY
echo $WAYLAND_DISPLAY
echo $XDG_RUNTIME_DIR
```

If those are blank, WSLg is not active in that shell.

## Notes

- The package name `hapticdevice_URDF` does not follow normal ROS 2 lowercase naming conventions, so builds and launches show a warning.
- The project is currently set up around WSL + ROS 2 Humble + Gazebo Sim.
- The arm is configured as a fixed-base robot.
