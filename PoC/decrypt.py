import encrypt_poc
import os
import json
import csv
from pathlib import Path


def decrypt_csv_file(input_file, output_file=None):
    """
    Decrypt an encrypted CSV file and save to a new file
    
    Args:
        input_file: Path to encrypted CSV file
        output_file: Path to save decrypted data (optional, auto-generates if not provided)
    """
    
    # Check if key file exists
    if not os.path.exists(encrypt_poc.KEY_FILE):
        print(f"[ERROR] Key file not found: {encrypt_poc.KEY_FILE}")
        print("Cannot decrypt without the encryption key.")
        return False
    
    # Load encryption key
    try:
        key = encrypt_poc.load_key()
        print(f"[SUCCESS] Loaded encryption key from {encrypt_poc.KEY_FILE}")
    except Exception as e:
        print(f"[ERROR] Failed to load key: {e}")
        return False
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"[ERROR] Input file not found: {input_file}")
        return False
    
    # Generate output filename if not provided
    if output_file is None:
        base_name = Path(input_file).stem
        output_file = f"{base_name}_decrypted.csv"
    
    # Decrypt and save
    try:
        print(f"[PROCESSING] Reading encrypted file: {input_file}")
        decrypted_rows = []
        fieldnames = None
        error_count = 0
        success_count = 0
        
        with open(input_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip header
                if line_num == 1 and line == 'encrypted_data':
                    print("[INFO] Skipping header row")
                    continue
                
                if not line:
                    continue
                
                try:
                    # Decrypt the line
                    decrypted_json = encrypt_poc.decrypt_line(key, line)
                    
                    # Check for decryption errors
                    if "[ERROR" in decrypted_json:
                        print(f"[WARNING] Line {line_num}: {decrypted_json}")
                        error_count += 1
                        continue
                    
                    # Parse JSON
                    data = json.loads(decrypted_json)
                    decrypted_rows.append(data)
                    
                    # Extract fieldnames from first row
                    if fieldnames is None:
                        fieldnames = list(data.keys())
                    
                    success_count += 1
                    
                except json.JSONDecodeError as e:
                    print(f"[WARNING] Line {line_num}: Invalid JSON after decryption - {e}")
                    error_count += 1
                except Exception as e:
                    print(f"[WARNING] Line {line_num}: {e}")
                    error_count += 1
        
        # Write decrypted data to CSV
        if decrypted_rows and fieldnames:
            with open(output_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(decrypted_rows)
            
            print(f"\n[SUCCESS] Decryption complete!")
            print(f"  - Successfully decrypted: {success_count} rows")
            print(f"  - Errors encountered: {error_count} rows")
            print(f"  - Output file: {output_file}")
            return True
        else:
            print("[ERROR] No valid rows found to decrypt")
            return False
    
    except Exception as e:
        print(f"[ERROR] Failed to decrypt file: {e}")
        return False


def main():
    """Main function to handle decryption"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python decrypt.py <encrypted_csv_file> [output_file]")
        print("Example: python decrypt.py AUV01_MS001_Data.csv")
        print("Example: python decrypt.py AUV01_MS001_Data.csv decrypted_output.csv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = decrypt_csv_file(input_file, output_file)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()