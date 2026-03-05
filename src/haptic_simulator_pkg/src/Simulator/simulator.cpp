#include <memory>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

/*
Based on this minimal publisher/subscriber tutorial:
https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Cpp-Publisher-And-Subscriber.html
*/


class Simulator : public rclcpp::Node
{
public:
  Simulator()
  : Node("simulator")
  {
    // Joint torque data retrieval
    auto joint_torque_callback =
      [this](std_msgs::msg::String::UniquePtr msg) -> void {
        RCLCPP_INFO(this->get_logger(), "I heard joint_torque info: '%s'", msg->data.c_str());
      };
    joint_torque_subscription_ =
      this->create_subscription<std_msgs::msg::String>("joint_torque", 10, joint_torque_subscription_);
    

    // Publish joint position data
    joint_pos_publisher_ = this->create_publisher<std_msgs::msg::String>("joint_pos", 10);
    auto timer_callback =
      [this]() -> void {
        auto message = std_msgs::msg::String();
        message.data = "Fake joint_pos data from sim: " + std::to_string(this->count_++);
        RCLCPP_INFO(this->get_logger(), "Publishing: '%s'", message.data.c_str());
        this->joint_torque_publisher_->publish(message);
      };
    
    // Timer to create test data
    timer_ = this->create_wall_timer(500ms, timer_callback);
  }

private:
  // Topic Interaction. TODO: Change the message types as appropriate
  rclcpp::Subscription<std_msgs::msg::String>::SharedPtr joint_torque_subscription_;
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr joint_pos_publisher_;
  // Timer
  rclcpp::TimerBase::SharedPtr timer_;
  size_t count_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<Simulator>());
  rclcpp::shutdown();
  return 0;
}