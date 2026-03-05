#include <memory>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

/*
Based on this minimal publisher/subscriber tutorial:
https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Cpp-Publisher-And-Subscriber.html
*/


class Visualization : public rclcpp::Node
{
public:
  Visualization()
  : Node("visualization")
  {
    // Joint position data retrieval
    auto joint_pos_callback =
      [this](std_msgs::msg::String::UniquePtr msg) -> void {
        RCLCPP_INFO(this->get_logger(), "I heard joint_pos info: '%s'", msg->data.c_str());
      };
    joint_pos_subscription_ =
      this->create_subscription<std_msgs::msg::String>("joint_pos", 10, joint_torque_subscription_);
  }

private:
  // Topic Interaction. TODO: Change the message types as appropriate
  rclcpp::Subscription<std_msgs::msg::String>::SharedPtr joint_pos_subscription_;
  size_t count_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<Visualization>());
  rclcpp::shutdown();
  return 0;
}