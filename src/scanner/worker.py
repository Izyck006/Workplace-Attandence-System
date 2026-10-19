from PySide6.QtCore import QThread, Signal
import time
import ctypes
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
            
        self.scan_status.emit("Please place your finger on the scanner...")
        
        
        try:
            self.scan_status.emit("Scanner Active: Waiting for finger...")
            
            if not self.scanner.begin_capture(self.image_type):
                self.scan_error.emit("Capture could not start. Reconnect the scanner and try again.")
                return
            
            good_frame_count = 0
            
            while self._is_running:
                
                success, image_bytes, w, h, is_final, finger_state = self.scanner.block_get_image(ignore_preview=False)
                
                if success and image_bytes:
                    if is_final:
                        try:
                            import winsound
                            winsound.Beep(1500, 200) 
                        except Exception:
                            pass
                            
                        self.scan_status.emit("Image captured!")
                        self.scan_complete.emit({
                            "status": "success", 
                            "image": image_bytes,
                            "width": w,
                            "height": h
                        })
                        
                        
                        time.sleep(1)
                        break
                    else:
                        
                        self.preview_frame.emit(image_bytes, w, h)
                        
                        
                        
                        if finger_state in (0, 2): 
                            good_frame_count += 1
                            if good_frame_count >= 10: 
                                self.scanner.take_result_image_manually()
                                good_frame_count = 0
                        else:
                            good_frame_count = 0
                            
                        time.sleep(0.01)
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
