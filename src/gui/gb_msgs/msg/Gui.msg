# dvl #
float32 velocity_x
float32 velocity_y
float32 velocity_z

float32 velocity_u
float32 velocity_v
float32 velocity_w

float32 dvl_roll
float32 dvl_pitch
float32 dvl_yaw

float32 altitude

float32 surge # resultan kecepatan

# alti #
float32 depth_data

# imu #
float32 roll_data
float32 pitch_data
float32 yaw_data
float32 roll_rate_data
float32 pitch_rate_data
float32 yaw_rate_data

# gps #
float64 lat
float64 long
int32 gps_status

# navigasi #
float32 navigasi_north
float32 navigasi_east
float32 navigasi_depth
float32 navigasi_u
float32 navigasi_v
float32 navigasi_w

# kompartemen 4 #
# INA219 #
float32 voltage
float32 current
# SHT31 #
float32 humidity
float32 temperature
# MS5803 #
float32 pressure
float32 temperature2

# moving mass #
# pitch #
float32 pitch_sp
float32 des_mm
float32 cur_mm
# roll #
float32 roll_sp
int32 servo_position

# buoyancy engine #
float32 desired_internal_volume
float32 internal_volume
float32 pressure_be
float32 depth_rate
float32 depth_sp
float32 netral_volume

# bow thruster #
float32 yaw_sp
float32 bow_percentage
float32 stern_percentage
float32 surge_percentage
float32 surge_sp
