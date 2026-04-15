import cv2
import numpy as np
import os
import time
from datetime import datetime
from ultralytics import YOLO

# ========================================================
# 1. PARAMETER DEFAULT PREPROCESSING
# ========================================================
A_SHIFT, B_SHIFT = 0, 0
OMEGA, CLAHE_CLIP = 0.75, 1.0
RED_STRENGTH, T_MIN = 10, 0.35

# ========================================================
# 2. FUNGSI PREPROCESSING DENGAN DIAGNOSTIK
# ========================================================
def white_balance_adaptive(img, cast_thresh=5.0, cast_max=30.0):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    L, A, B = cv2.split(lab)
    A_f, B_f = A.astype(np.float32), B.astype(np.float32)
    mean_A, mean_B = np.mean(A_f), np.mean(B_f)
    color_cast = max(abs(mean_A - 128), abs(mean_B - 128))

    if color_cast < cast_thresh:
        return img, "SKIP"

    k = np.clip((color_cast - cast_thresh) / (cast_max - cast_thresh), 0.0, 1.0)
    A_corr = np.clip(A_f - k * (mean_A - 128) + A_SHIFT, 0, 255).astype(np.uint8)
    B_corr = np.clip(B_f - k * (mean_B - 128) + B_SHIFT, 0, 255).astype(np.uint8)
    return cv2.cvtColor(cv2.merge([L, A_corr, B_corr]), cv2.COLOR_LAB2BGR), "RUN"

def restore_red_adaptive(img, red_thresh=0.9, red_max_boost=0.6):
    B, G, R = cv2.split(img)
    R_f, G_f = R.astype(np.float32), G.astype(np.float32)
    mean_R, mean_G = np.mean(R_f), np.mean(G_f)
    ratio_RG = mean_R / (mean_G + 1e-6)

    if ratio_RG > red_thresh:
        return img, "SKIP"

    k = np.clip((red_thresh - ratio_RG) / red_thresh, 0.0, 1.0) * red_max_boost
    R_corr = np.clip(R_f * (1.0 + k), 0, 255).astype(np.uint8)
    return cv2.merge([B, G, R_corr]), "RUN"

def clahe_enhance(img):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    L, A, B = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=max(CLAHE_CLIP, 0.1), tileGridSize=(8,8))
    L2 = clahe.apply(L)
    return cv2.cvtColor(cv2.merge([L2, A, B]), cv2.COLOR_LAB2BGR)

