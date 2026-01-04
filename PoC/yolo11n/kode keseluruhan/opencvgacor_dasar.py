import cv2
import numpy as np
import os

# ------------------------------
# Default parameter (sesuai website)
A_SHIFT = 0        # fine-tune green-red balance
B_SHIFT = 0       # fine-tune blue-yellow balance
OMEGA = 0.75       # dehazing strength
CLAHE_CLIP = 1.0   # CLAHE clip limit
RED_STRENGTH = 10  # red channel restoration intensity
T_MIN = 0.35       # minimum transmission for dehazing

import matplotlib.pyplot as plt

import time  # <-- tambahkan di atas

def process_and_save(img_path, save_folder):
    os.makedirs(save_folder, exist_ok=True)
    img = cv2.imread(img_path)

    start_time = time.time()          # <--- mulai hitung
    enhanced = enhance_underwater(img)
    end_time = time.time()            # <--- selesai

    base_name = os.path.basename(img_path)
    save_name = f"enhanced_{base_name}"
    save_path = os.path.join(save_folder, save_name)
    cv2.imwrite(save_path, enhanced)

    print(f"[INFO] Saved enhanced image: {save_name}")
    print(f"[INFO] Processing time: {end_time - start_time:.2f} detik")  # durasi

    return save_path



# ------------------------------
# Fungsi tampilkan histogram Red channel
def show_red_histogram(img, title="Red Channel Histogram"):
    """
    Menampilkan histogram Red channel sebagai pop-up.
    img   : input BGR image
    title : judul plot
    """
    _, _, r = cv2.split(img)

    plt.figure(figsize=(6,4))
    plt.title(title)
    plt.hist(r.ravel(), bins=256, range=(0,255), color='red')
    plt.xlabel("Intensity")
    plt.ylabel("Pixel Count")
    plt.tight_layout()
    plt.show()  # <-- ini akan munculin pop-up

# ------------------------------
# 1. White Balance (LAB)
def white_balance(img):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    L, A, B = cv2.split(lab)
    A = A.astype(np.float32)
    B = B.astype(np.float32)
 
 
    A = A - (np.mean(A) - 128) + A_SHIFT
    B = B - (np.mean(B) - 128) + B_SHIFT
 
 
    A = np.clip(A, 0, 255).astype(np.uint8)
    B = np.clip(B, 0, 255).astype(np.uint8)
 
 
    return cv2.cvtColor(cv2.merge([L, A, B]), cv2.COLOR_LAB2BGR)


# ------------------------------
# 1. White Balance (LAB)
def white_balance_adaptive(img,
                            cast_thresh=5.0,
                            cast_max=30.0,
                            A_SHIFT=0.0,
                            B_SHIFT=0.0,
                            verbose=True):

    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    L, A, B = cv2.split(lab)

    A_f = A.astype(np.float32)
    B_f = B.astype(np.float32)

    mean_A = np.mean(A_f)
    mean_B = np.mean(B_f)

    # 1. Color cast measurement (before)
    delta_A = abs(mean_A - 128)
    delta_B = abs(mean_B - 128)
    color_cast_before = max(delta_A, delta_B)

    if verbose:
        print(f"[WB] Color cast before WB: {color_cast_before:.2f}")

    # 2. Decision
    if color_cast_before < cast_thresh:
        if verbose:
            print("[WB] Cast below threshold, WB skipped.")
        return img

    # 3. Adaptive gain
    k = np.clip(
        (color_cast_before - cast_thresh) / (cast_max - cast_thresh),
        0.0, 1.0
    )

    # 4. Correction
    A_corr = A_f - k * (mean_A - 128) + A_SHIFT
    B_corr = B_f - k * (mean_B - 128) + B_SHIFT

    # 5. Measure after WB (langsung, tanpa ulang proses)
    mean_A_corr = np.mean(A_corr)
    mean_B_corr = np.mean(B_corr)
    color_cast_after = max(abs(mean_A_corr - 128), abs(mean_B_corr - 128))

    if verbose:
        print(f"[WB] WB strength k       : {k:.2f}")
        print(f"[WB] Color cast after WB : {color_cast_after:.2f}")

    A_corr = np.clip(A_corr, 0, 255).astype(np.uint8)
    B_corr = np.clip(B_corr, 0, 255).astype(np.uint8)

    lab_corr = cv2.merge([L, A_corr, B_corr])
    return cv2.cvtColor(lab_corr, cv2.COLOR_LAB2BGR)

