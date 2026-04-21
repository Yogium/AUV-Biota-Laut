import serial
import time
import sys

# Update this to match the port you found in the terminal
ARDUINO_PORT = '/dev/ttyUSB0' 
BAUD_RATE = 9600

try:
    # Open the serial connection. timeout=1 ensures the script doesn't hang forever waiting for a response
    ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
    
    print(f"Connected to {ARDUINO_PORT}. Waiting for Arduino to initialize...")
    # Wait 2 seconds after opening the port. Opening a serial port causes the Arduino to reset automatically.
    time.sleep(2) 
    
    def set_light_pwm(value):
        """Sends a PWM value (0-255) to the Arduino."""
        # Ensure the value stays within the 8-bit limit
        value = max(0, min(255, int(value)))
        
        # Format as a string with a newline character, then encode to bytes
        command = f"{value}\n"
        ser.write(command.encode('utf-8'))
        
        # Read the confirmation response from the Arduino
        response = ser.readline().decode('utf-8').strip()
        print(f"Sent: {value} | Arduino Reply: {response}")

    # --- Interactive Input Loop ---
    print("\n--- Interactive PWM Control Ready ---")
    print("Enter a PWM value between 0 (Off) and 255 (Full Brightness).")
    print("Type 'q' or 'exit' to quit.")
    
    while True:
        # Prompt the user for input
        user_input = input("\nEnter PWM value: ").strip().lower()
        
        # Allow the user to quit gracefully
        if user_input in ['q', 'exit', 'quit']:
            print("Turning off the light and exiting...")
            set_light_pwm(0)  # Safety feature: turn off the light before exiting
            break
            
        try:
            # Convert the input to an integer and send it
            pwm_val = int(user_input)
            set_light_pwm(pwm_val)
        except ValueError:
            # Handle the case where the user types letters or symbols instead of numbers
            print("Invalid input! Please enter a valid number (0-255) or 'q' to quit.")

except serial.SerialException as e:
    print(f"Error: Could not connect to Arduino. {e}")
except KeyboardInterrupt:
    # Handles the scenario where you press Ctrl+C to forcefully stop the script
    print("\nProgram interrupted by user. Exiting...")
finally:
    # Always close the port cleanly when the script finishes
    if 'ser' in locals() and ser.is_open:
        # Optional fallback: forcefully send a '0' to turn off the light just in case
        try:
             ser.write(b"0\n")
        except:
             pass
        ser.close()
        print("Serial port closed.")