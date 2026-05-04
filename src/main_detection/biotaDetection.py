# ========================================================
# BIOTA DETECTION WITH YOLO
# ========================================================

# Loads YOLO TensorRT engine into the Jetson's GPU memory
def load_yolo_model(model_path):
    print(f"[SYSTEM] Loading YOLO model into GPU memory from: {model_path}")
    
    # Only import YOLO when this function is called
    from ultralytics import YOLO

    model = YOLO(model_path, task="detect")
    return model

# Run YOLO model for biota inference
def run_yolo_model(model, frame):
    # Use best parameter from experiment
    results = model.predict(
        source=frame,
        device=0,
        imgsz=640,
        half=True,
        verbose=False
    )

    # Generate frames with bounding boxes
    yolo_frame = results[0].plot()

    # # Extract processing speed data
    # yolo_speeds = results[0].speed
    # yolo_pre = yolo_speeds['preprocess'] / 1000.0
    # yolo_inf = yolo_speeds['inference'] / 1000.0
    # yolo_post = yolo_speeds['postprocess'] / 1000.0
    # yolo_total = yolo_pre + yolo_inf + yolo_post

    # # Package timings into a clean dictionary
    # timing_data = {
    #     'preprocess': yolo_pre,
    #     'inference': yolo_inf,
    #     'postprocess': yolo_post,
    #     'total': yolo_total
    # }

    return yolo_frame