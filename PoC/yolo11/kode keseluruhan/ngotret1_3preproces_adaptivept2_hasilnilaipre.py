import cv2
import numpy as np
import os

# ------------------------------
# 1. Cek CLAHE ringan
def check_adaptive_clahe(img, threshold=30):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    contrast_metric = np.std(gray)
    return contrast_metric < threshold, contrast_metric, threshold

# ------------------------------
# 2. Cek Sharpening ringan
def check_adaptive_sharpen(img, grad_threshold=20):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    grad_mag = np.sqrt(grad_x**2 + grad_y**2)
    grad_mean = np.mean(grad_mag)
    need_sharp = grad_mean < grad_threshold
    return need_sharp, grad_mean, grad_threshold

# ------------------------------
# 3. Cek White Balance ringan
def check_adaptive_white_balance(img, diff_threshold=15):
    B_mean = np.mean(img[:,:,0])
    G_mean = np.mean(img[:,:,1])
    R_mean = np.mean(img[:,:,2])
    max_diff = max(abs(B_mean-R_mean), abs(B_mean-G_mean))
    need_wb = max_diff > diff_threshold
    return need_wb, max_diff, diff_threshold

# ------------------------------
# 4. Apply CLAHE ringan
def apply_clahe(img, clip_limit=1, tile_grid_size=(8,8)):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    l_clahe = clahe.apply(l)
    lab_clahe = cv2.merge((l_clahe, a, b))
    return cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2BGR)

# ------------------------------
# 5. Adaptive Sharpening (kernel dinamis sesuai grad_mean)
def adaptive_sharpening(img, T_target=20, alpha=0.1, iter_max_base=2):
    processed = img.copy()
    _, grad_prev, _ = check_adaptive_sharpen(processed)
    processed_last = processed.copy()  # versi terakhir untuk output

    print(f"Sharpening start: grad_mean = {grad_prev:.2f}, target = {T_target}")

    # Tentukan iterasi maksimum dinamis berdasarkan grad awal
    if grad_prev < 10:
        iter_max = max(iter_max_base, 5)  # blur parah, lebih banyak iterasi
    elif grad_prev < 15:
        iter_max = max(iter_max_base, 3)  # blur sedang
    else:
        iter_max = iter_max_base  # cukup detail, sedikit iterasi

    for i in range(iter_max):
        # Pilih kernel sesuai grad_prev
        if grad_prev < 10:
            kernel = np.array([[0, -0.18, 0],[-0.18, 1.72, -0.18],[0, -0.18, 0]])
        elif grad_prev < 15:
            kernel = np.array([[0, -0.12, 0],[-0.12, 1.48, -0.12],[0, -0.12, 0]])
        else:
            kernel = np.array([[0, -0.07, 0],[-0.07, 1.28, -0.07],[0, -0.07, 0]])

        processed_new = cv2.filter2D(processed, -1, kernel)
        _, grad_new, _ = check_adaptive_sharpen(processed_new)

        # Tentukan alasan berhenti
        if grad_prev >= T_target:
            print(f"Iteration {i+1}: grad_mean={grad_prev:.2f} >= target {T_target}, stop.")
            break
        elif (grad_new - grad_prev) / (grad_prev + 1e-6) < alpha:
            print(f"Iteration {i+1}: increase too small ({grad_prev:.2f} -> {grad_new:.2f}), stop.")
            processed_last = processed_new
            break
        else:
            print(f"Iteration {i+1}: grad_mean {grad_prev:.2f} -> {grad_new:.2f}, kernel applied.")
            processed = processed_new
            grad_prev = grad_new
            processed_last = processed_new

    return processed_last



# ------------------------------
# 6. Apply White Balance ringan
def apply_white_balance(img, strength=0.5):
    result = img.copy().astype(np.float32)
    B, G, R = cv2.split(result)
    K = (np.mean(R)+np.mean(G)+np.mean(B))/3
    R += (K - np.mean(R)) * strength
    G += (K - np.mean(G)) * strength
    B += (K - np.mean(B)) * strength
    result = cv2.merge([B, G, R])
    return np.clip(result, 0, 255).astype(np.uint8)

