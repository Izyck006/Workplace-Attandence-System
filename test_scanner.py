import sys
import os
import time
import datetime
from src.scanner.kojack import KojackScanner
from src.services.fingerprint import FingerprintMatcher
import cv2
import numpy as np

try:
    import winsound
except ImportError:
    winsound = None

def run_scanner_test():
    print("=" * 60)
    print("      INTEGRATED BIOMETRICS SCANNER TEST UTILITY")
    print("=" * 60)
    
    scanner = KojackScanner()
    count = scanner.get_device_count()
    print(f"[*] Detecting scanners... Found: {count} device(s)")
    
    if count == 0:
        print("[!] No scanners detected. Ensure USB cable is connected.")
        return False
        
    print("[*] Opening scanner device (index 0)...")
    if not scanner.open_device(0):
        print("[!] Failed to open scanner.")
        return False
        
    supported_type = scanner.get_supported_image_type()
    type_names = {
        1: "ROLL_SINGLE_FINGER",
        2: "FLAT_SINGLE_FINGER (Columbo / Single Finger)",
        3: "FLAT_TWO_FINGERS (Watson / Dual Finger)",
        4: "FLAT_FOUR_FINGERS (Kojak / Four Finger)"
    }
    mode_desc = type_names.get(supported_type, f"Type {supported_type}")
    print(f"[+] Scanner opened successfully!")
    print(f"[+] Hardware Capture Mode: {mode_desc}")
    print(f"[+] Resolution: 500 DPI")
    
    print("\n[*] Starting capture...")
    if not scanner.begin_capture():
        print("[!] Failed to begin capture.")
        scanner.close_device()
        return False
        
    print("\n" + "-" * 60)
    print("-> PLEASE PLACE YOUR FINGER ON THE SCANNER PLATEN NOW...")
    print("   (Testing live capture for up to 15 seconds. Ctrl+C to stop)")
    print("-" * 60 + "\n")
    
    captured = False
    start_time = time.time()
    good_frames = 0
    last_state = None
    
    try:
        while time.time() - start_time < 15:
            success, img_bytes, w, h, is_final, finger_state = scanner.block_get_image(ignore_preview=False)
            
            if success and img_bytes and w > 0 and h > 0:
                if finger_state != last_state:
                    if finger_state in (0, 2):
                        sys.stdout.write("\r[+] Finger detected on platen! Hold still...     \n")
                    else:
                        sys.stdout.write("\r[.] Platen empty. Waiting for finger...          \r")
                    sys.stdout.flush()
                    last_state = finger_state
                    
                if finger_state in (0, 2):
                    good_frames += 1
                    # After 8 stable frames (~0.4s), trigger manual capture if auto hasn't fired
                    if good_frames >= 8 and not is_final:
                        scanner.take_result_image_manually()
                        good_frames = 0
                else:
                    good_frames = 0
                    
                if is_final:
                    if winsound:
                        try:
                            winsound.Beep(1500, 200)
                        except Exception:
                            pass
                            
                    print(f"\n[+] SUCCESS: Fingerprint image captured!")
                    print(f"    - Dimensions: {w} x {h} pixels")
                    print(f"    - Raw Buffer Size: {len(img_bytes)} bytes")
                    
                    # Extract features
                    matcher = FingerprintMatcher()
                    desc = matcher.extract_descriptors(img_bytes, w, h)
                    kp_count = len(desc) if desc is not None else 0
                    quality = "Excellent" if kp_count > 150 else ("Good" if kp_count > 80 else "Fair")
                    print(f"    - Minutiae/Keypoints: {kp_count} ({quality} Quality)")
                    
                    # Save image to file
                    os.makedirs("captures", exist_ok=True)
                    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    out_path = os.path.join("captures", f"test_capture_{ts}.png")
                    arr = np.frombuffer(img_bytes, dtype=np.uint8).reshape((h, w))
                    cv2.imwrite(out_path, arr)
                    print(f"    - Saved Image: {os.path.abspath(out_path)}")
                    
                    captured = True
                    break
                    
            time.sleep(0.03)
            
        if not captured:
            print("\n[-] Timeout: No finger scan completed within 15 seconds.")
            
    except KeyboardInterrupt:
        print("\n[*] Test cancelled by user.")
    finally:
        scanner.close_device()
        print("[*] Scanner closed cleanly.")
        print("=" * 60)
        
    return captured

if __name__ == "__main__":
    run_scanner_test()
