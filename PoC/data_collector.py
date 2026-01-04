import socket
import json
import csv
import threading
import time
from datetime import datetime

class DataCollector:
    def __init__(self, output_file='unified_data.csv'):
        self.output_file = output_file
        self.data_buffer = {}
        self.lock = threading.Lock()
        self.servers = {}
        self.fieldnames = [
            'collection_timestamp', 'provider_id',
            'id', 'timestamp', 'lat', 'long', 'depth', 'label', 'conf', 'filename'
        ]
        
    def start_server(self, port, source_name):
        """Start a server on a specific port to receive data from a provider"""
        def handle_connections():
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(('0.0.0.0', port))
            server.listen(1)
            print(f"[{source_name}] Server listening on port {port}")
            
            while True:
                try:
                    conn, addr = server.accept()
                    print(f"[{source_name}] Connection from {addr}")
                    threading.Thread(
                        target=self.receive_data, 
                        args=(conn, source_name), 
                        daemon=True
                    ).start()
                except Exception as e:
                    print(f"[{source_name}] Error: {e}")
        
        thread = threading.Thread(target=handle_connections, daemon=True)
        thread.start()
        self.servers[source_name] = thread
    
    def receive_data(self, conn, source_name):
        """Receive data from a provider"""
        buffer = ""
        try:
            while True:
                chunk = conn.recv(1024).decode()
                if not chunk:
                    break
                    
                buffer += chunk
                lines = buffer.split('\n')
                buffer = lines[-1]
                
                for line in lines[:-1]:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            with self.lock:
                                if source_name not in self.data_buffer:
                                    self.data_buffer[source_name] = {}
                                self.data_buffer[source_name] = data
                                print(f"[{source_name}] Received: {data}")
                        except json.JSONDecodeError as e:
                            print(f"[{source_name}] JSON error: {e}")
        except Exception as e:
            print(f"[{source_name}] Connection error: {e}")
        finally:
            conn.close()
            print(f"[{source_name}] Disconnected")
    
    def write_to_csv(self, interval=5):
        """Periodically write unified data to CSV"""
        first_write = True
        
        while True:
            time.sleep(interval)
            
            with self.lock:
                if not self.data_buffer:
                    continue
                
                # Write one row per provider (one row = one provider's latest data)
                for provider_id, data in self.data_buffer.items():
                    unified_row = {
                        'collection_timestamp': datetime.now().isoformat(),
                        'provider_id': provider_id,
                        'id': data.get('id', ''),
                        'timestamp': data.get('timestamp', ''),
                        'lat': data.get('lat', ''),
                        'long': data.get('long', ''),
                        'depth': data.get('depth', ''),
                        'label': data.get('label', ''),
                        'conf': data.get('conf', ''),
                        'filename': data.get('filename', '')
                    }
                    
                    try:
                        with open(self.output_file, 'a', newline='') as f:
                            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
                            if first_write:
                                writer.writeheader()
                                first_write = False
                            writer.writerow(unified_row)
                        print(f"Wrote row for {provider_id}")
                    except Exception as e:
                        print(f"Error writing to CSV: {e}")

def main():
    collector = DataCollector('unified_data.csv')
    
    # Start servers for each provider
    # You can add more providers by calling start_server with different ports
    collector.start_server(5001, 'Camera_1')
    collector.start_server(5002, 'Camera_2')
    collector.start_server(5003, 'Camera_3')
    
    # Start CSV writer thread
    csv_thread = threading.Thread(target=collector.write_to_csv, args=(5,), daemon=True)
    csv_thread.start()
    
    print("Data collector started. Waiting for connections...")
    print("Provider ports: 5001, 5002, 5003")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")

if __name__ == '__main__':
    main()
