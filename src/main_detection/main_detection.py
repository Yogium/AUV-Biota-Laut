import time
import os
import cv2

# Import modules
from areaCheck import load_boundaries, is_in_area
from areaSetup import area_setup
from dataAcquisition import init_light_control, set_light_control, close_light_control, init_camera, get_camera_frame, close_camera
from preProcess import enhance_underwater_pipeline
from biotaDetection import load_yolo_model, run_yolo_model

# ========================================================
# PATHS AND GLOBAL VARIABLES
# ========================================================

# TensorRT engine path on Jetson AGX Orin
YOLO_ENGINE_PATH = "/home/krbai/coba_yolo_auv/model_yolo11/yolo11n_datasetfinal5/best.engine"
# Output directory
OUTPUT_DIR = "output/main_detection_result_1/"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# PWM value for light
PWM_VAL = 64

# ========================================================
# TELEMETRY (PLACEHOLDER)
# ========================================================
def get_cur_gps():
    # Simulates getting GPS from UDOO
    return -6.87, 107.98

# ========================================================
# MAIN
# ========================================================

def main():
    print("\n" + "="*50)
    print("\nAUV MARINE BIOTA MONITORING SYSTEM")
    print("\n" + "="*50)

    # ========================================================
    # INITIALIZATION
    # ========================================================
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
    cam_ready = init_camera
    if not cam_ready:
        print("[ERROR] Cannot start system without camera")
        return
    
    time.sleep(2)
    
    frame_count = 1
    system_active = False # Initially turned off

    try:
        print("\n[SYSTEM] Entering autonomous navigation loop...")
        while True:
            # Obtain current location
            cur_lat, cur_lon = get_cur_gps()
            
            if is_in_area(cur_lat, cur_lon, bounds):
                if not system_active:
                    print("\n[SYSTEM] AUV is entering monitoring zone. Activating marine biota detection system")
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
                    detect_frame = run_yolo_model(model, enhanced_frame)
                    total_time = time.time() - start_time

                    # Save to disk
                    filename = os.path.join(OUTPUT_DIR, f"data_{frame_count:04d}.jpg")
                    cv2.imwrite(filename, detect_frame)
                    print(f"[SYSTEM] Data {filename} is saved | Processing Time: {total_time:.3f} | {status_msg}")
                    frame_count += 1

            else: # Outside of monitoring zone
                if system_active:
                    print("\n[SYSTEM] AUV is outside of monitoring system. Turning off marine biota monitoring system...")
                    if cboard_ready:
                        set_light_control(0)
                    system_active = False
                
                time.sleep(1) # Sleep briefly
        
    except KeyboardInterrupt:
        print("\n[SYSTEM] System aborted. Initiating shutdown sequence...")
    finally:
        # Thread teardown
        print("[SYTEM] Shutting down hardware...")
        close_camera()
        close_light_control()
        print("[SYSTEM] Shutdown complete")
                
if __name__ == "__main__":
    main()