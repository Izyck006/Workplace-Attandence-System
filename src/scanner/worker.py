from PySide6.QtCore import QThread, Signal
import time
import ctypes
import numpy as np
from src.scanner.kojack import KojackScanner


class IBSU_ImageData(ctypes.Structure):
    _fields_ = [
        ("Buffer", ctypes.c_void_p),
        ("Width", ctypes.c_uint32),
        ("Height", ctypes.c_uint32),
        ("ResolutionX", ctypes.c_double),
        ("ResolutionY", ctypes.c_double),
        ("FrameTime", ctypes.c_double),
        ("Pitch", ctypes.c_int32),
        ("BitsPerPixel", ctypes.c_uint8),
        ("Format", ctypes.c_uint32),
        ("IsFinal", ctypes.c_int32),
        ("ProcessThres", ctypes.c_uint32),
    ]

HOLD_DURATION = 3.0


class ScannerWorker(QThread):
    scan_complete = Signal(object)
    scan_error = Signal(str)
    scan_status = Signal(str)
    preview_frame = Signal(bytes, int, int)

    def __init__(self, scanner_instance, parent=None, image_type=None):
        super().__init__(parent)
        self._is_running = True
        self.scanner = scanner_instance
        self.image_type = image_type

    def run(self):
        self.scan_status.emit("Initializing scanner...")

        if not self.scanner or self.scanner.get_device_count() == 0:
            self.scan_error.emit("No scanner detected.")
            return

        if self.scanner._handle is None:
            if not self.scanner.open_device(0):
                self.scan_error.emit("Failed to open scanner (Is it locked?).")
                return

        self.scan_status.emit("Place finger flat on scanner and hold steady (3s)...")

        try:
            if not self.scanner.begin_capture(self.image_type):
                self.scan_error.emit("Capture could not start. Reconnect the scanner and try again.")
                return

            hold_start_time = None
            best_frame = None
            best_sharpness = -1.0
            last_second_reported = -1
            lost_finger_frames = 0

            while self._is_running:
                success, image_bytes, w, h, is_final, finger_state = self.scanner.block_get_image(ignore_preview=False)

                if success and image_bytes and w > 0 and h > 0:
                    self.preview_frame.emit(image_bytes, w, h)

                    finger_on_platen = (finger_state in (0, 2))

                    if finger_on_platen:
                        lost_finger_frames = 0
                        now = time.time()
                        if hold_start_time is None:
                            hold_start_time = now
                            best_frame = None
                            best_sharpness = -1.0
                            last_second_reported = -1

                        elapsed = now - hold_start_time
                        remaining = max(1, int(HOLD_DURATION - elapsed + 0.99))

                        if remaining != last_second_reported:
                            last_second_reported = remaining
                            self.scan_status.emit(f"Scanning: Hold finger steady ({remaining}s remaining)...")

                        img_np = np.frombuffer(image_bytes, dtype=np.uint8)
                        sharpness = float(np.std(img_np))
                        if sharpness > best_sharpness:
                            best_sharpness = sharpness
                            best_frame = (image_bytes, w, h)

                        if elapsed >= HOLD_DURATION:
                            try:
                                import winsound
                                winsound.Beep(1500, 250)
                            except Exception:
                                pass

                            self.scan_status.emit("Scan complete!")
                            final_bytes, final_w, final_h = best_frame if best_frame else (image_bytes, w, h)
                            self.scan_complete.emit({
                                "status": "success",
                                "image": final_bytes,
                                "width": final_w,
                                "height": final_h
                            })
                            time.sleep(1)
                            break
                    else:
                        if hold_start_time is not None:
                            lost_finger_frames += 1
                            if lost_finger_frames > 4:
                                hold_start_time = None
                                best_frame = None
                                best_sharpness = -1.0
                                last_second_reported = -1
                                lost_finger_frames = 0
                                self.scan_status.emit("Finger lifted too soon. Please hold flat for 3 seconds.")
                        else:
                            self.scan_status.emit("Place finger flat on scanner and hold steady (3s)...")

                    time.sleep(0.03)
                else:
                    time.sleep(0.05)

        except Exception as e:
            try:
                import winsound
                winsound.Beep(250, 500)
            except Exception:
                pass
            self.scan_error.emit(str(e))
        finally:
            self.scanner.cancel_capture()

    def stop(self):
        self._is_running = False
        if self.scanner:
            self.scanner.cancel_capture()
        self.wait()