# ------------------------------
# 2. Red Channel Restoration
def restore_red_adaptive(img,
                         red_thresh=0.9,
                         red_max_boost=0.6,
                         verbose=True):

    # 1. Split channel
    B, G, R = cv2.split(img)

    R_f = R.astype(np.float32)
    G_f = G.astype(np.float32)

    # 2. Statistik dasar
    mean_R = np.mean(R_f)
    mean_G = np.mean(G_f)



    if verbose:
        print(f"[RED] mean_R={mean_R:.2f}, mean_G={mean_G:.2f}")
       

    # 3. Decision: apakah red collapse?
    ratio_RG = mean_R / (mean_G + 1e-6)

    if ratio_RG > red_thresh:
        if verbose:
            print("[RED] Red channel healthy, skip compensation.")
        return img

    # 4. Adaptive strength
    k = np.clip(
        (red_thresh - ratio_RG) / red_thresh,
        0.0, 1.0
    ) * red_max_boost

    if verbose:
        print(f"[RED] Red boost strength k = {k:.2f}")

    # 5. Red compensation (gain-based, bukan histogram)
    R_corr = R_f * (1.0 + k)

    R_corr = np.clip(R_corr, 0, 255).astype(np.uint8)
    
    mean_R_after = np.mean(R_corr)
    if verbose:
        print(f"[RED] mean_R after correction = {mean_R_after:.2f}")
    
    return cv2.merge([B, G, R_corr])


# ------------------------------
# 2. Red Channel Restoration
def restore_red(img):
    b, g, r = cv2.split(img)
    boost = cv2.equalizeHist(r)
    strength = RED_STRENGTH / 100.0
    r_new = cv2.addWeighted(r, 1 - strength, boost, strength, 0)
    return cv2.merge([b, g, r_new])



# ------------------------------
# 3. CLAHE (Luminance only)
def clahe_enhance(img):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    L, A, B = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=max(CLAHE_CLIP, 0.1))   
    L2 = clahe.apply(L)
    return cv2.cvtColor(cv2.merge([L2, A, B]), cv2.COLOR_LAB2BGR)

# ------------------------------
# Fungsi tampilkan histogram L channel
def show_L_histogram(img, title="L Channel Histogram"):
    """
    Menampilkan histogram L channel (luminance) sebagai pop-up.
    img   : input BGR image
    title : judul plot
    """
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    L, _, _ = cv2.split(lab)

    plt.figure(figsize=(6,4))
    plt.title(title)
    plt.hist(L.ravel(), bins=256, range=(0,255))
    plt.xlabel("Intensity")
    plt.ylabel("Pixel Count")
    plt.tight_layout()
    plt.show()


