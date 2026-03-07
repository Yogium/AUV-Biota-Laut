from ultralytics import YOLO
import cv2
import os
import time
import numpy as np
import csv
from ultralytics.utils.plotting import Annotator

# ---------------- CONFIG ----------------
MODEL_PATH = r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal5\yolo11s\best.pt"

INPUT_FOLDER = r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal5\testing\ngotret aja sih"
SAVE_FOLDER = r"D:\POCestimasijara\lucu2"
CSV_FILE = os.path.join(SAVE_FOLDER, "log_objects.csv")

AUV_SPEED = 0.5  # m/s
VEHICLE_ID = "auv01"
MISSION_ID = "ms03"
# ----------------------------------------

def generate_filename(counter):
    return f"{VEHICLE_ID}_{MISSION_ID}_img{counter:05d}.jpg"

# ===== Dummy Location Model =====
METER_TO_DEG = 1 / 111_111

def update_position(pos, dt):
    distance = AUV_SPEED * dt
    pos[0] += distance * METER_TO_DEG
    pos[1] += 0.3 * distance * METER_TO_DEG
    pos[2] += 0.05 * dt
    return pos
# ================================

# ===== Mapping warna (BGR) berdasarkan label dan flag =====
# flag 0 = yakin (tua), flag 1 = tidak yakin (muda)
COLOR_MAP = {
    (0,0): (32, 165, 218),   # ikan yakin - kuning tua
    (0,1): (0, 0, 255),  # ikan tidak yakin - kuning muda tetap kuning tapi kontras


    (1,0): (150, 0, 0),      # coral yakin - biru tua
    (1,1): (0, 0, 255),  # coral tidak yakin - biru muda

    (2,0): (255, 0, 255),      # seagrass yakin - merah tua
    (2,1): (0, 0, 255),  # seagrass tidak yakin - merah muda

    (3,0): (0, 100, 0),      # human yakin - hijau tua
    (3,1): (0, 0, 255),  # human tidak yakin - hijau muda

    (4,0): (80, 80, 80),     # other yakin - abu tua
    (4,1): (0, 0, 255),  # other tidak yakin - abu muda
}


def main():
    os.makedirs(SAVE_FOLDER, exist_ok=True)

    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(
                ["ID", "timestamp", "lat", "lon", "depth", "label", "confidence", "filename"]
            )

    model = YOLO(MODEL_PATH)

    image_counter = 1
    start_time = time.time()
    last_snapshot_time = time.time()
    position = np.array([-6.8900, 107.6100, 5.0], dtype=np.float32)

    image_files = sorted([
        f for f in os.listdir(INPUT_FOLDER)
        if f.lower().endswith(('.jpg', '.jpeg', '.png'))
    ])

    for img_name in image_files:
        snapshot_time = time.time()
        dt = snapshot_time - last_snapshot_time
        last_snapshot_time = snapshot_time

        img_path = os.path.join(INPUT_FOLDER, img_name)
        frame = cv2.imread(img_path)
        if frame is None:
            continue

        # YOLO + anotasi
        results = model(frame)
        annotated = frame.copy()
        annotator = Annotator(annotated)

        csv_rows = []
        boxes = results[0].boxes

        # ===== counter PER LABEL =====
        label_counter = {}

        if boxes is not None and len(boxes) > 0:
            for box in boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])

                # init counter per label
                if cls not in label_counter:
                    label_counter[cls] = 1
                else:
                    label_counter[cls] += 1

                obj_counter = label_counter[cls]

                # tentukan yakin/tidak yakin
                flag = 1 if conf < 0.5 else 0

                unique_id = f"{flag}{cls}{image_counter:05d}{obj_counter:03d}"

                x1, y1, x2, y2 = map(int, box.xyxy[0])

                # ===== pilih warna dari mapping =====
                color = COLOR_MAP.get((cls, flag), (255, 255, 255))

                # pasang label dengan warna yang benar
                annotator.box_label([x1, y1, x2, y2], f"ID:{unique_id}", color=color)

                csv_rows.append([
                    unique_id,
                    "",
                    float(position[0]),
                    float(position[1]),
                    float(position[2]),
                    str(cls),
                    float(conf),
                    generate_filename(image_counter)
                ])

        annotated = annotator.result()

        # Simpan gambar
        filename = generate_filename(image_counter)
        cv2.imwrite(os.path.join(SAVE_FOLDER, filename), annotated)

        # Update posisi
        position = update_position(position, dt)

        # t_global
        t_global = time.time() - start_time

        for row in csv_rows:
            row[1] = t_global

        if csv_rows:
            with open(CSV_FILE, "a", newline="") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerows(csv_rows)

        # proc_time sampai akhir
        proc_time = time.time() - snapshot_time

        print(
            f"[SNAPSHOT] img={filename} | "
            f"proc_time={proc_time:.3f}s | "
            f"t_global={t_global:.2f}s | "
            f"lat={position[0]:.6f}, "
            f"lon={position[1]:.6f}, "
            f"depth={position[2]:.2f}m"
        )

        image_counter += 1

    print("Semua gambar selesai diproses.")

