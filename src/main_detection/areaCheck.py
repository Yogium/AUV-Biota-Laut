import json

# Load boundary coordinates from JSON config file
def load_boundaries(filename="m_bounds.json"):
    try:
        with open(filename, "r") as infile:
            bounds = json.load(infile)
            print(f"[SYSTEM] Boundaries loaded from {filename}")
            return bounds
    except FileNotFoundError:
        print(f"[ERROR] File {filename} is not found")
        return None
    except json.JSONDecodeError:
        print(f"[ERROR] File {filename} is corrupted")
        return None

# Check if AUV is inside area
def is_in_area(cur_lat, cur_lon, bounds):
    if bounds is None:
        return False
    
    in_lat = bounds["min_lat"] <= cur_lat <= bounds["max_lat"]
    in_lon = bounds["min_lon"] <= cur_lon <= bounds["max_lon"]

    return in_lat and in_lon # True if coordinate is inside bounding box