import time
import base64
import cv2
import websocket
import json

# Import modules
from areaCheck import load_boundaries, is_in_area
from areaSetup import area_setup
from dataAcquisition import init_light_control, set_light_control, close_light_control, init_camera, get_camera_frame, close_camera
from preProcess import enhance_underwater_pipeline
from biotaDetection import load_yolo_model, run_yolo_model
from auv_sim import simulate_auv

# TensorRT engine path on Jetson AGX Orin
YOLO_ENGINE_PATH = "/home/krbai/acquisition/biotadetect_11.engine"

# PWM value for light
PWM_VAL = 64

# Time interval
MONITOR_INTERVAL = 1.5
NAV_INTERVAL = 0.2

# Mission settings
VEHICLE_ID = "auv01"
MISSION_ID = "ms01"
INIT_COORD = -7.701000, 108.654000, -5
AUV_SPEED = 2.0 # m/s
NAV_ACTIVE = True # Active

# Confidence threshold
CONF_THRES = 0.6

# WebSocket settings
WS_URL = "ws://localhost:8080"

# ========================================================
# MAIN
# ========================================================

def main():
    print("\n" + "="*50)
    print("\n    AUV MARINE BIOTA MONITORING SYSTEM")
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
    
    # Initialize websocket client
    ws = websocket.WebSocket()
    try:
        ws.connect(WS_URL)
        print("[SYSTEM] Connected via WebSocket")
    except Exception as err:
        print(f"[ERROR] Connection failed: {err}")
    
    time.sleep(2)
    
    frame_count = 1
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

                    # Append data
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
                    b64_detected = base64.b64encode(buffer_det).decode('utf-8')

                    # Build TCP payload
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
                        ws.send(json.dumps(ws_message))
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
        print("[SYSTEM] System aborted. Initiating shutdown sequence...")
    finally:
        # Shutting down system
        print("[SYSTEM] Shutting down hardware...")
        close_camera()
        close_light_control()
        # if 'ws' in locals and ws.connected():
        #     ws.close()
        print("[SYSTEM] Shutdown complete")
                
if __name__ == "__main__":
    main()