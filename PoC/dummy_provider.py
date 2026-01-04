import socket
import json
import time
import random
import uuid

def send_data(port, provider_name):
    """Simulates an AUV data provider that sends sensor readings"""
    RASPPI_IP = '192.168.1.12'
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((RASPPI_IP, port))
        print(f"{provider_name} connected to {RASPPI_IP}:{port}")
    except ConnectionRefusedError:
        print(f"Error: Could not connect to {RASPPI_IP}:{port}. Make sure the collector is running.")
        return
    
    counter = 0
    while True:
        try:
            counter += 1
            data = {
                'id': str(uuid.uuid4()),
                'timestamp': time.time(),
                'lat': random.uniform(-6.9, -6.8),  # Indonesia coordinates
                'long': random.uniform(107.5, 107.7),
                'depth': random.uniform(0, 20),  # meters
                'label': random.choice(['Ikan', 'Terumbu Karang', 'Tanaman', 'Manusia', 'Other']),
                'conf': round(random.uniform(0.5, 0.99), 2),  # confidence
                'filename': f"{provider_name}_frame_{counter}.jpg"
            }
            message = json.dumps(data) + '\n'
            sock.send(message.encode())
            print(f"{provider_name} sent: {data}")
            time.sleep(2)
        except Exception as e:
            print(f"Error in {provider_name}: {e}")
            break
    
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
