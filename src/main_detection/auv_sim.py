import math
import random

METER_PER_DEGREE = 111133 # meter/degree in latitude
WAVE_AMPLITUDE = 0.05 # 5cm of wave
SENSOR_NOISE = 0.02 # 2cm of jitter

# Obtain the closest corner from areaSetup.py to initiate target coordinate
def get_closest_corner(lat, lon, bounds):
    corners = [
        (bounds['min_lat'], bounds['min_lon']), # Bottom-Left
        (bounds['max_lat'], bounds['min_lon']), # Top-Left
        (bounds['min_lat'], bounds['max_lon']), # Bottom-Right
        (bounds['max_lat'], bounds['max_lon'])  # Top-Right
    ]

    # Calculate closest corner
    closest_corner = min(corners, key=lambda c: math.hypot(c[0] - lat, c[1] - lon))
    return closest_corner

# Simulate AUV movement from initial location to closest corner
def simulate_auv(cur_coord, bounds, speed, active, step_time, delay):
    cur_lat, cur_lon, cur_dep = cur_coord
    # Obtain closest corner
    end_lat, end_lon = get_closest_corner(cur_lat, cur_lon, bounds)
    
    # Calculate total distance and direction vector
    dist_left = math.hypot(end_lat - cur_lat, end_lon - cur_lon)
    if dist_left == 0:
        return "INACTIVE", cur_lat, cur_lon, cur_dep
    
    dir_lat = (end_lat - cur_lat) / dist_left
    dir_lon = (end_lon - cur_lon) / dist_left

    # Add wave drift by adding perpendicular vector (cross track error)
    perp_lat = -dir_lon
    perp_lon = dir_lat

    dist_meters = speed * delay
    speed_degree = dist_meters / METER_PER_DEGREE

    if active:
        if dist_left <= speed_degree:
            # Reached destination
            cur_lat, cur_lon = end_lat, end_lon
            active = False
        else:
            # Move towards destination
            cur_lat += dir_lat * speed_degree
            cur_lon += dir_lon * speed_degree

            # Apply noise
            # Wave drift
            wave_amp = WAVE_AMPLITUDE / METER_PER_DEGREE
            wave_drift = math.sin(step_time) * wave_amp
            # Sensor noise
            noise_sensor = random.gauss(mu=0, sigma=SENSOR_NOISE/METER_PER_DEGREE)

            # Calculate final coordinate
            cur_lat += (perp_lat * wave_drift) + noise_sensor
            cur_lon += (perp_lon * wave_drift) + noise_sensor

        # Output
        status_msg = "ACTIVE" if active else "INACTIVE"

        return status_msg, cur_lat, cur_lon, cur_dep