import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Output Files
ENCRYPTED_FILE = "m01_encrypted.txt"
KEY_FILE = "m01.key"

def generate_key():
    # Generate random AES key
    key = AESGCM.generate_key(bit_length=256)
    with open(KEY_FILE, "wb") as f:
        f.write(key)
    print(f"[STATUS] New Key generated and saved to: {KEY_FILE}")
    return key

def load_key():
    # Load key from storage
    with open(KEY_FILE, "rb") as f:
        return f.read()

def encrypt_line(key, plaintext_string):
    # Encrypt a single string and returns safe Base64 string
    # Convert string to byte
    data_bytes = plaintext_string.encode('utf-8')

    # Generate unique Nonce
    nonce = os.urandom(12)

    # Encrypt
    aesgcm = AESGCM(key)
    cipher_txt = aesgcm.encrypt(nonce, data_bytes, associated_data=None)

    # Combine Nonce + Ciphertext
    full_pkg = nonce + cipher_txt

    # Convert to Base64 string
    return base64.b64encode(full_pkg).decode('utf-8')

def decrypt_line(key, encrypted_string):
    # Take Base64 string --> bytes --> decrypts
    try:
        # 1. Decode Base64 back to raw binary
        full_pkg = base64.b64decode(encrypted_string)
        
        # 2. Split Nonce (first 12 bytes) and Ciphertext
        nonce = full_pkg[:12]
        cipher_txt = full_pkg[12:]
        
        # 3. Decrypt
        aesgcm = AESGCM(key)
        decrypted_bytes = aesgcm.decrypt(nonce, cipher_txt, associated_data=None)
        
        return decrypted_bytes.decode('utf-8')
        
    except Exception:
        return "[ERROR: TAMPER DETECTED OR KEY INVALID]"

# --- MAIN EXECUTION FLOW ---
if __name__ == "__main__":
    # Setup
    key = generate_key()
    # Dummy input
    input_line = "001,10:00:00,-8.760,115.121,3,Fish,0.76,img_001.jpg"
    # Encrypt line
    encrypted_str = encrypt_line(key, input_line)
    print(encrypted_str)
    # Decrypt line
    decrypted_str = decrypt_line(key, encrypted_str)
    print(decrypted_str)