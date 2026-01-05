from ultralytics import YOLO
import cv2
import os
import time
import numpy as np
import csv
from ultralytics.utils.plotting import Annotator

# ---------------- CONFIG ----------------
MODEL_PATH = r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal5\yolo11s\best.pt"
SAVE_FOLDER = r"D:\POC\POCC"
CSV_FILE = os.path.join(SAVE_FOLDER, "log_objects.csv")

INTERVAL = 1.5        # detik
AUV_SPEED = 0.5       # m/s

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

# ===== Mapping warna (BGR) =====
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
            writer.writerow([
                "ID", "timestamp", "lat", "lon", "depth",
                "label", "confidence", "filename"
            ])

    model = YOLO(MODEL_PATH)
    cap = cv2.VideoCapture(0)

    image_counter = 1
    start_time = time.time()
    last_snapshot_time = time.time()
    position = np.array([-6.8900, 107.6100, 5.0], dtype=np.float32)

    try:
        while True:
            snapshot_time = time.time()
            dt = snapshot_time - last_snapshot_time
            last_snapshot_time = snapshot_time

            # 1. Ambil snapshot
            ret, frame = cap.read()
            if not ret:
                break

            # 2. YOLO + anotasi
            results = model(frame)
            annotated = frame.copy()
            annotator = Annotator(annotated)

            csv_rows = []
            boxes = results[0].boxes

            # === COUNTER PER LABEL (FIX) ===
            label_counter = {}
            # ===============================

            if boxes is not None and len(boxes) > 0:
                for box in boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])

                    # Counter per label
                    if cls not in label_counter:
                        label_counter[cls] = 1
                    else:
                        label_counter[cls] += 1

                    obj_counter = label_counter[cls]
                    flag = 1 if conf < 0.5 else 0

                    unique_id = f"{flag}{cls}{image_counter:05d}{obj_counter:03d}"

                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    # ===== PILIH WARNA DARI COLOR_MAP =====
                    color = COLOR_MAP.get((cls, flag), (255, 255, 255))  # default putih jika label tidak ada
                    annotator.box_label(
                        [x1, y1, x2, y2],
                        f"ID:{unique_id}",
                        color=color
                    )

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

            # 3. Simpan gambar
            filename = generate_filename(image_counter)
            cv2.imwrite(os.path.join(SAVE_FOLDER, filename), annotated)

            # 4. Update posisi
            position = update_position(position, dt)

            # 5. Hitung t_global
            t_global = time.time() - start_time

            # 6. Update timestamp CSV
            for row in csv_rows:
                row[1] = t_global

            # 7. Tulis CSV
            if csv_rows:
                with open(CSV_FILE, "a", newline="") as f:
                    writer = csv.writer(f, delimiter=";")
                    writer.writerows(csv_rows)

            # 8. Hitung proc_time (SAMPAI AKHIR)
            finish_time = time.time()
            proc_time = finish_time - snapshot_time

            # 9. Log terminal
            print(
                f"[SNAPSHOT] img={filename} | "
                f"proc_time={proc_time:.3f}s | "
                f"t_global={t_global:.2f}s | "
                f"lat={position[0]:.6f}, "
                f"lon={position[1]:.6f}, "
                f"depth={position[2]:.2f}m"
            )

            image_counter += 1

            # 10. Jaga interval
            time.sleep(max(0, INTERVAL - proc_time))

    except KeyboardInterrupt:
        print("Stop requested by user")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Camera released, program exited cleanly")

if __name__ == "__main__":
    main()




"""
====
ini kode yang udah sesuai warnanya


"""

