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

# TensorRT engine path on Jetson AGX Orin
YOLO_ENGINE_PATH = "/home/krbai/coba_yolo_auv/model_yolo11/yolo11n_datasetfinal5/best.engine"
# Output directory
# OUTPUT_DIR = "output/main_detection_result_1/"
# os.makedirs(OUTPUT_DIR, exist_ok=True)

# PWM value for light
PWM_VAL = 64

# Time interval
TIME_INTERVAL = 1.5

# Mission settings
VEHICLE_ID = "auv01"
MISSION_ID = "ms01"

# WebSocket settings
WS_URL = ""

# ========================================================
# TELEMETRY (PLACEHOLDER)
# ========================================================
def get_cur_gps():
    # Simulates getting GPS from UDOO
    return 6.87, 7.98, 12.5

# ========================================================
# MAIN
# ========================================================

def main():
    print("\n" + "="*50)
    print("\nAUV MARINE BIOTA MONITORING SYSTEM")
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
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
    
    time.sleep(2)
    
    frame_count = 1
    system_active = False # Initially turned off

    try:
        print("[SYSTEM] Entering autonomous navigation loop...")
        while True:
            # Obtain current location
            cur_lat, cur_lon, cur_depth = get_cur_gps()
            
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
                    detect_frame, detections, filename = run_yolo_model(model, enhanced_frame, frame_count, VEHICLE_ID, MISSION_ID)
                    total_time = time.time() - start_time

                    # Save to disk
                    # filepath = os.path.join(OUTPUT_DIR, filename)
                    # cv2.imwrite(filepath, detect_frame)

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
                            "filename": filename    
                        }
                        detect_data.append(row)

                    # Encode images (preprocessed and detected)
                    _, buffer_enh = cv2.imencode('.jpg', enhanced_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
                    _, buffer_det = cv2.imencode('.jpg', detect_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 100])

                    b64_enhanced = base64.b64encode(buffer_enh).decode('utf-8')
                    b64_detected = base64.b64encode(buffer_det).decode('utf-8')

                    # Build TCP payload
                    ws_message = {
                        "metadata": detect_data,
                        "images": {
                            "preprocessed": b64_enhanced,
                            "detected": b64_detected
                        }
                    }

                    # Send over to websocket
                    try:
                        ws.send(json.dumps(ws_message))
                        print(f"[SYSTEM] Data sent via WebSocket")
                    except Exception as e:
                        print(f"[ERROR] Sending data failed: {e}")

                    print(f"[SYSTEM] Data {filename} is saved | Processing Time: {total_time:.3f} | {status_msg}")
                    frame_count += 1

                    # Add time interval
                    time.sleep(TIME_INTERVAL)
                else:
                    print("[ERROR] Failed to grab frame from camera hardware")
                    time.sleep(1)

            else: # Outside of monitoring zone
                if system_active:
                    print("[SYSTEM] AUV is outside of monitoring system. Turning off marine biota monitoring system...")
                    if cboard_ready:
                        set_light_control(0)
                    system_active = False
                
                time.sleep(1) # Sleep briefly
        
    except KeyboardInterrupt:
        print("[SYSTEM] System aborted. Initiating shutdown sequence...")
    finally:
        # Thread teardown
        print("[SYSTEM] Shutting down hardware...")
        close_camera()
        close_light_control()
        print("[SYSTEM] Shutdown complete")
                
if __name__ == "__main__":
    main()