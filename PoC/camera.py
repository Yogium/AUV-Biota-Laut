import cv2
from datetime import datetime
import time

def image_cap(out_path = None):
    print("Testing camera access...")
    cap = cv2.VideoCapture(0)
    print(f"Camera opened: {cap.isOpened()}")

    if cap.isOpened():
        print("Waiting 5 seconds for camera initialization...")
        time.sleep(5)
        
        ret, frame = cap.read()
        print(f"Frame read success: {ret}")
        
        if ret:
            print(f"Frame shape: {frame.shape}")
            if out_path is None:
                out_path = f"image_{datetime.now().strftime('%Y%m%d_%H%M')}.jpg"
            cv2.imwrite(out_path, frame)
            print(f"Image saved as {out_path}")
            return out_path
        else:
            print("Failed to read frame")
    else:
        print("Failed to open camera")

    cap.release()
    return None

if __name__ == "__main__":
    result = image_cap()
    print(f"Image saved: {result}")