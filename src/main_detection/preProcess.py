import cv2
import numpy as np

# Parameters from experiment
A_SHIFT, B_SHIFT = 0, 0
OMEGA, CLAHE_CLIP = 0.75, 1.0
RED_STRENGTH, T_MIN = 10, 0.35

# ========================================================
# PREPROCESSING FUNCTIONS
# ========================================================

# White Balance Function
def white_balance_adaptive(img, cast_thresh=5.0, cast_max=30.0):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    L, A, B = cv2.split(lab)
    A_f, B_f = A.astype(np.float32), B.astype(np.float32)
    mean_A, mean_B = np.mean(A_f), np.mean(B_f)
    color_cast = max(abs(mean_A - 128), abs(mean_B - 128))

    if color_cast < cast_thresh:
        return img, "SKIP"

    k = np.clip((color_cast - cast_thresh) / (cast_max - cast_thresh), 0.0, 1.0)
    A_corr = np.clip(A_f - k * (mean_A - 128) + A_SHIFT, 0, 255).astype(np.uint8)
    B_corr = np.clip(B_f - k * (mean_B - 128) + B_SHIFT, 0, 255).astype(np.uint8)
    return cv2.cvtColor(cv2.merge([L, A_corr, B_corr]), cv2.COLOR_LAB2BGR), "RUN"

# Red Restoration Function
def restore_red_adaptive(img, red_thresh=0.9, red_max_boost=0.6):
    B, G, R = cv2.split(img)
    R_f, G_f = R.astype(np.float32), G.astype(np.float32)
    mean_R, mean_G = np.mean(R_f), np.mean(G_f)
    ratio_RG = mean_R / (mean_G + 1e-6)

    if ratio_RG > red_thresh:
        return img, "SKIP"

    k = np.clip((red_thresh - ratio_RG) / red_thresh, 0.0, 1.0) * red_max_boost
    R_corr = np.clip(R_f * (1.0 + k), 0, 255).astype(np.uint8)
    return cv2.merge([B, G, R_corr]), "RUN"

# CLAHE Function
def clahe_enhance(img):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    L, A, B = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=max(CLAHE_CLIP, 0.1), tileGridSize=(8,8))
    L2 = clahe.apply(L)
    return cv2.cvtColor(cv2.merge([L2, A, B]), cv2.COLOR_LAB2BGR)

# Dehazing Function
def dehaze(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    A = np.percentile(gray, 95)
    t = np.clip(1 - OMEGA * (gray / A), T_MIN, 1.0)
    t_stack = cv2.merge([t, t, t])
    J = (img.astype(np.float32) - A) / t_stack + A
    return np.clip(J, 0, 255).astype(np.uint8)

# Sharpening Function
def sharpen(img):
    blur = cv2.GaussianBlur(img, (3, 3), 0)
    return cv2.addWeighted(img, 1.2, blur, -0.2, 0)

# Gamma Correction Function
def gamma_correct(img, g=1.2):
    inv = 1.0 / g
    table = np.array([(i / 255.0) ** inv * 255 for i in range(256)]).astype("uint8")
    return cv2.LUT(img, table)

# Image Enhancing Pipeline
def enhance_underwater_pipeline(img):
    out, st_wb = white_balance_adaptive(img)
    out, st_rr = restore_red_adaptive(out)
    
    out = clahe_enhance(out)
    out = dehaze(out)
    out = sharpen(out)
    out = gamma_correct(out)
    
    status_msg = f"[WB:{st_wb}] [RED:{st_rr}] [CLAHE:OK] [DEHAZE:OK] [SHARP:OK] [GAMMA:OK]"
    return out, status_msg