# Encodes the information from a GPS receiver.

Header header

int32 fix_quality
int32 FIX_NONE = 0
int32 FIX_GPS  = 1
int32 FIX_DGPS = 2
int32 FIX_PPS = 3

DecimalLatLon global_position
float32 altitude

# Horizontal dilution of precision.
float32 hdop

# UTC time from the GPS receiver
time gps_time

float64 latitude

float64 longitude
