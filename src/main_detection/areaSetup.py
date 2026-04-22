import json

# ========================================================
# MONITORING ZONE SETUP
# ========================================================

# Area Setup Function
def area_setup():
    print("[SYSTEM] Configure Monitoring Zone")
    try: 
        lat1, lon1 = float(input("Enter Corner 1 Latitude & Longitude: ").split())
        lat2, lon2 = float(input("Enter Corner 2 Latitude & Longitude: ").split())
    except ValueError:
        print("[ERROR] Input must be in decimal")
        return
    
    # Determine boundary limits
    bounds = {
        "min_lat": min(lat1, lat2),
        "max_lat": max(lat1, lat2),
        "min_lon": min(lon1, lon2),
        "max_lon": max(lon1, lon2)
    }

    # Store boundary in JSON file
    try:
        with open("m_bounds.json", "w") as outfile:
            json.dump(bounds, outfile, indent=4)
        print("\n[SYSTEM] Monitoring zone is saved to m_bounds.json")
    except Exception as err:
        print(f"\n[ERROR] Monitoring zone cannot be made: {err}")
    
    return