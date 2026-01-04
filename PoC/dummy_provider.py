import socket
import json
import time
import random
import uuid
import camera
import os

def send_data(port, provider_name):
    """Simulates an AUV data provider that sends sensor readings with real camera images"""
    RASPPI_IP = 'localhost'
    
    # Setup camera
    cap = camera.setup_camera()
    if cap is None:
        print(f"{provider_name}: Camera setup failed, using dummy mode")
        cap = None
    
    # Create output directory for images
    output_dir = "captured_images"
    os.makedirs(output_dir, exist_ok=True)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((RASPPI_IP, port))
        print(f"{provider_name} connected to {RASPPI_IP}:{port}")
    except ConnectionRefusedError:
        print(f"Error: Could not connect to {RASPPI_IP}:{port}. Make sure the collector is running.")
        if cap:
            cap.release()
        return
    
    counter = 0
    mission_number = "MS001"
    AUV_number = "AUV01"
    
    while True:
        try:
            counter += 1 
            # Capture image from camera if available
            image_filename = None
            if cap:
                ret, frame = cap.read()
                if ret:
                    # Save the captured frame
                    image_filename = os.path.join(output_dir, f"{AUV_number}_{mission_number}_{counter:06d}.jpg")
                    import cv2
                    cv2.imwrite(image_filename, frame)
                    image_filename = os.path.basename(image_filename)
            
            # If no camera, use default filename
            if not image_filename:
                image_filename = f"{AUV_number}, {mission_number}, {counter:06d}.jpg"
            
            data = {
                'id': str(uuid.uuid4()),
                'timestamp': time.time(),
                'lat': random.uniform(-6.9, -6.8),  # Indonesia coordinates
                'long': random.uniform(107.5, 107.7),
                'depth': random.uniform(0, 20),  # meters
                'label': random.choice(['Ikan', 'Terumbu Karang', 'Tanaman', 'Manusia', 'Other']),
                'conf': round(random.uniform(0.5, 0.99), 2),  # confidence
                'filename': image_filename
            }
            message = json.dumps(data) + '\n'
            sock.send(message.encode())
            print(f"{provider_name} sent: {data}")
            time.sleep(1.5)
        except Exception as e:
            print(f"Error in {provider_name}: {e}")
            break
    
    if cap:
        cap.release()
    sock.close()

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
        provider_name = sys.argv[2] if len(sys.argv) > 2 else f"Provider_{port}"
    else:
        print("Usage: python dummy_provider.py <port> [provider_name]")
        print("Example: python dummy_provider.py 5001 Camera_1")
        sys.exit(1)
    
    send_data(port, provider_name)
