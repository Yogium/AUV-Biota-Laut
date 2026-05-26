Header header

# Basic navigation status
float64 latitude
float64 longitude
float32 depth
float32 altitude
float32 heading
bool at_surface

# Safety
float32 up_time
bool vehicle_initialized
bool water_detected
float32 battery_charge
float32 battery_voltage
float32[] internal_temperature

# Safety: data age
float32 navigation_data_age
float32 imu_data_age
float32 depth_data_age
float32 altitude_data_age
float32 dvl_data_age
float32 dvl_valid_data_age
float32 gps_data_age
float32 modem_data_age
float32 wifi_data_age

# Thrusters enabled
bool thrusters_enabled

# Running controller
uint8 CONTROLLER_NONE = 0
uint8 CONTROLLER_WAYPOINT = 1
uint8 CONTROLLER_SECTION = 2
uint8 CONTROLLER_PARK = 3
uint8 active_controller
bool altitude_mode

# Active Mode 
uint8 MANUAL = 0
uint8 STABILIZE = 1
uint8 DEPTH_HOLD = 2
uint8 AUG = 3
uint8 AUV = 4
uint8 HUG = 5
uint8 GUIDED = 6
uint8 SURFACE = 7
uint8 RTH = 8
uint8 mode_status

# Mission status
bool mission_active
int32 current_step
int32 total_steps
