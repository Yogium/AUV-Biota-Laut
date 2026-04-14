from ultralytics import YOLO
import cv2
import os

# ========================================================
# 1. LOAD MODEL (MODE GACOR - TENSORRT)
# ========================================================
model_path = "/home/krbai/coba_yolo_auv/model_yolo11/yolo11n_datasetfinal5/best.engine"
model = YOLO(model_path, task="detect")

# ========================================================
# 2. FOLDER INPUT & OUTPUT
# ========================================================
input_folder = "/home/krbai/coba_yolo_auv/gambar_testing_bersih/"
output_folder = "/home/krbai/coba_yolo_auv/output/output_yolo11n_dtf5/data_bersih_engine"

os.makedirs(output_folder, exist_ok=True)

image_files = [f for f in os.listdir(input_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

print(f"🚀 Memulai deteksi 'Mode Gacor' pada {len(image_files)} gambar...")
print("-" * 65)
print(f"{'Filename':<20} | {'Pre':<6} | {'Infer':<6} | {'Post':<6} | {'TOTAL (ms)':<10}")
print("-" * 65)

# ========================================================
# 3. DETEKSI DENGAN OPTIMASI PENUH (STREAM=TRUE)
# ========================================================
results = model.predict(
    source=input_folder, 
    device=0,         
    imgsz=640,        
    half=True,        
    stream=True,      
    conf=0.25         
)

for result in results:
    filename = os.path.basename(result.path)
    
    # --- AMBIL INFORMASI WAKTU LENGKAP ---
    pre = result.speed['preprocess']
    inf = result.speed['inference']
    post = result.speed['postprocess']
    total = pre + inf + post
    
    # Print baris tabel
    print(f"{filename[:20]:<20} | {pre:>5.1f} | {inf:>5.1f} | {post:>5.1f} | {total:>10.1f}")
    # -------------------------------------
    
    # Plot & Simpan
    annotated_frame = result.plot()
    out_path = os.path.join(output_folder, f"hasil_{filename}")
    cv2.imwrite(out_path, annotated_frame)

print("-" * 65)
print(f"✅ Selesai! Semua hasil tersimpan di: {output_folder}")


"""
#ini kode yang gaada informasi waktu ynag lenkgap ==========

from ultralytics import YOLO
import cv2
import os

# ========================================================
# 1. LOAD MODEL (MODE GACOR - TENSORRT)

# ========================================================
# Memanggil file .engine yang sudah Anda buat (TensorRT)
model_path = "/home/krbai/coba_yolo_auv/model_yolo11/yolo11n_datasetfinal5/best.engine"
model = YOLO(model_path, task="detect")

# ========================================================
# 2. FOLDER INPUT & OUTPUT
# ========================================================
input_folder = "/home/krbai/coba_yolo_auv/gambar_testing_bersih/"
output_folder = "/home/krbai/coba_yolo_auv/output/output_yolo11n_dtf5/data_bersih_engine"

os.makedirs(output_folder, exist_ok=True)

# Ambil daftar semua gambar (Filter file format gambar saja)
image_files = [f for f in os.listdir(input_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

print(f"🚀 Memulai deteksi 'Mode Gacor' pada {len(image_files)} gambar...")

# ========================================================
# 3. DETEKSI DENGAN OPTIMASI PENUH
# ========================================================
# Menggunakan model.predict sebagai generator (stream=True) agar hemat RAM
# dan half=True agar menggunakan FP16 (Akselerasi GPU Orin)
results = model.predict(
    source=input_folder, 
    device=0,         # Wajib GPU
    imgsz=640,        # Konsisten dengan export
    half=True,        # AKTIFKAN FP16 (Mode Gacor)
    stream=True,      # Proses satu per satu sebagai generator (Efisien)
    conf=0.25         # Confidence threshold standar
)

# Karena stream=True, kita melakukan iterasi pada generator 'results'
for result in results:
    # Mengambil path asli file untuk menamai output
    original_path = result.path
    filename = os.path.basename(original_path)
    
    # Plot hasil deteksi ke gambar
    annotated_frame = result.plot()

    # Simpan hasil menggunakan OpenCV
    out_path = os.path.join(output_folder, f"hasil_{filename}")
    cv2.imwrite(out_path, annotated_frame)
    
    # Menampilkan info performa per gambar di terminal
    # Speed['inference'] menunjukkan berapa ms (milidetik) per gambar
    inference_speed = result.speed['inference']
    print(f"[OK] {filename} | Speed: {inference_speed:.1f}ms")

print("-" * 40)
print(f"✅ Selesai! Semua hasil tersimpan di: {output_folder}")


"""




"""#= ini kode yang make onnx
from ultralytics import YOLO
import cv2
import os
from datetime import datetime

# =========================
# 1. Load Model (ONNX di Jetson)
# =========================
# Menggunakan path yang Anda berikan, jangan lupa sertakan nama filenya di ujung
model_path = "/home/krbai/coba_yolo_auv/model_yolo11/yolo11n_datasetfinal5/best.onnx"
model = YOLO(model_path, task="detect")

# =========================
# 2. Folder Input & Output
# =========================
input_folder = "/home/krbai/coba_yolo_auv/gambar_testing_bersih/"
output_folder = "/home/krbai/coba_yolo_auv/output/output_yolo11n_dtf5/data_bersih"

# Buat folder output jika belum ada
os.makedirs(output_folder, exist_ok=True)

# =========================
# 3. Loop Semua Gambar
# =========================
print(f"Memulai deteksi di: {input_folder}")

for filename in os.listdir(input_folder):
    if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        img_path = os.path.join(input_folder, filename)

        # YOLO inference (device=0 wajib agar pakai GPU Orin)
        # Menggunakan .predict lebih stabil untuk batch processing
        results = model.predict(source=img_path, device=0, imgsz=640)
        annotated = results[0].plot()

        # Nama file output
        out_name = f"hasil_{filename}"
        out_path = os.path.join(output_folder, out_name)

        # Simpan hasil
        cv2.imwrite(out_path, annotated)
        print(f"[OK] Disimpan: {out_path}")

print("-" * 30)
print(f"Selesai! Semua hasil ada di: {output_folder}")"""