# ------------------------------
# Fungsi utama (STRUKTUR TETAP)
def adaptive_preprocess_save_smooth(img_path, save_folder):
    os.makedirs(save_folder, exist_ok=True)
    img = cv2.imread(img_path)
    processed = img.copy()

    # --- CLAHE ---
    need_clahe, val_contrast, thresh_contrast = check_adaptive_clahe(processed)
    if need_clahe:
        processed = apply_clahe(processed)
       #pass

    # --- SHARPENING ---
    need_sharp, val_grad, thresh_grad = check_adaptive_sharpen(processed)
    if need_sharp:
        processed = adaptive_sharpening(processed)
       # pass

    # --- WHITE BALANCE ---
    need_wb, val_wb, thresh_wb = check_adaptive_white_balance(processed)
    if need_wb:
        processed = apply_white_balance(processed)
        #pass

    # --- Cek adaptive filter setelah apply ---
    _, val_contrast_post, _ = check_adaptive_clahe(processed)
    _, val_grad_post, _ = check_adaptive_sharpen(processed)
    _, val_wb_post, _ = check_adaptive_white_balance(processed)


    # --- Simpan file ---
    base_name = os.path.basename(img_path)
    save_name = f"semuanya_{base_name}"
    save_path = os.path.join(save_folder, save_name)
    cv2.imwrite(save_path, processed)

    # --- Log ringkas, format lama ---
    print(f"[INFO] {base_name} -> Saved: {save_name}")
    print(f"       Filters: CLAHE : {'ON' if need_clahe else 'OFF'}, "
          f"Sharpening : {'ON' if need_sharp else 'OFF'}, "
          f"WhiteBalance : {'ON' if need_wb else 'OFF'}")
    print(f"       Thresholds: CLAHE : {thresh_contrast}, Sharpening : {thresh_grad}, WB : {thresh_wb}")
    print(f"       Values before apply: CLAHE : {val_contrast:.2f}, Sharpening : {val_grad:.2f}, WB : {val_wb:.2f}")
    print(f"       Values after apply:  CLAHE : {val_contrast_post:.2f}, Sharpening : {val_grad_post:.2f}, WB : {val_wb_post:.2f}")

    return save_path

# ------------------------------
# Contoh penggunaan
img_path = r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal3\testing_preproces2\gb16.png"
save_folder = r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal3\testing_preproces2"

adaptive_preprocess_save_smooth(img_path, save_folder)






