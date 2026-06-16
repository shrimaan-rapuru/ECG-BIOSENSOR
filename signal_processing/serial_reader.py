import serial
import time
import csv
from datetime import datetime

# Configuration
PORT = 'COM3'
BAUD_RATE = 115200
DURATION = 30  # seconds to record

def read_ecg(port=PORT, baud=BAUD_RATE, duration=DURATION):
    print(f"Connecting to Arduino on {port}...")
    ser = serial.Serial(port, baud, timeout=1)
    time.sleep(2)  # Wait for Arduino to reset
    
    data = []
    timestamps = []
    start_time = time.time()
    
    print(f"Recording for {duration} seconds... Stay still!")
    
    while time.time() - start_time < duration:
        line = ser.readline().decode('utf-8').strip()
        if line == '!':
            continue  # Skip lead-off readings
        try:
            value = int(line)
            data.append(value)
            timestamps.append(time.time() - start_time)
        except ValueError:
            continue
    
    ser.close()
    actual_fs = len(data) / duration
    print(f"Recording complete. {len(data)} samples captured.")
    print(f"Actual sampling rate: {actual_fs:.1f} Hz")
    return timestamps, data
    
    

def save_csv(timestamps, data, filename):
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'ecg_value'])
        for t, v in zip(timestamps, data):
            writer.writerow([round(t, 4), v])
    print(f"Saved to {filename}")

if __name__ == "__main__":
    timestamps, data = read_ecg()
    filename = f"../results/experiment_1/subject_6_resting_trial_5.csv"
    save_csv(timestamps, data, filename)