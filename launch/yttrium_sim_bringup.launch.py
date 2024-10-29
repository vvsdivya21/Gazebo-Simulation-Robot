import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from launch_ros.actions import Node, SetParameter
from launch.launch_description_sources import PythonLaunchDescriptionSource
import xacro


def generate_launch_description():
    ld = LaunchDescription()


    # Specify the name of the package and path to xacro file within the package
    pkg_name = 'yttrium_description'
    file_subpath = 'urdf/yttrium.urdf.xacro'
    # Include the launch file from another package
    included_launch = IncludeLaunchDescription(
    PythonLaunchDescriptionSource([get_package_share_directory('coursework2'), '/launch', '/sim_bringup.launch.py'])
    )

    # Use xacro to process the file
    xacro_file = os.path.join(get_package_share_directory(pkg_name),file_subpath)
    robot_description_raw = xacro.process_file(xacro_file).toxml()

 
    # Run the spawner node from the gazebo_ros package. The entity name doesn't really matter if you only have a single robot.
    node_spawn_entity = Node(package='ros_gz_sim', executable='create',
                        arguments=['-topic', '/robot_description',
                                   '-z', '0.5'],
                        output='screen')

    # robot state publisher node
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description_raw}] # add other parameters here if required
    )
    # Bridge
    # https://github.com/gazebosim/ros_gz/tree/humble/ros_gz_bridge
    node_ros_gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=  [
                    '/clock'                           + '@rosgraph_msgs/msg/Clock'   + '[' + 'ignition.msgs.Clock',
                    '/model/yttrium/cmd_vel'  + '@geometry_msgs/msg/Twist'   + '@' + 'ignition.msgs.Twist',
                    '/model/yttrium/odometry' + '@nav_msgs/msg/Odometry'     + '[' + 'ignition.msgs.Odometry',
                    '/model/yttrium/scan'     + '@sensor_msgs/msg/LaserScan' + '[' + 'ignition.msgs.LaserScan',
                    '/model/yttrium/tf'       + '@tf2_msgs/msg/TFMessage' + '[' + 'ignition.msgs.Pose_V',
                    '/model/yttrium/imu'      + '@sensor_msgs/msg/Imu'       + '[' + 'ignition.msgs.IMU',
                    '/world/empty/model/yttrium/joint_state' + '@sensor_msgs/msg/JointState' + '[' + 'ignition.msgs.Model',
                    '/model/yttrium/depth' + '@sensor_msgs/msg/Image' + '[' + 'ignition.msgs.Image',
                    ],
        parameters= [{'qos_overrides./yttrium.subscriber.reliability': 'reliable'}],
        remappings= [
                    ('/model/yttrium/cmd_vel',  '/cmd_vel'),
                    ('/model/yttrium/odometry', '/odom_raw'   ),
                    ('/model/yttrium/scan',     '/scan'   ),
                    ('/model/yttrium/depth', '/depth'), 
                    ('/model/yttrium/tf',       '/tf'     ),
                    ('/model/yttrium/imu',      '/imu_raw'),     
                    ('/world/empty/model/yttrium/joint_state', 'joint_states')
                    ],
        output='screen'
    )


    # Twist Mux node
    node_twist_mux = Node(
    package='twist_mux',
    executable='twist_mux',
    name='twist_mux',
    output='screen',
    parameters=[os.path.join(get_package_share_directory('yttrium_description'), 'config', 'twist_mux.yaml')]
)


    # Add actions to LaunchDescription
    ld.add_action(SetParameter(name='use_sim_time', value=True))
    ld.add_action(included_launch)
    ld.add_action(node_spawn_entity)
    ld.add_action(node_robot_state_publisher)
    ld.add_action(node_twist_mux)
    ld.add_action(node_ros_gz_bridge)
   

    return ld
