import cv2
import numpy as np
import os
import time
from datetime import datetime

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

def gamma_correct(img, g=1.8):
    inv = 1.0 / g
    table = np.array([(i / 255.0) ** inv * 255 for i in range(256)]).astype("uint8")
    return cv2.LUT(img, table)

def enhance_underwater_pipeline(img):
    # Tracking status untuk logging
    out, st_wb = white_balance_adaptive(img)
    out, st_rr = restore_red_adaptive(out)
    
    # Fungsi statis (pasti jalan)
    out = clahe_enhance(out)
    out = dehaze(out)
    out = sharpen(out)
    out = gamma_correct(out)
    
    status_msg = f"[WB:{st_wb}] [RED:{st_rr}] [CLAHE:OK] [DEHAZE:OK] [SHARP:OK] [GAMMA:OK]"
    return out, status_msg

# ========================================================
# 3. MAIN PROCESSOR (REAL-TIME INTEGRATED)
# ========================================================

output_folder = "/home/krbai/coba_yolo_auv/output/nyoba_kamera_preprocess_ngotret4/"
os.makedirs(output_folder, exist_ok=True)

def start_realtime_capture(camera_index=0):
    print(f"🚀 Membuka kamera pada index {camera_index}...")
    cap = cv2.VideoCapture(camera_index)
    
    # --- KONFIGURASI RESOLUSI (Sesuai Proposal: Minimal 720p) ---
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    # ------------------------------------------------------------

    # Set buffer paling rendah untuk menghindari lag pose jari
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        print("❌ Gagal membuka kamera! Periksa koneksi USB.")
        return

    count = 1
    print(f"Sistem Siap. Target Latensi: < 1.5 detik")
    print("-" * 70)

    try:
        while True:
            # 1. Clear Hardware Buffer
            for _ in range(5):
                cap.grab()
            
            # 2. Mulai Hitung Waktu (Total Lifecycle)
            start_total = time.time()
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            ret, frame = cap.retrieve()
            
            if ret:
                # 3. Jalankan Pipeline & Dapatkan Status
                enhanced_frame, pipeline_status = enhance_underwater_pipeline(frame)
                
                # 4. Simpan ke SSD
                file_name = f"{count}.jpg"
                save_path = os.path.join(output_folder, file_name)
                cv2.imwrite(save_path, enhanced_frame)
                
                # 5. Selesai & Hitung Durasi
                total_duration = time.time() - start_total
                
                # Print Log Rapi
                print(f"📸 [FOTO {count:03d}] | {timestamp} | Resolusi: {frame.shape[1]}x{frame.shape[0]}")
                print(f"   Pipeline : {pipeline_status}")
                print(f"   Simpan   : {file_name}")
                print(f"   Durasi   : {total_duration:.4f} detik")
                print("-" * 50)
                
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






"""
import cv2
import numpy as np
import os
import time
from datetime import datetime

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

def gamma_correct(img, g=1.8):
    inv = 1.0 / g
    table = np.array([(i / 255.0) ** inv * 255 for i in range(256)]).astype("uint8")
    return cv2.LUT(img, table)

def enhance_underwater_pipeline(img):
    # Tracking status untuk logging
    out, st_wb = white_balance_adaptive(img)
    out, st_rr = restore_red_adaptive(out)
    
    # Fungsi statis (pasti jalan)
    out = clahe_enhance(out)
    out = dehaze(out)
    out = sharpen(out)
    out = gamma_correct(out)
    
    status_msg = f"[WB:{st_wb}] [RED:{st_rr}] [CLAHE:OK] [DEHAZE:OK] [SHARP:OK] [GAMMA:OK]"
    return out, status_msg

# ========================================================
# 3. MAIN PROCESSOR (REAL-TIME INTEGRATED)
# ========================================================

output_folder = "/home/krbai/coba_yolo_auv/output/nyoba_kamera_preprocess_ngotret3/"
os.makedirs(output_folder, exist_ok=True)

def start_realtime_capture(camera_index=0):
    print(f"🚀 Membuka kamera pada index {camera_index}...")
    cap = cv2.VideoCapture(camera_index)
    
    # Set buffer paling rendah untuk menghindari lag pose jari
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        print("❌ Gagal membuka kamera! Periksa koneksi USB.")
        return

    count = 1
    print(f"Sistem Siap. Target Latensi: < 1.5 detik")
    print("-" * 70)

    try:
        while True:
            # 1. Clear Hardware Buffer
            for _ in range(5):
                cap.grab()
            
            # 2. Mulai Hitung Waktu (Total Lifecycle)
            start_total = time.time()
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            ret, frame = cap.retrieve()
            
            if ret:
                # 3. Jalankan Pipeline & Dapatkan Status
                enhanced_frame, pipeline_status = enhance_underwater_pipeline(frame)
                
                # 4. Simpan ke SSD
                file_name = f"{count}.jpg"
                save_path = os.path.join(output_folder, file_name)
                cv2.imwrite(save_path, enhanced_frame)
                
                # 5. Selesai & Hitung Durasi
                total_duration = time.time() - start_total
                
                # Print Log Rapi
                print(f"📸 [FOTO {count:03d}] | {timestamp} | Resolusi: {frame.shape[1]}x{frame.shape[0]}")
                print(f"   Pipeline : {pipeline_status}")
                print(f"   Simpan   : {file_name}")
                print(f"   Durasi   : {total_duration:.4f} detik")
                print("-" * 50)
                
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



    """