"""
====================================================================================================
ini kode yang udah csv juga paling update yaitu waktu proc nya setelah csv
from ultralytics import YOLO
import cv2
import os
import time
import numpy as np
import csv
from ultralytics.utils.plotting import Annotator

# ---------------- CONFIG ----------------
MODEL_PATH = r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal5\yolo11s\best.pt"
SAVE_FOLDER = r"D:\POC"
CSV_FILE = os.path.join(SAVE_FOLDER, "log_objects.csv")

INTERVAL = 1.5        # detik
AUV_SPEED = 0.5       # m/s

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
            writer.writerow([
                "ID", "timestamp", "lat", "lon", "depth",
                "label", "confidence", "filename"
            ])

    model = YOLO(MODEL_PATH)
    cap = cv2.VideoCapture(0)

    image_counter = 1
    start_time = time.time()
    last_snapshot_time = time.time()
    position = np.array([-6.8900, 107.6100, 5.0], dtype=np.float32)

    try:
        while True:
            snapshot_time = time.time()
            dt = snapshot_time - last_snapshot_time
            last_snapshot_time = snapshot_time

            # 1. Ambil snapshot
            ret, frame = cap.read()
            if not ret:
                break

            # 2. YOLO + anotasi
            results = model(frame)
            annotated = frame.copy()
            annotator = Annotator(annotated)

            csv_rows = []
            boxes = results[0].boxes

            # === COUNTER PER LABEL (FIX) ===
            label_counter = {}
            # ===============================

            if boxes is not None and len(boxes) > 0:
                for box in boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])

                    # Counter per label
                    if cls not in label_counter:
                        label_counter[cls] = 1
                    else:
                        label_counter[cls] += 1

                    obj_counter = label_counter[cls]
                    flag = 1 if conf < 0.5 else 0

                    unique_id = f"{flag}{cls}{image_counter:05d}{obj_counter:03d}"

                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    annotator.box_label(
                        [x1, y1, x2, y2],
                        f"ID:{unique_id}"
                    )

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

            # 3. Simpan gambar
            filename = generate_filename(image_counter)
            cv2.imwrite(os.path.join(SAVE_FOLDER, filename), annotated)

            # 4. Update posisi
            position = update_position(position, dt)

            # 5. Hitung t_global
            t_global = time.time() - start_time

            # 6. Update timestamp CSV
            for row in csv_rows:
                row[1] = t_global

            # 7. Tulis CSV
            if csv_rows:
                with open(CSV_FILE, "a", newline="") as f:
                    writer = csv.writer(f, delimiter=";")
                    writer.writerows(csv_rows)

            # 8. Hitung proc_time (SAMPAI AKHIR)
            finish_time = time.time()
            proc_time = finish_time - snapshot_time

            # 9. Log terminal
            print(
                f"[SNAPSHOT] img={filename} | "
                f"proc_time={proc_time:.3f}s | "
                f"t_global={t_global:.2f}s | "
                f"lat={position[0]:.6f}, "
                f"lon={position[1]:.6f}, "
                f"depth={position[2]:.2f}m"
            )

            image_counter += 1

            # 10. Jaga interval
            time.sleep(max(0, INTERVAL - proc_time))

    except KeyboardInterrupt:
        print("Stop requested by user")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Camera released, program exited cleanly")

if __name__ == "__main__":
    main()
"""




