cmake_minimum_required(VERSION 3.8)

project(hapticdevice_URDF)

find_package(ament_cmake REQUIRED)

install(DIRECTORY config launch meshes urdf
  DESTINATION share/${PROJECT_NAME}
)

set(PACKAGE_DATA_FILES
  "${CMAKE_CURRENT_SOURCE_DIR}/building_robot.sdf"
)

install(FILES ${PACKAGE_DATA_FILES}
  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS
  scripts/bringup_controllers.py
  scripts/validate_launch.py
  scripts/validate_command.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
