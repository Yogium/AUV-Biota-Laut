from ultralytics import YOLO
import cv2
import os
from datetime import datetime

# Load model
model = YOLO(r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal3\best.pt")

# Path video input dan folder output
video_path = r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal3\testing\GH023425 Pt2.MP4"
save_folder = r"D:\ngotret_testyolovideo_masukfolder"
os.makedirs(save_folder, exist_ok=True)

# Buka video
cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)
if fps == 0:
    fps = 30

width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
if width == 0 or height == 0:
    width, height = 640, 480  # fallback

# Output video dengan codec MJPG + .avi
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
save_path = os.path.join(save_folder, f"{timestamp}_video_detected.avi")
fourcc = cv2.VideoWriter_fourcc(*'MJPG')
out = cv2.VideoWriter(save_path, fourcc, fps, (width, height))

if not out.isOpened():
    raise RuntimeError(f"VideoWriter gagal inisialisasi! fps={fps}, size=({width},{height})")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    results = model(frame)
    annotated = results[0].plot()
    out.write(annotated)

cap.release()
out.release()
print(f"[INFO] Video deteksi disimpan di: {save_path}")
