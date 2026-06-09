import time
import base64
import cv2
import socket
import json
import subprocess
import os
import getpass
import sys

# Import modules
from areaCheck import load_boundaries, is_in_area
from areaSetup import area_setup
from dataAcquisition import init_light_control, set_light_control, close_light_control, init_camera, get_camera_frame, close_camera
from preProcess import enhance_underwater_pipeline
from biotaDetection import load_yolo_model, run_yolo_model
from auv_sim import simulate_auv
from imageStorage import save_image_local

# Database execution
DB_SERVER_EXEC = "./main_database.out"

# WebSocket settings
TCP_IP = "127.0.0.1"
TCP_PORT = 8080
ROS_IP = "192.168.2.102"
ROS_PORT = 9191

# ========================================================
# SETUP
# ========================================================
CONFIG_PATH = "setup.json"

try:
    with open(CONFIG_PATH, 'r') as setup:
        config = json.load(setup)
except Exception as e:
    print(f"[ERROR] Failed to load {CONFIG_PATH}")
    sys.exit(1) # Abort mission

# YOLO engine path
YOLO_ENGINE_PATH = config.get("engine_path")
# PWM value
PWM_VAL = config.get("pwm_val")
# Time intervals
MONITOR_INTERVAL = config.get("monitor_interval")
NAV_INTERVAL = config.get("nav_interval")
# Mission settings
VEHICLE_ID = f"auv{config.get("vehicle_id"):02d}"
MISSION_ID = f"auv{config.get("mission_id"):02d}"
INIT_COORD = tuple(config.get("init_coord"))
AUV_SPEED = config.get("auv_speed")
NAV_ACTIVE = config.get("nav_active")
CONF_THRES = config.get("conf_threshold")

# ========================================================
# MAIN
# ========================================================

