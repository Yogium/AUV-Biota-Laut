import asyncio
import websockets
import json
import base64
import cv2
import numpy as np
import os
import csv

# Create folders
MAIN_DIR = "results"
PREP_DIR = MAIN_DIR + "/preprocess"
DET_DIR = MAIN_DIR + "/detection"

os.makedirs(MAIN_DIR, exist_ok=True)
os.makedirs(PREP_DIR, exist_ok=True)
os.makedirs(DET_DIR, exist_ok=True)

# Placeholder CSV file
CSV_FILE = os.path.join(MAIN_DIR, "log_objects.csv")

async def handle_connection(websocket):
    print("\n[SYSTEM] System connected successfully!")
    try:
        async for message in websocket:
            data = json.loads(message)

            filename = data["filename"]
            metadata = data["metadata"]

            print(f"[SYSTEM] Received payload. Detections: {len(metadata)}")

            # Decode and save images
            b64_enhanced = data["images"]["preprocessed"]
            if b64_enhanced:
                img_data_enh = base64.b64decode(b64_enhanced)
                np_arr_enh = np.frombuffer(img_data_enh, np.uint8)
                img_enh = cv2.imdecode(np_arr_enh, cv2.IMREAD_COLOR)
                cv2.imwrite(os.path.join(PREP_DIR, filename), img_enh)

            b64_detected = data["images"]["detected"]
            if b64_detected:
                img_data_det = base64.b64decode(b64_detected)
                np_arr_det = np.frombuffer(img_data_det, np.uint8)
                img_det = cv2.imdecode(np_arr_det, cv2.IMREAD_COLOR)
                cv2.imwrite(os.path.join(DET_DIR, filename), img_det)

            print(f" -> Images saved successfully: {filename}")

            # Save metadata to CSV (if detection)
            if metadata:
                file_exists = os.path.isfile(CSV_FILE)
                with open(CSV_FILE, mode='a', newline='') as csv_file:
                    fieldnames = ["ID", "time", "lat", "lon", "depth", "label", "confidence", "flag", "filename"]
                    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                    
                    if not file_exists:
                        writer.writeheader()
                    
                    for item in metadata:
                        writer.writerow(item)
                        
                print(f"[STATUS] Logged {len(metadata)} rows to CSV")
            else:
                print("[STATUS] No marine biota detected")

    except websockets.exceptions.ConnectionClosed:
        print("[SYSTEM] System disconnected")
    except Exception as err:
        print(f"[ERROR] Server error: {err}")

async def main():
    print(f"[SYSTEM] Starting server. Saving data to ./{MAIN_DIR}/")
    # Limit max payload to 10MB
    MAX_PAYLOAD = 10 * 1024 * 1024 
    async with websockets.serve(handle_connection, "0.0.0.0", 8080, max_size=MAX_PAYLOAD, ping_interval=None, ping_timeout=None):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())