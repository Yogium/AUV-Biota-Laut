# Initial state
geometry_msgs/Point initial_position
float64 initial_yaw
float64 initial_surge
bool use_initial_yaw

# Final state
geometry_msgs/Point final_position
float64 final_yaw
float64 final_surge
bool use_final_yaw

# Flag to consider z as altitude
bool altitude_mode

# Final waypoint tolerance (LOS only)
geometry_msgs/Point tolerance