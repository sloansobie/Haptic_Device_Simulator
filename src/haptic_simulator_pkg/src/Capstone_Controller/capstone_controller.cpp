#include <memory>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

/*
Based on this minimal publisher/subscriber tutorial:
https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Cpp-Publisher-And-Subscriber.html

This is where Edwin + Kyle's capstone functionality can be implemented.

NOTE: In this implementation, raw joint poisition and joint position are assumed to be the same topic, so
the capstone controller only subscribes to the topic, and does not publish any joint position data.
*/


class CapstoneController : public rclcpp::Node
{
public:
  CapstoneController()
  : Node("capstone_controller")
  {
    // Setpoint data retrieval
    auto setpoint_callback =
      [this](std_msgs::msg::String::UniquePtr msg) -> void {
        RCLCPP_INFO(this->get_logger(), "I heard setpoint info: '%s'", msg->data.c_str());
      };
    setpoint_subscription_ =
      this->create_subscription<std_msgs::msg::String>("setpoint", 10, setpoint_callback);
    
    // Joint position data retrieval
    auto joint_pos_callback =
      [this](std_msgs::msg::String::UniquePtr msg) -> void {
        RCLCPP_INFO(this->get_logger(), "I heard joint_pos info: '%s'", msg->data.c_str());
      };
    joint_pos_subscription_ =
      this->create_subscription<std_msgs::msg::String>("joint_pos", 10, joint_pos_callback);

    // Publish joint torque data
    joint_torque_publisher_ = this->create_publisher<std_msgs::msg::String>("joint_torque", 10);
    auto timer_callback =
      [this]() -> void {
        auto message = std_msgs::msg::String();
        message.data = "Fake joint_torque data from capstone: " + std::to_string(this->count_++);
        RCLCPP_INFO(this->get_logger(), "Publishing: '%s'", message.data.c_str());
        this->joint_torque_publisher_->publish(message);
      };
    
    // Timer to create test data
    timer_ = this->create_wall_timer(500ms, timer_callback);
  }

private:
  // Topic interaction TODO: Change the message types as appropriate
  rclcpp::Subscription<std_msgs::msg::String>::SharedPtr setpoint_subscription_;
  rclcpp::Subscription<std_msgs::msg::String>::SharedPtr joint_pos_subscription_;
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr joint_torque_publisher_;

  // Timer
  rclcpp::TimerBase::SharedPtr timer_;
  size_t count_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<CapstoneController>());
  rclcpp::shutdown();
  return 0;
}