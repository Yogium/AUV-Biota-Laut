from ultralytics import YOLO

# 1. PAKAI FILE .PT (BUKAN .ONNX)
model_path = "/home/krbai/coba_yolo_auv/model_yolo11/yolo11n_datasetfinal5/best.pt"

# 2. Load model
model = YOLO(model_path)

# 3. Export ke format TensorRT (Engine)
print("Sedang 'menjahit' dari .pt ke Engine... (Tunggu 5-10 menit)")
model.export(format="engine", device=0, half=True)

print("SUKSES! Sekarang file 'best.engine' akan muncul.")