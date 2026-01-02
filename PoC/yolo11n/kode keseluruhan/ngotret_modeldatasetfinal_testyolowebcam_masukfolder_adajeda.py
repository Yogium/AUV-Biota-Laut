from ultralytics import YOLO
import cv2
import os
from datetime import datetime
import time

model = YOLO(r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal5\best.pt")

save_folder = "detected_frames"
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