def dehaze(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    A = np.percentile(gray, 95)
    t = np.clip(1 - OMEGA * (gray / A), T_MIN, 1.0)
    t_stack = cv2.merge([t, t, t])
    J = (img.astype(np.float32) - A) / t_stack + A
    return np.clip(J, 0, 255).astype(np.uint8)

def sharpen(img):
    blur = cv2.GaussianBlur(img, (3, 3), 0)
    return cv2.addWeighted(img, 1.2, blur, -0.2, 0)

def gamma_correct(img, g=1.2):
    inv = 1.0 / g
    table = np.array([(i / 255.0) ** inv * 255 for i in range(256)]).astype("uint8")
    return cv2.LUT(img, table)

def enhance_underwater_pipeline(img):
    out, st_wb = white_balance_adaptive(img)
    out, st_rr = restore_red_adaptive(out)
    
    out = clahe_enhance(out)
    out = dehaze(out)
    out = sharpen(out)
    out = gamma_correct(out)
    
    status_msg = f"[WB:{st_wb}] [RED:{st_rr}] [CLAHE:OK] [DEHAZE:OK] [SHARP:OK] [GAMMA:OK]"
    return out, status_msg

# ========================================================
# 3. MAIN PROCESSOR (REAL-TIME INTEGRATED + YOLO GACOR)
# ========================================================

# Setup Folders Output
folder_pre_only = "/home/krbai/coba_yolo_auv/output/gabungan/gabungan_pre_ngotret2/"
folder_yolo = "/home/krbai/coba_yolo_auv/output/gabungan/gabungan_yolo_ngotret2/"
os.makedirs(folder_pre_only, exist_ok=True)
os.makedirs(folder_yolo, exist_ok=True)

# Load YOLO Model (MODE TENSORRT / ENGINE)
model_path = "/home/krbai/coba_yolo_auv/model_yolo11/yolo11n_datasetfinal5/best.engine"
print(f"⏳ Memuat model TensorRT ke memori GPU dari:\n   {model_path}")
model = YOLO(model_path, task="detect") 

def start_realtime_capture(camera_index=0):
    print(f"🚀 Membuka kamera pada index {camera_index}...")
    cap = cv2.VideoCapture(camera_index)
    
    # Resolusi 720p sesuai standar proposal
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        print("❌ Gagal membuka kamera! Periksa koneksi USB.")
        return

    count = 1
    print(f"Sistem Siap (Preprocess CPU + YOLO TensorRT GPU). Target: < 1.5 detik")
    print("-" * 75)

    try:
        while True:
            # 1. Clear Hardware Buffer
            for _ in range(5):
                cap.grab()
            
            # 2. Mulai Hitung Waktu Total (Lifecycle)
            start_total = time.time()
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            ret, frame = cap.retrieve()
            
            if ret:
                # ==========================================
                # TAHAP A: PREPROCESSING (CPU)
                # ==========================================
                start_pre = time.time()
                enhanced_frame, pipeline_status = enhance_underwater_pipeline(frame)
                durasi_pre = time.time() - start_pre

                # ==========================================
                # TAHAP B: YOLO INFERENCE (GPU TENSORRT)
                # ==========================================
                # Menggunakan parameter Gacor: device=0, half=True, imgsz=640
                results = model.predict(
                    source=enhanced_frame, 
                    device=0, 
                    imgsz=640, 
                    half=True, 
                    verbose=False
                )
                
                yolo_frame = results[0].plot()
                
                # Mengambil data waktu (ms -> s)
                yolo_speeds = results[0].speed
                yolo_pre = yolo_speeds['preprocess'] / 1000.0
                yolo_inf = yolo_speeds['inference'] / 1000.0
                yolo_post = yolo_speeds['postprocess'] / 1000.0
                durasi_yolo_total = yolo_pre + yolo_inf + yolo_post

                # ==========================================
                # TAHAP C: PENYIMPANAN KE SSD (2 Folder)
                # ==========================================
                file_name = f"{count:03d}.jpg"
                cv2.imwrite(os.path.join(folder_pre_only, file_name), enhanced_frame)
                cv2.imwrite(os.path.join(folder_yolo, file_name), yolo_frame)
                
                # ==========================================
                # TAHAP D: LOGGING WAKTU LENGKAP
                # ==========================================
                total_duration = time.time() - start_total
                
                print(f"📸 [FOTO {count:03d}] | {timestamp} | Resolusi: {frame.shape[1]}x{frame.shape[0]}")
                print(f"   [1] PREPROCESS : {durasi_pre:.4f} detik")
                print(f"       Status     : {pipeline_status}")
                print(f"   [2] YOLOv11    : {durasi_yolo_total:.4f} detik (Total)")
                print(f"       Rincian    : Pre:{yolo_pre:.4f}s | Infer:{yolo_inf:.4f}s | Post:{yolo_post:.4f}s")
                print(f"   [TOTAL CYCLE]  : {total_duration:.4f} detik (Termasuk I/O Disk)")
                print("-" * 75)
                
                count += 1
                time.sleep(3) # Jeda antar pengambilan
            else:
                print("⚠️ Hardware Error: Gagal mengambil frame.")
                break
                
    except KeyboardInterrupt:
        print("\n⏹️ Proses dihentikan oleh pengguna.")
    finally:
        cap.release()
        print("🔌 Hardware Released. Kamera Off.")

if __name__ == "__main__":
    start_realtime_capture(camera_index=0)