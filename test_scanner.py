import sys
from src.scanner.kojack import KojackScanner

def test_kojack():
    print("Testing Kojack Scanner Connection...")
    scanner = KojackScanner()
    
    count = scanner.get_device_count()
    print(f"Device count: {count}")
    
    if count > 0:
        print("Attempting to open the first device (Index 0)...")
        if scanner.open_device(0):
            print("SUCCESS! Kojack Scanner initialized and opened.")
            scanner.close_device()
            print("Device closed cleanly.")
        else:
            print("FAILED to open the device.")
    else:
        print("No IB scanners detected. Please ensure drivers are installed and device is plugged in.")

if __name__ == "__main__":
    test_kojack()
