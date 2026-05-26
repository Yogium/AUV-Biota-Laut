Header header

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
