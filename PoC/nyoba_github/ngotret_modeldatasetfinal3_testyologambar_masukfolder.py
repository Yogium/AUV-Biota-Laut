from ultralytics import YOLO
import cv2
import os
from datetime import datetime

# Load model
model = YOLO(r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal3\best.pt")

# Folder output
save_folder = r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal3\testing_preproces\test_white_balance_mang"
os.makedirs(save_folder, exist_ok=True)

# Path gambar input
img_path = r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal3\testing_preproces\white_balance_mang\WB1_0,4_gb1.jpg"

# Baca gambar
img = cv2.imread(img_path)

# Deteksi dengan YOLO
results = model(img)

# Annotate hasil deteksi
annotated = results[0].plot()

# Simpan dengan timestamp unik
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
filename = f"{timestamp}_WB1_0,4_gb1.jpg"
save_path = os.path.join(save_folder, filename)
cv2.imwrite(save_path, annotated)

print(f"[INFO] Gambar disimpan di: {save_path}")
