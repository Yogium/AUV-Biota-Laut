import cv2
import time
import os

# 1. Tentukan Folder Output
output_folder = "/home/krbai/coba_yolo_auv/output/nyoba_kamera/"
os.makedirs(output_folder, exist_ok=True)

def start_capture_loop(camera_index=0):
    print(f"Membuka kamera pada index {camera_index}...")
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print("Gagal membuka kamera!")
        return

    count = 1  # Penamaan file mulai dari 1
    print("Mulai pengambilan gambar setiap 3 detik. Tekan Ctrl+C untuk berhenti.")
    print("-" * 40)

    try:
        while True:
            ret, frame = cap.read()
            
            if ret:
                # Nama file: 1.jpg, 2.jpg, dst.
                file_name = f"{count}.jpg"
                save_path = os.path.join(output_folder, file_name)
                
                # Simpan gambar
                cv2.imwrite(save_path, frame)
                
                print(f"[OK] Gambar ke-{count} disimpan di: {file_name}")
                
                count += 1
                # Tunggu 3 detik sebelum loop berikutnya
                time.sleep(3)
            else:
                print("Gagal membaca frame dari kamera!")
                break
                
    except KeyboardInterrupt:
        print("\nPengambilan gambar dihentikan oleh pengguna.")
    finally:
        cap.release()
        print("Kamera dilepaskan.")

if __name__ == "__main__":
    # Ganti angka 0 jika kamera binocular Anda terdeteksi di index lain (1, 2, dst)
    start_capture_loop(camera_index=0)