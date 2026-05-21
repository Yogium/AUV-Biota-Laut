import json
import os
import cv2

def save_image_local(image_matrix, filename, subfolder="", config_path="setup.json"):
    """
    Reads the target base folder from setup.json, appends an optional subfolder, 
    and saves the OpenCV image matrix to disk without changing the filename.
    """
    # 1. Load the configuration file safely
    try:
        with open(config_path, 'r') as file:
            config = json.load(file)
    except FileNotFoundError:
        print(f"[ERROR] {config_path} not found. Defaulting to 'images' folder.")
        config = {}
    except json.JSONDecodeError:
        print(f"[ERROR] {config_path} is invalid JSON. Defaulting to 'images' folder.")
        config = {}

    # 2. Extract the base folder path (default to 'images' if missing)
    base_folder = config.get("image_folder", "images")

    # 3. Construct the target directory (e.g., images/preprocessed)
    target_folder = os.path.join(base_folder, subfolder)

    # 4. Create the nested directories if they don't already exist
    os.makedirs(target_folder, exist_ok=True)

    # 5. Construct the full file path with the original filename
    file_path = os.path.join(target_folder, filename)

    # 6. Save using OpenCV directly
    try:
        compression_params = [int(cv2.IMWRITE_JPEG_QUALITY), 70]
        cv2.imwrite(file_path, image_matrix, compression_params)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save image {filename} locally: {e}")
        return False