# ------------------------------
# 4. Dehazing 
def dehaze(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    A = np.percentile(gray, 95)
    t = 1 - OMEGA * (gray / A)
    t = np.clip(t, T_MIN, 1.0)
    t = cv2.merge([t, t, t])
    J = (img.astype(np.float32) - A) / t + A
    return np.clip(J, 0, 255).astype(np.uint8)

# ------------------------------
# 5. Adaptive Unsharp Maskingx
def sharpness_metric(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    grad_mag = np.sqrt(grad_x**2 + grad_y**2)
    return np.mean(grad_mag)


def sharpen(img):
    sharp_before = sharpness_metric(img)

    blur = cv2.GaussianBlur(img, (3, 3), 0)
    out = cv2.addWeighted(img, 1.2, blur, -0.2, 0)

    sharp_after = sharpness_metric(out)

    print(f"[SHARP] before = {sharp_before:.2f}, after = {sharp_after:.2f}")

    return out


# ------------------------------
# 6. Gamma Correction
def gamma_correct(img, g=1.1):
    inv = 1.0 / g
    table = np.array([(i / 255.0) ** inv * 255 for i in range(256)]).astype("uint8")
    return cv2.LUT(img, table)

# ------------------------------
# 7. Full pipeline
def enhance_underwater(img):
    out = img.copy()
    
    
    out = white_balance_adaptive(out)   #===========================--------------------===============
    #show_red_histogram(out, title="Red Channel sebelum Adaptive Restoration")
    out = restore_red_adaptive(out)
    #show_red_histogram(out, title="Red Channel after Adaptive Restoration A")
    show_L_histogram(out, title="L Channel sebelum CLAHE")
    out = clahe_enhance(out)
    show_L_histogram(out, title="L Channel setelah CLAHE")
    out = dehaze(out)
    out = sharpen(out)
    out = gamma_correct(out)
    return out

# ------------------------------
# 8. Run and save
def process_and_save(img_path, save_folder):
    os.makedirs(save_folder, exist_ok=True)
    img = cv2.imread(img_path)
    enhanced = enhance_underwater(img)
    
    base_name = os.path.basename(img_path)
    save_name = f"nabielrrB_{base_name}"
    save_path = os.path.join(save_folder, save_name)
    cv2.imwrite(save_path, enhanced)
    
    print(f"[INFO] Saved enhanced image: {save_name}")
    return save_path


def process_folder(input_folder, save_folder, exts=(".png", ".jpg", ".jpeg")):
    os.makedirs(save_folder, exist_ok=True)
    total_start = time.time()  # waktu total untuk semua gambar

    for fname in sorted(os.listdir(input_folder)):
        if fname.lower().endswith(exts):
            img_path = os.path.join(input_folder, fname)
            img = cv2.imread(img_path)

            if img is None:
                print(f"[WARNING] Gagal baca: {fname}")
                continue

            start_time = time.time()
            enhanced = enhance_underwater(img)
            end_time = time.time()

            save_path = os.path.join(save_folder, f"6wb'_rr'_cl1_dh_sh02_gm11_{fname}") 
            cv2.imwrite(save_path, enhanced)
            print(f"[INFO] Processed: {fname} in {end_time - start_time:.2f} detik")

    total_end = time.time()
    print(f"[INFO] Total processing time: {total_end - total_start:.2f} detik")
            

# ------------------------------
# Contoh penggunaan
input_folder = r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal5\testing\datamentah"
save_folder  = r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal5\testing\ngotret aja sih"

#process_and_save(input_folder, save_folder)
process_folder(input_folder, save_folder)


"""
catetan default nama file semua proses yak =============================
f"6wb'_rr'_cl1_dh_sh02_gm11_{fname}")
f"6wb_rr_cl_dh_sh_gm_{fname}")
f"7tprr_wb'_cl_dh_sh_gm_{fname}")
    
================================================================================
INI KODE ORIGINALNYA
import cv2
import numpy as np
import os

# ------------------------------
# Default parameter (sesuai website)
A_SHIFT = 0        # fine-tune green-red balance
B_SHIFT = 0       # fine-tune blue-yellow balance
OMEGA = 0.75       # dehazing strength
CLAHE_CLIP = 1.0   # CLAHE clip limit
RED_STRENGTH = 10  # red channel restoration intensity
T_MIN = 0.35       # minimum transmission for dehazing

import matplotlib.pyplot as plt

import time  # <-- tambahkan di atas

def process_and_save(img_path, save_folder):
    os.makedirs(save_folder, exist_ok=True)
    img = cv2.imread(img_path)

    start_time = time.time()          # <--- mulai hitung
    enhanced = enhance_underwater(img)
    end_time = time.time()            # <--- selesai

    base_name = os.path.basename(img_path)
    save_name = f"enhanced_{base_name}"
    save_path = os.path.join(save_folder, save_name)
    cv2.imwrite(save_path, enhanced)

    print(f"[INFO] Saved enhanced image: {save_name}")
    print(f"[INFO] Processing time: {end_time - start_time:.2f} detik")  # durasi

    return save_path



# ------------------------------
# Fungsi tampilkan histogram Red channel
def show_red_histogram(img, title="Red Channel Histogram"):
    
    #Menampilkan histogram Red channel sebagai pop-up.
    #img   : input BGR image
    #title : judul plot
    
    _, _, r = cv2.split(img)

    plt.figure(figsize=(6,4))
    plt.title(title)
    plt.hist(r.ravel(), bins=256, range=(0,255), color='red')
    plt.xlabel("Intensity")
    plt.ylabel("Pixel Count")
    plt.tight_layout()
    plt.show()  # <-- ini akan munculin pop-up

# ------------------------------
# 1. White Balance (LAB)
def white_balance(img):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    L, A, B = cv2.split(lab)
    A = A.astype(np.float32)
    B = B.astype(np.float32)
 
 
    A = A - (np.mean(A) - 128) + A_SHIFT
    B = B - (np.mean(B) - 128) + B_SHIFT
 
 
    A = np.clip(A, 0, 255).astype(np.uint8)
    B = np.clip(B, 0, 255).astype(np.uint8)
 
 
    return cv2.cvtColor(cv2.merge([L, A, B]), cv2.COLOR_LAB2BGR)


# ------------------------------
# 1. White Balance (LAB)
def white_balance_adaptive(img,
                            cast_thresh=5.0,
                            cast_max=30.0,
                            A_SHIFT=0.0,
                            B_SHIFT=0.0,
                            verbose=True):

    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    L, A, B = cv2.split(lab)

    A_f = A.astype(np.float32)
    B_f = B.astype(np.float32)

    mean_A = np.mean(A_f)
    mean_B = np.mean(B_f)

    # 1. Color cast measurement (before)
    delta_A = abs(mean_A - 128)
    delta_B = abs(mean_B - 128)
    color_cast_before = max(delta_A, delta_B)

    if verbose:
        print(f"[WB] Color cast before WB: {color_cast_before:.2f}")

    # 2. Decision
    if color_cast_before < cast_thresh:
        if verbose:
            print("[WB] Cast below threshold, WB skipped.")
        return img

    # 3. Adaptive gain
    k = np.clip(
        (color_cast_before - cast_thresh) / (cast_max - cast_thresh),
        0.0, 1.0
    )

    # 4. Correction
    A_corr = A_f - k * (mean_A - 128) + A_SHIFT
    B_corr = B_f - k * (mean_B - 128) + B_SHIFT

    # 5. Measure after WB (langsung, tanpa ulang proses)
    mean_A_corr = np.mean(A_corr)
    mean_B_corr = np.mean(B_corr)
    color_cast_after = max(abs(mean_A_corr - 128), abs(mean_B_corr - 128))

    if verbose:
        print(f"[WB] WB strength k       : {k:.2f}")
        print(f"[WB] Color cast after WB : {color_cast_after:.2f}")

    A_corr = np.clip(A_corr, 0, 255).astype(np.uint8)
    B_corr = np.clip(B_corr, 0, 255).astype(np.uint8)

    lab_corr = cv2.merge([L, A_corr, B_corr])
    return cv2.cvtColor(lab_corr, cv2.COLOR_LAB2BGR)

# ------------------------------
# 2. Red Channel Restoration
def restore_red_adaptive(img,
                         red_thresh=0.9,
                         red_max_boost=0.6,
                         verbose=True):

    # 1. Split channel
    B, G, R = cv2.split(img)

    R_f = R.astype(np.float32)
    G_f = G.astype(np.float32)

    # 2. Statistik dasar
    mean_R = np.mean(R_f)
    mean_G = np.mean(G_f)



    if verbose:
        print(f"[RED] mean_R={mean_R:.2f}, mean_G={mean_G:.2f}")
       

    # 3. Decision: apakah red collapse?
    ratio_RG = mean_R / (mean_G + 1e-6)

    if ratio_RG > red_thresh:
        if verbose:
            print("[RED] Red channel healthy, skip compensation.")
        return img

    # 4. Adaptive strength
    k = np.clip(
        (red_thresh - ratio_RG) / red_thresh,
        0.0, 1.0
    ) * red_max_boost

    if verbose:
        print(f"[RED] Red boost strength k = {k:.2f}")

    # 5. Red compensation (gain-based, bukan histogram)
    R_corr = R_f * (1.0 + k)

    R_corr = np.clip(R_corr, 0, 255).astype(np.uint8)
    
    mean_R_after = np.mean(R_corr)
    if verbose:
        print(f"[RED] mean_R after correction = {mean_R_after:.2f}")
    
    return cv2.merge([B, G, R_corr])


# ------------------------------
# 2. Red Channel Restoration
def restore_red(img):
    b, g, r = cv2.split(img)
    boost = cv2.equalizeHist(r)
    strength = RED_STRENGTH / 100.0
    r_new = cv2.addWeighted(r, 1 - strength, boost, strength, 0)
    return cv2.merge([b, g, r_new])



# ------------------------------
# 3. CLAHE (Luminance only)
def clahe_enhance(img):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    L, A, B = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=max(CLAHE_CLIP, 0.1))   
    L2 = clahe.apply(L)
    return cv2.cvtColor(cv2.merge([L2, A, B]), cv2.COLOR_LAB2BGR)

# ------------------------------
# 4. Dehazing 
def dehaze(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    A = np.percentile(gray, 95)
    t = 1 - OMEGA * (gray / A)
    t = np.clip(t, T_MIN, 1.0)
    t = cv2.merge([t, t, t])
    J = (img.astype(np.float32) - A) / t + A
    return np.clip(J, 0, 255).astype(np.uint8)

# ------------------------------
# 5. Adaptive Unsharp Maskingx
def sharpness_metric(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    grad_mag = np.sqrt(grad_x**2 + grad_y**2)
    return np.mean(grad_mag)


def sharpen(img):
    sharp_before = sharpness_metric(img)

    blur = cv2.GaussianBlur(img, (3, 3), 0)
    out = cv2.addWeighted(img, 1.2, blur, -0.2, 0)

    sharp_after = sharpness_metric(out)

    print(f"[SHARP] before = {sharp_before:.2f}, after = {sharp_after:.2f}")

    return out


# ------------------------------
# 6. Gamma Correction
def gamma_correct(img, g=1.1):
    inv = 1.0 / g
    table = np.array([(i / 255.0) ** inv * 255 for i in range(256)]).astype("uint8")
    return cv2.LUT(img, table)

# ------------------------------
# 7. Full pipeline
def enhance_underwater(img):
    out = img.copy()
    
    
    out = white_balance_adaptive(out)   #===========================--------------------===============
    #show_red_histogram(out, title="Red Channel sebelum Adaptive Restoration")
    out = restore_red_adaptive(out)
    #show_red_histogram(out, title="Red Channel after Adaptive Restoration A")
    out = clahe_enhance(out)
    out = dehaze(out)
    out = sharpen(out)
    out = gamma_correct(out)
    return out

# ------------------------------
# 8. Run and save
def process_and_save(img_path, save_folder):
    os.makedirs(save_folder, exist_ok=True)
    img = cv2.imread(img_path)
    enhanced = enhance_underwater(img)
    
    base_name = os.path.basename(img_path)
    save_name = f"nabielrrB_{base_name}"
    save_path = os.path.join(save_folder, save_name)
    cv2.imwrite(save_path, enhanced)
    
    print(f"[INFO] Saved enhanced image: {save_name}")
    return save_path


def process_folder(input_folder, save_folder, exts=(".png", ".jpg", ".jpeg")):
    os.makedirs(save_folder, exist_ok=True)
    total_start = time.time()  # waktu total untuk semua gambar

    for fname in sorted(os.listdir(input_folder)):
        if fname.lower().endswith(exts):
            img_path = os.path.join(input_folder, fname)
            img = cv2.imread(img_path)

            if img is None:
                print(f"[WARNING] Gagal baca: {fname}")
                continue

            start_time = time.time()
            enhanced = enhance_underwater(img)
            end_time = time.time()

            save_path = os.path.join(save_folder, f"6wb'_rr'_cl1_dh_sh02_gm11_{fname}") 
            cv2.imwrite(save_path, enhanced)
            print(f"[INFO] Processed: {fname} in {end_time - start_time:.2f} detik")

    total_end = time.time()
    print(f"[INFO] Total processing time: {total_end - total_start:.2f} detik")
            

# ------------------------------
# Contoh penggunaan
input_folder = r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal5\testing\datamentah"
save_folder  = r"D:\KULIAH ITB Daffa\SEM 7\PERTAAN\peryoloan\model\model_datasetfinal5\testing\ngotret aja sih"

#process_and_save(input_folder, save_folder)
process_folder(input_folder, save_folder)

"""


"""
================================================================================================================================================================
INI KODE UNTUK YANG 



"""