"""==========================================================================================
INI KODE UTAMANYA YA

import cv2
import numpy as np
import os

# ------------------------------
# 1. Cek CLAHE ringan
def check_adaptive_clahe(img, threshold=30):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    contrast_metric = np.std(gray)
    return contrast_metric < threshold, contrast_metric, threshold

# ------------------------------
# 2. Cek Sharpening ringan
def check_adaptive_sharpen(img, grad_threshold=20):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    grad_mag = np.sqrt(grad_x**2 + grad_y**2)
    grad_mean = np.mean(grad_mag)
    need_sharp = grad_mean < grad_threshold
    return need_sharp, grad_mean, grad_threshold

# ------------------------------
# 3. Cek White Balance ringan
def check_adaptive_white_balance(img, diff_threshold=15):
    B_mean = np.mean(img[:,:,0])
    G_mean = np.mean(img[:,:,1])
    R_mean = np.mean(img[:,:,2])
    max_diff = max(abs(B_mean-R_mean), abs(B_mean-G_mean))
    need_wb = max_diff > diff_threshold
    return need_wb, max_diff, diff_threshold

# ------------------------------
# 4. Apply CLAHE ringan
def apply_clahe(img, clip_limit=1.0, tile_grid_size=(8,8)):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    l_clahe = clahe.apply(l)
    lab_clahe = cv2.merge((l_clahe, a, b))
    return cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2BGR)

# ------------------------------
# 5. Adaptive Sharpening (kernel dinamis sesuai grad_mean)
def adaptive_sharpening(img, T_target=20, alpha=0.1, iter_max_base=2):
    processed = img.copy()
    _, grad_prev, _ = check_adaptive_sharpen(processed)
    processed_last = processed.copy()  # versi terakhir untuk output

    print(f"Sharpening start: grad_mean = {grad_prev:.2f}, target = {T_target}")

    # Tentukan iterasi maksimum dinamis berdasarkan grad awal
    if grad_prev < 10:
        iter_max = max(iter_max_base, 5)  # blur parah, lebih banyak iterasi
    elif grad_prev < 15:
        iter_max = max(iter_max_base, 3)  # blur sedang
    else:
        iter_max = iter_max_base  # cukup detail, sedikit iterasi

    for i in range(iter_max):
        # Pilih kernel sesuai grad_prev
        if grad_prev < 10:
            kernel = np.array([[0, -0.18, 0],[-0.18, 1.72, -0.18],[0, -0.18, 0]])
        elif grad_prev < 15:
            kernel = np.array([[0, -0.12, 0],[-0.12, 1.48, -0.12],[0, -0.12, 0]])
        else:
            kernel = np.array([[0, -0.07, 0],[-0.07, 1.28, -0.07],[0, -0.07, 0]])

        processed_new = cv2.filter2D(processed, -1, kernel)
        _, grad_new, _ = check_adaptive_sharpen(processed_new)

        # Tentukan alasan berhenti
        if grad_prev >= T_target:
            print(f"Iteration {i+1}: grad_mean={grad_prev:.2f} >= target {T_target}, stop.")
            break
        elif (grad_new - grad_prev) / (grad_prev + 1e-6) < alpha:
            print(f"Iteration {i+1}: increase too small ({grad_prev:.2f} -> {grad_new:.2f}), stop.")
            processed_last = processed_new
            break
        else:
            print(f"Iteration {i+1}: grad_mean {grad_prev:.2f} -> {grad_new:.2f}, kernel applied.")
            processed = processed_new
            grad_prev = grad_new
            processed_last = processed_new

    return processed_last



# ------------------------------
# 6. Apply White Balance ringan
def apply_white_balance(img, strength=0.5):
    result = img.copy().astype(np.float32)
    B, G, R = cv2.split(result)
    K = (np.mean(R)+np.mean(G)+np.mean(B))/3
    R += (K - np.mean(R)) * strength
    G += (K - np.mean(G)) * strength
    B += (K - np.mean(B)) * strength
    result = cv2.merge([B, G, R])
    return np.clip(result, 0, 255).astype(np.uint8)

# ------------------------------
# Fungsi utama (STRUKTUR TETAP)
def adaptive_preprocess_save_smooth(img_path, save_folder):
    os.makedirs(save_folder, exist_ok=True)
    img = cv2.imread(img_path)
    processed = img.copy()

    # --- CLAHE ---
    need_clahe, val_contrast, thresh_contrast = check_adaptive_clahe(processed)
    if need_clahe:
        #processed = apply_clahe(processed)
        pass

    # --- SHARPENING ---
    need_sharp, val_grad, thresh_grad = check_adaptive_sharpen(processed)
    if need_sharp:
        #processed = adaptive_sharpening(processed)
        pass

    # --- WHITE BALANCE ---
    need_wb, val_wb, thresh_wb = check_adaptive_white_balance(processed)
    if need_wb:
        processed = apply_white_balance(processed)
        #pass

    # --- Cek adaptive filter setelah apply ---
    _, val_contrast_post, _ = check_adaptive_clahe(processed)
    _, val_grad_post, _ = check_adaptive_sharpen(processed)
    _, val_wb_post, _ = check_adaptive_white_balance(processed)


    # --- Simpan file ---
    base_name = os.path.basename(img_path)
    save_name = f"1mang_irwan2{base_name}"
    save_path = os.path.join(save_folder, save_name)
    cv2.imwrite(save_path, processed)

    # --- Log ringkas, format lama ---
    print(f"[INFO] {base_name} -> Saved: {save_name}")
    print(f"       Filters: CLAHE : {'ON' if need_clahe else 'OFF'}, "
          f"Sharpening : {'ON' if need_sharp else 'OFF'}, "
          f"WhiteBalance : {'ON' if need_wb else 'OFF'}")
    print(f"       Thresholds: CLAHE : {thresh_contrast}, Sharpening : {thresh_grad}, WB : {thresh_wb}")
    print(f"       Values before apply: CLAHE : {val_contrast:.2f}, Sharpening : {val_grad:.2f}, WB : {val_wb:.2f}")
    print(f"       Values after apply:  CLAHE : {val_contrast_post:.2f}, Sharpening : {val_grad_post:.2f}, WB : {val_wb_post:.2f}")

    return save_path

# ------------------------------
# Contoh penggunaan
img_path = r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal3\testing_preproces\gb1.jpg"
save_folder = r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal3\testing_preproces"

adaptive_preprocess_save_smooth(img_path, save_folder)


"""


"""========================================================================================================================================================
xxxxx

"""



"""========================================================================================================================================================
xxxxx

"""


"""========================================================================================================================================================
xxxxx

"""

"""========================================================================================================================================================
xxxxx

"""



