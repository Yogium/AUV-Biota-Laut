# Color mapping (cls, flag) -> BGR
COLOR_MAP = {
    (0,0): (32, 165, 218),   # Fish
    (0,1): (0, 0, 255),      # Fish (unsure)
    (1,0): (150, 0, 0),      # Coral
    (1,1): (0, 0, 255),      # Coral (unsure)
    (2,0): (255, 0, 255),    # Seagrass
    (2,1): (0, 0, 255),      # Seagrass (unsure)
    (3,0): (0, 100, 0),      # Human
    (3,1): (0, 0, 255),      # Human (unsure)
    (4,0): (80, 80, 80),     # Others
    (4,1): (0, 0, 255),      # Others (unsure)
}

# Loads YOLO TensorRT engine into the Jetson's GPU memory
def load_yolo_model(model_path):
    print(f"[SYSTEM] Loading YOLO model into GPU memory from: {model_path}")
    
    # Only import YOLO when this function is called
    from ultralytics import YOLO

    model = YOLO(model_path, task="detect")
    return model

# Run YOLO model for biota inference
def run_yolo_model(model, frame, frame_count, vehicle_id, mission_id):
    # Import annotator only when function called to prevent collision
    from ultralytics.utils.plotting import Annotator

    # Use best parameter from experiment
    results = model.predict(
        source=frame,
        device=0,
        imgsz=1280,
        half=True,
        verbose=False
    )
    
    annotated_frame = frame.copy()
    annotator = Annotator(annotated_frame)
    boxes = results[0].boxes

    filename = f"{vehicle_id}_{mission_id}_img{frame_count:05d}.jpg"
    detections = []
    label_counter = {}

    if boxes is not None and len(boxes) > 0:
        for box in boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])

            # Counter per label for this specific frame
            if cls not in label_counter:
                label_counter[cls] = 1
            else:
                label_counter[cls] += 1
            
            obj_counter = label_counter[cls]

            # Uncertainty flag
            flag = 1 if conf > 0.5 else 0
            flag_text = "Yakin" if flag == 1 else "Tidak Yakin"

            # Unique ID
            unique_id = f"{flag}{cls}{frame_count:05d}{obj_counter:03d}"

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            # Draw bounding box
            color = COLOR_MAP.get((cls, flag), (255, 255, 255))
            annotator.box_label([x1, y1, x2, y2], f"ID:{unique_id}", color=color)

            # Save metadata
            detections.append({
                "ID": unique_id,
                "label": cls,
                "confidence": conf,
                "flag": flag_text
            })

    return annotator.result(), detections, filename