"""
====================================================================================================
ini kode csv yang aman ID nya gak ilang
from ultralytics import YOLO
import cv2
import os
import time
import numpy as np
import csv
from ultralytics.utils.plotting import Annotator

# ---------------- CONFIG ----------------
MODEL_PATH = r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal5\yolo11s\best.pt"
SAVE_FOLDER = r"D:\POC"
CSV_FILE = os.path.join(SAVE_FOLDER, "log_objects.csv")

INTERVAL = 1.5        # detik
AUV_SPEED = 0.5       # m/s

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

    # Siapkan CSV jika belum ada
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["ID", "timestamp", "lat", "lon", "depth", "label", "confidence", "filename"])

    model = YOLO(MODEL_PATH)
    cap = cv2.VideoCapture(0)

    image_counter = 1
    start_time = time.time()
    position = np.array([-6.8900, 107.6100, 5.0], dtype=np.float32)
    last_snapshot_time = time.time()

    try:
        while True:
            snapshot_time = time.time()
            dt = snapshot_time - last_snapshot_time
            last_snapshot_time = snapshot_time

            # 1. Ambil snapshot
            ret, frame = cap.read()
            if not ret:
                break

            # 2. YOLO + anotasi + generate ID per objek
            results = model(frame)
            annotated = frame.copy()
            annotator = Annotator(annotated)

            csv_rows = []

            boxes = results[0].boxes
            if boxes is not None and len(boxes) > 0:
                for i, box in enumerate(boxes):
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])

                    # FLAG ketidakpastian
                    flag = 1 if conf < 0.5 else 0
                    obj_counter = i + 1
                    unique_id = f"{flag}{cls}{image_counter:05d}{obj_counter:03d}"  # string

                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    annotator.box_label([x1, y1, x2, y2], f"ID:{unique_id}")

                    # CSV rows
                    csv_rows.append([
                        str(unique_id),         # ID sebagai string
                        "",                     # placeholder timestamp, nanti diupdate
                        position[0],
                        position[1],
                        position[2],
                        str(cls),
                        conf,
                        generate_filename(image_counter)
                    ])

            annotated = annotator.result()

            # 3. Simpan gambar
            filename = generate_filename(image_counter)
            cv2.imwrite(os.path.join(SAVE_FOLDER, filename), annotated)

            # 4. Update posisi
            position = update_position(position, dt)

            # 5. Hitung proc_time & t_global
            finish_time = time.time()
            proc_time = finish_time - snapshot_time
            t_global = finish_time - start_time

            # 6. Update timestamp CSV dengan t_global
            for row in csv_rows:
                row[1] = f"{t_global:.3f}"

            # 7. Tulis CSV
            if csv_rows:
                with open(CSV_FILE, "a", newline="") as f:
                    writer = csv.writer(f, delimiter=";")
                    writer.writerows(csv_rows)

            # 8. Print log terminal
            print(
                f"[SNAPSHOT] img={filename} | "
                f"proc_time={proc_time:.3f}s | "
                f"t_global={t_global:.2f}s | "
                f"lat={position[0]:.6f}, "
                f"lon={position[1]:.6f}, "
                f"depth={position[2]:.2f}m"
            )

            image_counter += 1

            # 9. Jaga interval
            time.sleep(max(0, INTERVAL - proc_time))

    except KeyboardInterrupt:
        print("Stop requested by user")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Camera released, program exited cleanly")

if __name__ == "__main__":
    main()
"""



"""
==================================================================================================
Ini kode yang udah CSV ya
from ultralytics import YOLO
import cv2
import os
import time
import numpy as np
import csv
from ultralytics.utils.plotting import Annotator

# ---------------- CONFIG ----------------
MODEL_PATH = r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal5\yolo11s\best.pt"
SAVE_FOLDER = r"D:\POC"
CSV_FILE = os.path.join(SAVE_FOLDER, "log_objects.csv")

INTERVAL = 1.5        # detik
AUV_SPEED = 0.5       # m/s

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

    # Siapkan CSV jika belum ada
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["ID", "timestamp", "lat", "lon", "depth", "label", "confidence", "filename"])

    model = YOLO(MODEL_PATH)
    cap = cv2.VideoCapture(0)

    image_counter = 1
    start_time = time.time()
    position = np.array([-6.8900, 107.6100, 5.0], dtype=np.float32)
    last_snapshot_time = time.time()

    try:
        while True:
            snapshot_time = time.time()
            dt = snapshot_time - last_snapshot_time
            last_snapshot_time = snapshot_time

            # 1. Ambil snapshot
            ret, frame = cap.read()
            if not ret:
                break

            # 2. YOLO + anotasi + generate ID per objek
            results = model(frame)
            annotated = frame.copy()
            annotator = Annotator(annotated)

            # Siapkan list untuk CSV
            csv_rows = []

            boxes = results[0].boxes
            if boxes is not None and len(boxes) > 0:
                for i, box in enumerate(boxes):
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    label_text = f"{cls}"  # label jenisnya

                    # FLAG ketidakpastian
                    flag = 1 if conf < 0.5 else 0

                    obj_counter = i + 1
                    unique_id = f"{flag}{cls}{image_counter:05d}{obj_counter:03d}"

                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    annotator.box_label([x1, y1, x2, y2], f"ID:{unique_id}")

                    # Tambahkan ke CSV list
                    timestamp = time.time()
                    csv_rows.append([
                        unique_id,
                        timestamp,
                        position[0],
                        position[1],
                        position[2],
                        cls,
                        conf,
                        generate_filename(image_counter)
                    ])

            annotated = annotator.result()

            # 3. Simpan gambar ke folder
            filename = generate_filename(image_counter)
            cv2.imwrite(os.path.join(SAVE_FOLDER, filename), annotated)

            # 4. Update posisi
            position = update_position(position, dt)

            # 5. Tulis CSV per objek
            if csv_rows:
                with open(CSV_FILE, "a", newline="") as f:
                    writer = csv.writer(f, delimiter=";")
                    writer.writerows(csv_rows)

            # 6. Hitung proc_time dan t_global
            finish_time = time.time()
            proc_time = finish_time - snapshot_time
            t_global = finish_time - start_time

            # 7. Print log terminal
            print(
                f"[SNAPSHOT] img={filename} | "
                f"proc_time={proc_time:.3f}s | "
                f"t_global={t_global:.2f}s | "
                f"lat={position[0]:.6f}, "
                f"lon={position[1]:.6f}, "
                f"depth={position[2]:.2f}m"
            )

            image_counter += 1

            # 8. Jaga interval 1.5 detik
            time.sleep(max(0, INTERVAL - proc_time))

    except KeyboardInterrupt:
        print("Stop requested by user")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Camera released, program exited cleanly")

if __name__ == "__main__":
    main()
"""



