while True:
    try:
        # Input titik kotak
        x1 = float(input("Masukkan x1: "))
        y1 = float(input("Masukkan y1: "))
        x2 = float(input("Masukkan x2: "))
        y2 = float(input("Masukkan y2: "))
    except ValueError:
        print("Masukkan angka yang valid.")
        continue

    width = abs(x2 - x1)
    height = abs(y2 - y1)

    area = width * height

    if 750 <= area <= 14040:
        print(f"Luas kotak: {area:.2f} m²")
        break
    else:
        print("Area tidak valid. Masukkan titik lain.")

# Input posisi AUV
try:
    x_auv = float(input("Masukkan posisi AUV x: "))
    y_auv = float(input("Masukkan posisi AUV y: "))
except ValueError:
    print("Masukkan angka yang valid.")
    exit()

# Tentukan batas kotak
x_min = min(x1, x2)
x_max = max(x1, x2)
y_min = min(y1, y2)
y_max = max(y1, y2)

# Cek posisi AUV
if x_min <= x_auv <= x_max and y_min <= y_auv <= y_max:
    print("AUV berada di dalam kotak")
else:
    print("AUV berada di luar kotak")




"""
====================================================================================
ini kode awal ya masukin dan ngitung luasnya dan nebak di dalam atau luar
while True:
    try:
        # Input titik kotak
        x1 = float(input("Masukkan x1: "))
        y1 = float(input("Masukkan y1: "))
        x2 = float(input("Masukkan x2: "))
        y2 = float(input("Masukkan y2: "))
    except ValueError:
        print("Masukkan angka yang valid.")
        continue

    width = abs(x2 - x1)
    height = abs(y2 - y1)

    area = width * height

    if 750 <= area <= 14040:
        print(f"Luas kotak: {area:.2f} m²")
        break
    else:
        print("Area tidak valid. Masukkan titik lain.")

# Input posisi AUV
try:
    x_auv = float(input("Masukkan posisi AUV x: "))
    y_auv = float(input("Masukkan posisi AUV y: "))
except ValueError:
    print("Masukkan angka yang valid.")
    exit()

# Tentukan batas kotak
x_min = min(x1, x2)
x_max = max(x1, x2)
y_min = min(y1, y2)
y_max = max(y1, y2)

# Cek posisi AUV
if x_min <= x_auv <= x_max and y_min <= y_auv <= y_max:
    print("AUV berada di dalam kotak")
else:
    print("AUV berada di luar kotak")

"""