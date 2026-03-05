cmake_minimum_required(VERSION 3.8)
project(haptic_sim_pkg)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
# uncomment the following section in order to fill in
# further dependencies manually.
# find_package(<dependency> REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)

# Add Node executables
# User Controller
add_executable(user_controller src/User_Controller/user_controller.cpp)
ament_target_dependencies(user_controller rclcpp std_msgs)

# Capstone Controller
add_executable(capstone_controller src/Capstone_Controller/capstone_controller.cpp)
ament_target_dependencies(capstone_controller rclcpp std_msgs)

# Simulator
add_executable(simulator src/Simulator/simulator.cpp)
ament_target_dependencies(simulator rclcpp std_msgs)

# Visualization
add_executable(visualization src/Visualization/visualization.cpp)
ament_target_dependencies(visualization rclcpp std_msgs)

install(TARGETS
  user_controller
  capstone_controller
  simulator
  visualization
  DESTINATION lib/${PROJECT_NAME})



if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