"""
========================================================================
ini kode yang udah ada ID nya mang di tiap 1,5 detik snapshot
from ultralytics import YOLO
import cv2
import os
import time
import numpy as np
from ultralytics.utils.plotting import Annotator

# ---------------- CONFIG ----------------
MODEL_PATH = r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal5\yolo11s\best.pt"
SAVE_FOLDER = r"D:\POC"

INTERVAL = 1.5        # detik
AUV_SPEED = 0.5       # m/s

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

    model = YOLO(MODEL_PATH)
    cap = cv2.VideoCapture(0)

    image_counter = 1
    start_time = time.time()

    position = np.array([-6.8900, 107.6100, 5.0], dtype=np.float32)
    last_snapshot_time = time.time()

    try:
        while True:
            snapshot_time = time.time()
            dt = snapshot_time - last_snapshot_time
            last_snapshot_time = snapshot_time

            # 1. SNAPSHOT
            ret, frame = cap.read()
            if not ret:
                break

            # 2. YOLO
            results = model(frame)

            # 3. CUSTOM ANNOTATION DENGAN ID
            annotated = frame.copy()
            annotator = Annotator(annotated)

            boxes = results[0].boxes
            if boxes is not None and len(boxes) > 0:
                for i, box in enumerate(boxes):
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])

                    # FLAG ketidakpastian
                    flag = 1 if conf < 0.5 else 0

                    # COUNTER objek di frame
                    obj_counter = i + 1

                    # GENERATE ID (10 digit, string supaya nol di depan tetap ada)
                    unique_id = f"{flag}{cls}{image_counter:05d}{obj_counter:03d}"

                    # Bounding box koordinat
                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    # Label di box = ID
                    label_text = f"ID:{unique_id}"

                    annotator.box_label([x1, y1, x2, y2], label_text)

            annotated = annotator.result()

            # 4. SAVE
            filename = generate_filename(image_counter)
            cv2.imwrite(os.path.join(SAVE_FOLDER, filename), annotated)

            finish_time = time.time()
            proc_time = finish_time - snapshot_time
            t_global = finish_time - start_time

            # 5. UPDATE LOCATION
            position = update_position(position, dt)

            # 6. PRINT LOG
            print(
                f"[SNAPSHOT] img={filename} | "
                f"proc_time={proc_time:.3f}s | "
                f"t_global={t_global:.2f}s | "
                f"lat={position[0]:.6f}, "
                f"lon={position[1]:.6f}, "
                f"depth={position[2]:.2f}m"
            )

            image_counter += 1

            # 7. JAGA INTERVAL 1.5 DETIK
            time.sleep(max(0, INTERVAL - proc_time))

    except KeyboardInterrupt:
        print("Stop requested by user")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Camera released, program exited cleanly")


if __name__ == "__main__":
    main()
"""