def main():
    print("\n" + "="*50)
    print("\n       AUV MARINE BIOTA MONITORING SYSTEM")
    print("\n" + "="*50)

    # Monitoring zone setup using areaSetup
    area_setup()

    # Load monitoring zone
    bounds = load_boundaries("m_bounds.json")
    if not bounds:
        print("[ERROR] Cannot start mission without monitoring zone")
        return
    
    # Initialize YOLO model
    model = load_yolo_model(YOLO_ENGINE_PATH)

    # Initialize hardware
    cboard_ready = init_light_control()
    if not cboard_ready:
        print("[WARNING] Camera Lighting Control Board not detected. Running system without light control")
    
    # Initialize camera thread
    cam_ready = init_camera()
    if not cam_ready:
        print("[ERROR] Cannot start system without camera")
        return
    
    # Initialize database server
    db_process = None
    if os.path.exists(DB_SERVER_EXEC):
        print("\n[SYSTEM] Database Initialization")
        db_password = getpass.getpass(prompt="Enter the C++ Database password: ")

        print(f"[SYSTEM] Starting C++ database server: {DB_SERVER_EXEC}")
        try:
            db_process = subprocess.Popen([DB_SERVER_EXEC], stdin=subprocess.PIPE, text=True)
            db_process.stdin.write(db_password+'\n')
            db_process.stdin.flush()
            time.sleep(2) #give time to initialize db
        except Exception as e:
            print(f"[ERROR] Failed to start C++ server {e}")
    else:
        print(f"[ERROR] C++ executeable not found at {DB_SERVER_EXEC}.")

    # Initialize websocket client
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((TCP_IP, TCP_PORT))
        print("[SYSTEM] Connected via WebSocket")
    except Exception as err:
        print(f"[ERROR] Connection failed: {err}")
    
    time.sleep(2)
    
    frame_count = 1
    total_rows = 0
    system_active = False # Initially turned off

    try:
        print("[SYSTEM] Entering autonomous navigation loop...")
        # Iniitialization
        step_time = 0
        cur_coord = INIT_COORD
        while NAV_ACTIVE:
            # Determine loop delay
            cur_delay = MONITOR_INTERVAL if system_active else NAV_INTERVAL # Navigation updates every half second
            # Obtain current location
            status_msg, cur_lat, cur_lon, cur_depth = simulate_auv(cur_coord, bounds, AUV_SPEED, NAV_ACTIVE, step_time, cur_delay)
            # Update current coordinate
            cur_coord = (cur_lat, cur_lon, cur_depth)
            
            if is_in_area(cur_lat, cur_lon, bounds):
                if not system_active:
                    print("[SYSTEM] AUV is entering monitoring zone. Activating marine biota detection system")
                    if cboard_ready:
                        set_light_control(PWM_VAL)
                    system_active = True
                
                # Fetch frame directly
                raw_frame = get_camera_frame()

                # Data pipeline
                if raw_frame is not None:
                    # Preprocess
                    start_time = time.time()
                    enhanced_frame, status_msg = enhance_underwater_pipeline(raw_frame)

                    # YOLO Detection
                    detect_frame, detections, filename = run_yolo_model(model, CONF_THRES, enhanced_frame, frame_count, VEHICLE_ID, MISSION_ID)
                    total_time = time.time() - start_time

                    # Obtain current time
                    cur_time = time.strftime("%H:%M:%S")

                    # Append detection data to JSON
                    detect_data = []
                    for det in detections:
                        row = {
                            "ID": det["ID"],
                            "time": cur_time,
                            "lat": cur_lat,
                            "lon": cur_lon,
                            "depth": cur_depth,
                            "label": det["label"],
                            "confidence": det["confidence"],
                            "flag": det["flag"],
                            "filename": filename    
                        }
                        detect_data.append(row)

                    # Encode images (preprocessed and detected)
                    _, buffer_enh = cv2.imencode('.jpg', enhanced_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                    _, buffer_det = cv2.imencode('.jpg', detect_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])

                    b64_enhanced = base64.b64encode(buffer_enh).decode('utf-8')
                    save_image_local(enhanced_frame, filename, subfolder="preprocessed")
                    b64_detected = base64.b64encode(buffer_det).decode('utf-8')
                    save_image_local(detect_frame, filename, subfolder="bounding_box")

                    # Build JSON message sent through TCP
                    ws_message = {
                        "filename": filename,
                        "metadata": detect_data,
                        "images": {
                            "preprocessed": b64_enhanced,
                            "detected": b64_detected
                        }
                    }

                    # Send over to websocket
                    try:
                        tcp_message = json.dumps(ws_message) + "\n"
                        sock.sendall(tcp_message.encode('utf-8'))
                        #counter for how many rows of data is sent
                        total_rows += len(detect_data)
                        print(f"[SYSTEM] Data {filename} is sent via WebSocket | Processing Time: {total_time:.3f}")
                    
                    except Exception as e:
                        print(f"[ERROR] Failed to send {filename}: {e}")

                    frame_count += 1
                else:
                    print("[ERROR] Failed to grab frame from camera hardware")

            else: # Outside of monitoring zone
                if system_active:
                    print("[SYSTEM] AUV is outside of monitoring system. Turning off marine biota monitoring system...")
                    if cboard_ready:
                        set_light_control(0)
                    system_active = False
                # Print current position
                print(f"[SYSTEM] En route to target position. Current position: ({cur_lat:.6f}, {cur_lon:.6f})")
            
            # Add step time and delay
            step_time += 1
            time.sleep(cur_delay)

            if status_msg == "INACTIVE":
                print("[SYSTEM] AUV has reached target position")
        
    except KeyboardInterrupt:
        print("\n[SYSTEM] System aborted. Initiating shutdown sequence...")
    finally:
        # Shutting down system
        print("[SYSTEM] Shutting down hardware...")
        close_camera()
        close_light_control()
        if 'sock' in locals():
            sock.close()

        # Shuts down C++ server
        if 'db_process' in locals() and db_process is not None:
            print("[SYSTEM] Terminating C++ Database Server...")
            db_process.terminate()
            db_process.wait() 
        print(f"[SYSTEM] Total rows of data sent to database: {total_rows}")
        print("[SYSTEM] Shutdown complete")
                
if __name__ == "__main__":
    main()
