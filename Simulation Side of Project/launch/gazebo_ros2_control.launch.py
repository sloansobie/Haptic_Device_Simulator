from pathlib import Path
import shutil
import tempfile

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo, OpaqueFunction, RegisterEventHandler, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.event_handlers import OnProcessExit
from launch_ros.actions import Node


def _launch_setup(context, *args, **kwargs):
    pkg_share = Path(get_package_share_directory('hapticdevice_URDF'))
    gz_sim_launch = Path(get_package_share_directory('ros_gz_sim')) / 'launch' / 'gz_sim.launch.py'
    urdf_template = pkg_share / 'urdf' / 'hapticdevice_URDF.urdf'
    controllers_source = pkg_share / 'config' / 'hapticdevice_controllers.yaml'
    mesh_source_dir = pkg_share / 'meshes'
    robot_name = LaunchConfiguration('robot_name').perform(context)
    startup_timeout = LaunchConfiguration('startup_timeout').perform(context)

    robot_description = urdf_template.read_text(encoding='utf-8')
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as tmp:
        tmp.write(controllers_source.read_text(encoding='utf-8'))
        controllers_file = Path(tmp.name)

    mesh_dir = Path(tempfile.mkdtemp(prefix='hapticdevice_meshes_'))
    shutil.copytree(mesh_source_dir, mesh_dir, dirs_exist_ok=True)

    robot_description = robot_description.replace('__HAPTICDEVICE_CONTROLLERS_FILE__', controllers_file.as_posix())
    robot_description = robot_description.replace('package://hapticdevice_URDF/meshes', mesh_dir.as_posix())

    with tempfile.NamedTemporaryFile(mode='w', suffix='.urdf', delete=False, encoding='utf-8') as tmp:
        tmp.write(robot_description)
        generated_urdf = tmp.name

    world_path = Path(LaunchConfiguration('world').perform(context))
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sdf', delete=False, encoding='utf-8') as tmp:
        generated_world = Path(tmp.name)
    shutil.copyfile(world_path, generated_world)
    world_name = LaunchConfiguration('world_name').perform(context)
    headless = LaunchConfiguration('headless').perform(context).lower() in ('1', 'true', 'yes', 'on')
    gz_args = f'-r -s {generated_world}' if headless else str(generated_world)

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[
            {'robot_description': robot_description},
            {'use_sim_time': True},
        ],
    )

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        name='spawn_hapticdevice',
        output='screen',
        arguments=[
            '-name', robot_name,
            '-allow_renaming', 'false',
            '-world', world_name,
            '-x', LaunchConfiguration('x').perform(context),
            '-y', LaunchConfiguration('y').perform(context),
            '-z', LaunchConfiguration('z').perform(context),
            '-R', LaunchConfiguration('roll').perform(context),
            '-P', LaunchConfiguration('pitch').perform(context),
            '-Y', LaunchConfiguration('yaw').perform(context),
            '-file', generated_urdf,
        ],
    )

    controller_bringup = Node(
        package='hapticdevice_URDF',
        executable='bringup_controllers.py',
        name='hapticdevice_controller_bringup',
        output='screen',
        arguments=[
            '--controller-manager', '/controller_manager',
            '--controllers-file', controllers_file.as_posix(),
            '--timeout', startup_timeout,
        ],
    )

    return [
        LogInfo(
            msg=(
                f'Launching hapticdevice_URDF in {"headless" if headless else "GUI"} mode '
                f'with staged assets in {controllers_file.parent} and world {world_path.name}.'
            )
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(gz_sim_launch)),
            launch_arguments={
                'gz_args': gz_args,
            }.items(),
        ),
        robot_state_publisher,
        spawn_robot,
        RegisterEventHandler(
            OnProcessExit(
                target_action=spawn_robot,
                on_exit=[controller_bringup],
            )
        ),
    ]


def generate_launch_description():
    pkg_share = Path(get_package_share_directory('hapticdevice_URDF'))

    return LaunchDescription([
        DeclareLaunchArgument(
            'world',
            default_value=str(pkg_share / 'building_robot.sdf'),
            description='SDF world file to launch in Gazebo Sim.',
        ),
        DeclareLaunchArgument(
            'world_name',
            default_value='arm_world',
            description='Name of the world inside the SDF file.',
        ),
        DeclareLaunchArgument('robot_name', default_value='hapticdevice_URDF'),
        DeclareLaunchArgument('x', default_value='0.0'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument('z', default_value='0.15'),
        DeclareLaunchArgument('roll', default_value='0.0'),
        DeclareLaunchArgument('pitch', default_value='0.0'),
        DeclareLaunchArgument('yaw', default_value='0.0'),
        DeclareLaunchArgument(
            'startup_timeout',
            default_value='120',
            description='Seconds to wait for controller-manager readiness and controller activation.',
        ),
        DeclareLaunchArgument(
            'headless',
            default_value='true',
            description='Run Gazebo without the GUI to avoid WSL OGRE rendering crashes.',
        ),
        SetEnvironmentVariable('LIBGL_ALWAYS_SOFTWARE', '1'),
        OpaqueFunction(function=_launch_setup),
    ])