"""
=======================================================================================================================================
ini webcam yang tiap 1,5 detik ya, sudah ada lat long
from ultralytics import YOLO
import cv2
import os
import time
import numpy as np

# ---------------- CONFIG ----------------
MODEL_PATH = r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal5\yolo11s\best.pt"
SAVE_FOLDER = r"D:\POC"

INTERVAL = 1.5        # detik
AUV_SPEED = 0.5       # m/s

VEHICLE_ID = "auv01"
MISSION_ID = "ms03"
# ----------------------------------------


def generate_filename(counter):
    return f"{VEHICLE_ID}_{MISSION_ID}_img{counter:05d}.jpg"


# ===== Dummy Location Model (Masuk Akal) =====
METER_TO_DEG = 1 / 111_111  # meter ke derajat latitude (aproksimasi lokal)

def update_position(pos, dt):
    distance = AUV_SPEED * dt  # meter

    pos[0] += distance * METER_TO_DEG        # latitude
    pos[1] += 0.3 * distance * METER_TO_DEG  # longitude (lebih pelan)
    pos[2] += 0.05 * dt                      # depth (m)

    return pos
# ============================================


def main():
    os.makedirs(SAVE_FOLDER, exist_ok=True)

    model = YOLO(MODEL_PATH)
    cap = cv2.VideoCapture(0)

    image_counter = 1
    start_time = time.time()

    # posisi awal dummy (float32 x 3)
    position = np.array(
        [-6.8900, 107.6100, 5.0], dtype=np.float32
    )  # lat, lon, depth

    last_snapshot_time = time.time()

    while True:
        snapshot_time = time.time()
        dt = snapshot_time - last_snapshot_time
        last_snapshot_time = snapshot_time

        # 1. SNAPSHOT
        ret, frame = cap.read()
        if not ret:
            break

        # 2. YOLO + SAVE
        results = model(frame)
        annotated = results[0].plot()

        filename = generate_filename(image_counter)
        cv2.imwrite(os.path.join(SAVE_FOLDER, filename), annotated)

        finish_time = time.time()

        # 3. TIMING
        proc_time = finish_time - snapshot_time   # snapshot → file tersimpan
        t_global = finish_time - start_time

        # 4. UPDATE LOCATION
        position = update_position(position, dt)

        # 5. PRINT LOG LENGKAP
        print(
            f"[SNAPSHOT] img={filename} | "
            f"proc_time={proc_time:.3f}s | "
            f"t_global={t_global:.2f}s | "
            f"lat={position[0]:.6f}, "
            f"lon={position[1]:.6f}, "
            f"depth={position[2]:.2f}m"
        )

        image_counter += 1

        # 6. JAGA INTERVAL 1.5 DETIK
        time.sleep(max(0, INTERVAL - proc_time))


if __name__ == "__main__":
    main()


"""



"""
=====================================================================================================================
KODE AWALNYA YOLO webcam
from ultralytics import YOLO
import cv2
import os
from datetime import datetime
import time

model = YOLO(r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal5\yolo11s\best.pt")

save_folder = "D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal5\testing\POC"
os.makedirs(save_folder, exist_ok=True)

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame)

    # draw boxes
    annotated = results[0].plot()

    # jika ada deteksi
    if len(results[0].boxes) > 0:
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S-%f")[:-3]
        filename = f"frame_{timestamp}.jpg"
        path = os.path.join(save_folder, filename)
        cv2.imwrite(path, annotated)

        cv2.imshow("Deteksi", annotated)
        cv2.waitKey(1)

        time.sleep(1.5)   # jeda 1.5 detik sambil tetap nunjukkin frame yang sama

    else:
        cv2.imshow("Deteksi", annotated)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
"""