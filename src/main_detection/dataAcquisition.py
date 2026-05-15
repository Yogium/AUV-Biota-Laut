import serial
import time
import cv2

ARDUINO_PORT = '/dev/ttyUSB0' 
BAUD_RATE = 9600
CAMERA_INDEX = 0 # Default

# Global flags and variables
ser = None
cap = None

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
# CAMERA FUNCTIONS
# ========================================================

# Initialize camera function
def init_camera():
    # Grabs frames and puts frame in memory queue
    global cap
    print(f"[SYSTEM] Opening camera on index {CAMERA_INDEX}")
    cap = cv2.VideoCapture(CAMERA_INDEX)

    # Set resolution (720p)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        print("[ERROR] Failed to open camera. Check connection")
        return False
    return True

# Obtain camera frame
def get_camera_frame():
    global cap
    if cap is None or not cap.isOpened():
        return None
    
    # Clear hardware buffer
    for _ in range(5):
        cap.grab()

    ret, frame = cap.retrieve()
    if ret:
        return frame
    return None

# Close camera
def close_camera():
    global cap
    if cap is not None:
        cap.release()
        print("[SYSTEM] Hardware released. Turning off camera...")