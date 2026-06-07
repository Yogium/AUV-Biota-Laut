import json
import math

# Setup the monitoring zone based on input coordinates
def area_setup():
    print("\n[SYSTEM] Configure Monitoring Zone")
    try: 
        # map() applies the float conversion to both coordinates cleanly
        lat1, lon1 = map(float, input("[SYSTEM] Enter Corner 1 Latitude & Longitude (space separated): ").split())
        lat2, lon2 = map(float, input("[SYSTEM] Enter Corner 2 Latitude & Longitude (space separated): ").split())
    except ValueError:
        print("[ERROR] Input must be decimal numbers separated by a space.")
        return
    
    bounds = {
        "min_lat": min(lat1, lat2),
        "max_lat": max(lat1, lat2),
        "min_lon": min(lon1, lon2),
        "max_lon": max(lon1, lon2)
    }

    try:
        with open("m_bounds.json", "w") as outfile:
            json.dump(bounds, outfile, indent=4)
        print("[SYSTEM] Monitoring zone is saved to m_bounds.json")
    except Exception as err:
        print(f"[ERROR] Monitoring zone cannot be made: {err}")

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