if __name__ == "__main__":
    main()


"""
====================================================================================================
ini kode yang dasarnya yak
from ultralytics import YOLO
import cv2
import os
import time
import numpy as np
import csv
from ultralytics.utils.plotting import Annotator

# ---------------- CONFIG ----------------
MODEL_PATH = r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal5\yolo11s\best.pt"

INPUT_FOLDER = r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal5\testing\databersih"
SAVE_FOLDER = r"D:\POC2"
CSV_FILE = os.path.join(SAVE_FOLDER, "log_objects.csv")

AUV_SPEED = 0.5  # m/s
VEHICLE_ID = "auv01"
MISSION_ID = "ms03"
# ----------------------------------------

def generate_filename(counter):
    return f"{VEHICLE_ID}_{MISSION_ID}_img{counter:05d}.jpg"

# ===== Dummy Location Model =====
METER_TO_DEG = 1 / 111_111

def update_position(pos, dt):
    distance = AUV_SPEED * dt
    pos[0] += distance * METER_TO_DEG
    pos[1] += 0.3 * distance * METER_TO_DEG
    pos[2] += 0.05 * dt
    return pos
# ================================

def main():
    os.makedirs(SAVE_FOLDER, exist_ok=True)

    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(
                ["ID", "timestamp", "lat", "lon", "depth", "label", "confidence", "filename"]
            )

    model = YOLO(MODEL_PATH)

    image_counter = 1
    start_time = time.time()
    last_snapshot_time = time.time()
    position = np.array([-6.8900, 107.6100, 5.0], dtype=np.float32)

    image_files = sorted([
        f for f in os.listdir(INPUT_FOLDER)
        if f.lower().endswith(('.jpg', '.jpeg', '.png'))
    ])

    for img_name in image_files:
        snapshot_time = time.time()
        dt = snapshot_time - last_snapshot_time
        last_snapshot_time = snapshot_time

        img_path = os.path.join(INPUT_FOLDER, img_name)
        frame = cv2.imread(img_path)
        if frame is None:
            continue

        # YOLO + anotasi
        results = model(frame)
        annotated = frame.copy()
        annotator = Annotator(annotated)

        csv_rows = []
        boxes = results[0].boxes

        # ===== counter PER LABEL =====
        label_counter = {}

        if boxes is not None and len(boxes) > 0:
            for box in boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])

                # init counter per label
                if cls not in label_counter:
                    label_counter[cls] = 1
                else:
                    label_counter[cls] += 1

                obj_counter = label_counter[cls]

                flag = 1 if conf < 0.5 else 0
                unique_id = f"{flag}{cls}{image_counter:05d}{obj_counter:03d}"

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                annotator.box_label([x1, y1, x2, y2], f"ID:{unique_id}")

                csv_rows.append([
                    unique_id,
                    "",
                    float(position[0]),
                    float(position[1]),
                    float(position[2]),
                    str(cls),
                    float(conf),
                    generate_filename(image_counter)
                ])


        annotated = annotator.result()

        # Simpan gambar
        filename = generate_filename(image_counter)
        cv2.imwrite(os.path.join(SAVE_FOLDER, filename), annotated)

        # Update posisi
        position = update_position(position, dt)

        # t_global
        t_global = time.time() - start_time

        for row in csv_rows:
            row[1] = t_global

        if csv_rows:
            with open(CSV_FILE, "a", newline="") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerows(csv_rows)

        # proc_time sampai akhir
        proc_time = time.time() - snapshot_time

        print(
            f"[SNAPSHOT] img={filename} | "
            f"proc_time={proc_time:.3f}s | "
            f"t_global={t_global:.2f}s | "
            f"lat={position[0]:.6f}, "
            f"lon={position[1]:.6f}, "
            f"depth={position[2]:.2f}m"
        )

        image_counter += 1

    print("Semua gambar selesai diproses.")

if __name__ == "__main__":
    main()
"""