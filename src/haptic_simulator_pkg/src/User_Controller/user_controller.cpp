#include <chrono>
#include <memory>
#include <string>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

using namespace std::chrono_literals;

/*
Based on this minimal publisher/subscriber tutorial:
https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Cpp-Publisher-And-Subscriber.html
*/

class UserController : public rclcpp::Node
{
public:
  UserController()
  : Node("user_controller"), count_(0)
  {
    setpoint_publisher_ = this->create_publisher<std_msgs::msg::String>("setpoint", 10);
    auto timer_callback =
      [this]() -> void {
        auto message = std_msgs::msg::String();
        message.data = "Fake setpoint data from user: " + std::to_string(this->count_++);
        RCLCPP_INFO(this->get_logger(), "Publishing: '%s'", message.data.c_str());
        this->setpoint_publisher_->publish(message);
      };
    // Timer to create test data
    timer_ = this->create_wall_timer(500ms, timer_callback);
  }

private:
  // Topic Interaction TODO: Change the message types as appropriate
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr setpoint_publisher_;
  // Timer
  rclcpp::TimerBase::SharedPtr timer_;
  size_t count_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<UserController>());
  rclcpp::shutdown();
  return 0;
}