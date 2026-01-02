from ultralytics import YOLO
import cv2
import os
from datetime import datetime

# =========================
# Load model
# =========================
model = YOLO(
    r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal4\best.pt"
)

# =========================
# Folder input & output
# =========================
input_folder = r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal5\testing\datamentah"
output_folder = r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal5\testing\output_datamentah"

os.makedirs(output_folder, exist_ok=True)

# =========================
# Loop semua gambar
# =========================
for filename in os.listdir(input_folder):
    if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        img_path = os.path.join(input_folder, filename)

        img = cv2.imread(img_path)
        if img is None:
            continue

        # YOLO inference
        results = model(img)
        annotated = results[0].plot()

        # Nama file output (pakai nama asli + timestamp biar aman)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        out_name = f"{os.path.splitext(filename)[0]}_{timestamp}.jpg"
        out_path = os.path.join(output_folder, out_name)

        cv2.imwrite(out_path, annotated)
        print(f"[OK] Disimpan: {out_path}")

print("Selesai. Semua gambar sudah diproses.")





"""
=================================================================================================================================
ini kode buat multi foto
from ultralytics import YOLO
import cv2
import os
from datetime import datetime

# =========================
# Load model
# =========================
model = YOLO(
    r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal5\best.pt"
)

# =========================
# Folder input & output
# =========================
input_folder = r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal5\testing\databersih"
output_folder = r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal5\testing\output_databersih"

os.makedirs(output_folder, exist_ok=True)

# =========================
# Loop semua gambar
# =========================
for filename in os.listdir(input_folder):
    if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        img_path = os.path.join(input_folder, filename)

        img = cv2.imread(img_path)
        if img is None:
            continue

        # YOLO inference
        results = model(img)
        annotated = results[0].plot()

        # Nama file output (pakai nama asli + timestamp biar aman)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        out_name = f"{os.path.splitext(filename)[0]}_{timestamp}.jpg"
        out_path = os.path.join(output_folder, out_name)

        cv2.imwrite(out_path, annotated)
        print(f"[OK] Disimpan: {out_path}")

print("Selesai. Semua gambar sudah diproses.")

"""


"""=======================================================================================
ini kode aslinya mang

from ultralytics import YOLO
import cv2
import os
from datetime import datetime

# Load model
model = YOLO(r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal3\best.pt")

# Folder output
save_folder = r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal3\testing_preproces\ngotret_test"
os.makedirs(save_folder, exist_ok=True)

# Path gambar input
img_path = r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal3\testing_preproces\gb1.jpg"

# Baca gambar
img = cv2.imread(img_path)

# Deteksi dengan YOLO
results = model(img)

# Annotate hasil deteksi
annotated = results[0].plot()

# Simpan dengan timestamp unik
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
filename = f"{timestamp}_SH2_7_.jpg"
save_path = os.path.join(save_folder, filename)
cv2.imwrite(save_path, annotated)

print(f"[INFO] Gambar disimpan di: {save_path}")

"""



"""=======================================================================================
ini kode yang bakal flag merah di bwah confidence tresshold
from ultralytics import YOLO
import cv2
import os
from datetime import datetime

# Load model
model = YOLO(r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal3\best.pt")

# Folder output
save_folder = r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal3\testing_preproces\ngotret_test"
os.makedirs(save_folder, exist_ok=True)

# Path gambar input
img_path = r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal3\testing_preproces\gb1.jpg"

# Baca gambar
img = cv2.imread(img_path)

# Deteksi dengan YOLO
results = model(img)

# Ambil hasil
boxes = results[0].boxes
names = model.names

# Copy image buat anotasi
annotated = img.copy()

CONF_THRESHOLD = 0.5

for box in boxes:
    x1, y1, x2, y2 = map(int, box.xyxy[0])
    conf = float(box.conf[0])
    cls = int(box.cls[0])
    label = names[cls]

    # Warna berdasarkan confidence
    if conf < CONF_THRESHOLD:
        color = (0, 0, 255)   # merah
    else:
        color = (0, 255, 0)   # hijau

    text = f"{label} {conf:.2f}"

    # Draw bounding box
    cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
    cv2.putText(
        annotated,
        text,
        (x1, y1 - 5),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        color,
        2
    )

# Simpan dengan timestamp unik
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
filename = f"{timestamp}_SH2_7_.jpg"
save_path = os.path.join(save_folder, filename)
cv2.imwrite(save_path, annotated)

print(f"[INFO] Gambar disimpan di: {save_path}")

"""



"""=======================================================================================
ini kode yang bakal ngilangin bbox kalo di bawah conf tresshold
from ultralytics import YOLO
import cv2
import os
from datetime import datetime

# Load model
model = YOLO(r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal3\best.pt")

# Folder output
save_folder = r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal3\testing_preproces\ngotret_test"
os.makedirs(save_folder, exist_ok=True)

# Path gambar input
img_path = r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal3\testing_preproces\gb1.jpg"

# Baca gambar
img = cv2.imread(img_path)

# Deteksi dengan confidence threshold
results = model(img, conf=0.5)

# Annotate hasil deteksi
annotated = results[0].plot()

# Simpan hasil
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
filename = f"{timestamp}_SH2_7_.jpg"
save_path = os.path.join(save_folder, filename)
cv2.imwrite(save_path, annotated)

print(f"[INFO] Gambar disimpan di: {save_path}")


"""


"""=======================================================================================
ini kode 

"""
