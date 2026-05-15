import json

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
    except Exception as e:
        print(f"[ERROR] Monitoring zone cannot be made: {e}")