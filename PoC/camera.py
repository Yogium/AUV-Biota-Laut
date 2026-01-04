import camera_test
import cv2
import os
import time

def setup_camera():
    """Find and initialize camera"""
    print("Setting up camera...")
    cameras = camera_test.find_cameras()
    
    if not cameras:
        print("No cameras found!")
        return None
    
    camera_index = cameras[0]
    print(f"Using camera at index {camera_index}")
    
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("Failed to open camera")
        return None
    
    print("Camera initialized successfully")
    return cap

def capture_images_loop(duration=None, interval=1.5):
    """
    Capture images every interval seconds
    
    Args:
        duration: Total duration in seconds (None = infinite)
        interval: Time between captures in seconds (default 1.5)
    """
    # Create captured_images folder if it doesn't exist
    output_dir = "captured_images"
    os.makedirs(output_dir, exist_ok=True)
    print(f"Images will be saved to: {os.path.abspath(output_dir)}")
    
    # Setup camera
    cap = setup_camera()
    if cap is None:
        return
    
    try:
        start_time = time.time()
        capture_count = 0
        auv_number = "AUV01"
        mission_number = "MS001"
        
        print(f"Starting image capture every {interval} seconds...")
        print("Press Ctrl+C to stop\n")
        
        while True:
            # Check if duration exceeded
            if duration and (time.time() - start_time) > duration:
                print(f"Duration of {duration} seconds reached")
                break
            
            ret, frame = cap.read()
            if ret:
                # Generate filename with AUV, mission, and image number
                capture_count += 1
                filename = os.path.join(output_dir, f"{auv_number}_{mission_number}_{capture_count:06d}.jpg")
                
                # Save image
                cv2.imwrite(filename, frame)
                capture_count += 1
                print(f"[{capture_count}] Saved: {filename}")
            else:
                print("Failed to read frame")
                break
            
            # Wait for interval
            time.sleep(interval)
    
    except KeyboardInterrupt:
        print(f"\nCapture stopped. Total images captured: {capture_count}")
    finally:
        cap.release()
        print("Camera released")

if __name__ == "__main__":
    # Capture images for 60 seconds at 1.5 second intervals
    # Or set duration=None for infinite capture until Ctrl+C
    capture_images_loop(duration=10, interval=1.5)
