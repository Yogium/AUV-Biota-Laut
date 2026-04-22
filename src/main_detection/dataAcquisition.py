import serial
import time
import cv2
import threading
import queue

# ========================================================
# HARDWARE PARAMETERS
# ========================================================

ARDUINO_PORT = '/dev/ttyUSB0' 
BAUD_RATE = 9600
CAMERA_INDEX = 0
CAP_INTERVAL = 1

# Global flags and variables
is_Recording = False
ser = None
camera_thread = None

# ========================================================
# LIGHT CONTROL FUNCTION
# ========================================================

# Initialize Light Control Function
def init_light_control():
    # Initialize serial connection to the Arduino Nano
    global ser
    try:
        ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
        print(f"[SYSTEM] Connected to {ARDUINO_PORT}. Initializing")
        time.sleep(2) # Waiting for Arduino to initialize
        return True
    except serial.SerialException as err:
        print(f"[ERROR] Could not connect to Arduino. {err}")
        ser = None
        return False

# Set Light Control PWM Function
def set_light_control(value):
    # Sends a PWM value from Jetson AGX Orin to Arduino Nano via serial
    if not ser or not ser.is_open:
        print("[ERROR] Serial port is not open. Cannot send PWM value")
        return
    
    # Limit PWM value
    value = max(0, min(255, int(value)))

    sendcommand = f"{value}\n"
    ser.write(sendcommand.encode('utf-8'))

    response = ser.readline().decode('utf-8').strip()
    return response

# Close Light Control Function
def close_light_control():
    # Safely turns off light
    global ser
    if ser and ser.is_open:
        try:
            ser.write(b"0\n") # PWM 0
        except:
            pass
        ser.close()
        print("[SYSTEM] Serial port closed.")


# ========================================================
# PERIODIC CAMERA CAPTURE
# ========================================================

# Periodic Capture Function
def periodic_capture(frame_queue):
    # Grabs frames and puts frame in memory queue
    global is_Recording
    print(f"[SYSTEM] Opening camera on index {CAMERA_INDEX}")
    cap = cv2.VideoCapture(CAMERA_INDEX)

    # Set resolution (720p)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        print("[ERROR] Failed to open camera. Check connection")
        is_Recording = False
        return
    
    print("[SYSTEM] Data Acquisition System is ready. Capturing frames...")

    try:
        while is_Recording:
            # Clear buffer
            for _ in range(5):
                cap.grab()
            
            ret, frame = cap.retrieve()

            if ret:
                # Save to queue
                if frame_queue.full():
                    try:
                        frame_queue.get_nowait()
                    except queue.Empty:
                        pass
                
                frame_queue.put(frame)

                # Sleep loop to allow quick thread exit
                for _ in range(CAP_INTERVAL * 10):
                    if not is_Recording:
                        break
                    time.sleep(0.1)
            else:
                print("[ERROR] Failed to capture frame")
                break

    finally:
        cap.release()
        print("[SYSTEM] Hardware released. Turning off camera")

# ========================================================
# THREAD MANAGEMENT CONTROL
# ========================================================

def start_camera_thread(frame_queue):
    # Start camera capture in background thread
    global is_Recording, camera_thread
    if is_Recording:
        return
    
    is_Recording = True
    # Pass the queue into the thread
    camera_thread = threading.Thread(target=periodic_capture, args=(frame_queue,), daemon=True)
    camera_thread.start()

def stop_camera_thread():
    # Stops camera background thread
    global is_Recording, camera_thread
    is_Recording = False
    if camera_thread:
        print("[SYSTEM] Waiting for camera to close...")
        camera_thread.join()