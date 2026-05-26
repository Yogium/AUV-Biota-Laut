Header header

bool estimation_ok
# Error value of estimation_ok is false.
int32 error_num
# int32 ERROR_...

# Rest of message valid if estimation_ok is true.

# Duration of time the motion occurred over.
std_msgs/Duration motion_duration 

# Relative vehicle motion, in ROS right-handed coordinate frame
# (forward, left, up position, quaternion rotation).
geometry_msgs/Pose pose_change

# TODO: Possibly include integrated position, e.g. visual_odom->base_link
