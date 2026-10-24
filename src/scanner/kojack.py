import ctypes
import os
import platform
import logging
import sys
from pathlib import Path
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


IBSU_MAX_STR_LEN = 256
IBSU_STATUS_OK = 0
IBSU_ERR_DEVICE_NOT_FOUND = -1
IBSU_ERR_CAPTURE_STILL_RUNNING = -303
IBSU_ERR_CAPTURE_INVALID_MODE = -305

IBSU_IMAGE_TYPE_NONE = 0
IBSU_IMAGE_TYPE_ROLL_SINGLE_FINGER = 1
IBSU_IMAGE_TYPE_FLAT_SINGLE_FINGER = 2
IBSU_IMAGE_TYPE_FLAT_TWO_FINGERS = 3
IBSU_IMAGE_TYPE_FLAT_FOUR_FINGERS = 4
IBSU_IMAGE_RESOLUTION_500 = 500

IBSU_OPTION_AUTO_CONTRAST = 1
IBSU_OPTION_AUTO_CAPTURE = 2

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

class KojackScanner:
    """
    Python wrapper for the Integrated Biometrics IBScanUltimate SDK.
    Uses ctypes to interface with IBScanUltimate.dll.
    Supports Columbo, Kojack, Watson, Sherlock and other IB scanners.
    """
    def __init__(self):
        self._dll = None
        self._handle = None
        self._is_initialized = False
        
        self._load_library()
        
    def _load_library(self):
        try:
            if platform.system() == "Windows":
                
                roots = [Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[2])) / 'scanner_runtime']
                if os.getenv('IBSCAN_SDK_DIR'):
                    roots.insert(0, Path(os.environ['IBSCAN_SDK_DIR']))
                roots.append(Path(os.environ.get('ProgramFiles', r'C:\Program Files')) /
                             'Integrated Biometrics' / 'IBScanUltimateSDK_x64' / 'Bin')
                root = next((root for root in roots if (root / 'IBScanUltimate.dll').is_file()), None)
                if root is None:
                    logger.warning("Scanner SDK missing. Install the x64 Integrated Biometrics SDK or provide scanner_runtime.")
                    return
                if hasattr(os, 'add_dll_directory'):
                    self._dll_directory = os.add_dll_directory(str(root))
                self._dll = ctypes.WinDLL(str(root / 'IBScanUltimate.dll'))
            else:
                logger.warning("OS not supported for this wrapper version.")
                return
                
            self._setup_function_signatures()
            self._is_initialized = True
        except Exception as e:
            logger.error(f"Failed to load IBScanUltimate DLL: {e}")

    def _setup_function_signatures(self):
        self._dll.IBSU_GetDeviceCount.argtypes = [ctypes.POINTER(ctypes.c_int)]
        self._dll.IBSU_GetDeviceCount.restype = ctypes.c_int
        
        self._dll.IBSU_OpenDevice.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
        self._dll.IBSU_OpenDevice.restype = ctypes.c_int
        
        self._dll.IBSU_CloseDevice.argtypes = [ctypes.c_int]
        self._dll.IBSU_CloseDevice.restype = ctypes.c_int
        
        self._dll.IBSU_BeginCaptureImage.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint32]
        self._dll.IBSU_BeginCaptureImage.restype = ctypes.c_int

        if hasattr(self._dll, "IBSU_IsCaptureAvailable"):
            self._dll.IBSU_IsCaptureAvailable.argtypes = [
                ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int)
            ]
            self._dll.IBSU_IsCaptureAvailable.restype = ctypes.c_int
        
        if hasattr(self._dll, "IBSU_TakeResultImageManually"):
            self._dll.IBSU_TakeResultImageManually.argtypes = [ctypes.c_int]
            self._dll.IBSU_TakeResultImageManually.restype = ctypes.c_int

        if hasattr(self._dll, "IBSU_CancelCaptureImage"):
            self._dll.IBSU_CancelCaptureImage.argtypes = [ctypes.c_int]
            self._dll.IBSU_CancelCaptureImage.restype = ctypes.c_int
        
        self._dll.IBSU_BGetImage.argtypes = [
            ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, 
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p
        ]
        self._dll.IBSU_BGetImage.restype = ctypes.c_int

    def get_device_count(self) -> int:
        if not self._dll:
            return 0
        count = ctypes.c_int(0)
        status = self._dll.IBSU_GetDeviceCount(ctypes.byref(count))
        if status != IBSU_STATUS_OK:
            logger.error(f"Failed to get device count: status {status}")
            return 0
        return count.value

    def open_device(self, index: int = 0) -> bool:
        if not self._dll:
            return False
        if self._handle is not None:
            return True
            
        handle = ctypes.c_int(-1)
        status = self._dll.IBSU_OpenDevice(index, ctypes.byref(handle))
        if status == IBSU_STATUS_OK:
            self._handle = handle.value
            return True
            
        logger.error(f"Failed to open device {index}: status {status}")
        return False

    def is_capture_available(self, image_type: int, resolution: int = 500) -> bool:
        """Check if the connected device supports the given image type and resolution."""
        if not self._dll or self._handle is None:
            return False
        if not hasattr(self._dll, "IBSU_IsCaptureAvailable"):
            return True
        avail = ctypes.c_int(0)
        status = self._dll.IBSU_IsCaptureAvailable(
            self._handle, image_type, resolution, ctypes.byref(avail)
        )
        return status == IBSU_STATUS_OK and bool(avail.value)

    def get_supported_image_type(self, preferred: Optional[int] = None) -> int:
        """
        Returns a valid image type supported by the currently connected scanner.
        If preferred is available, returns it. Otherwise falls back in order:
        FLAT_SINGLE_FINGER (2) -> FLAT_TWO_FINGERS (3) -> FLAT_FOUR_FINGERS (4) -> ROLL_SINGLE_FINGER (1).
        """
        if preferred is not None and self.is_capture_available(preferred):
            return preferred
            
        for candidate in [
            IBSU_IMAGE_TYPE_FLAT_SINGLE_FINGER,
            IBSU_IMAGE_TYPE_FLAT_TWO_FINGERS,
            IBSU_IMAGE_TYPE_FLAT_FOUR_FINGERS,
            IBSU_IMAGE_TYPE_ROLL_SINGLE_FINGER,
        ]:
            if self.is_capture_available(candidate):
                return candidate
        return preferred if preferred is not None else IBSU_IMAGE_TYPE_FLAT_SINGLE_FINGER

    def begin_capture(self, image_type: Optional[int] = None) -> bool:
        if not self._dll or self._handle is None:
            return False
        
        target_type = self.get_supported_image_type(image_type)
        
        status = self._dll.IBSU_BeginCaptureImage(self._handle, target_type, 500, IBSU_OPTION_AUTO_CONTRAST)
        if status != IBSU_STATUS_OK and status not in (IBSU_ERR_CAPTURE_STILL_RUNNING, -205): 
            print(f"Failed to begin capture: {status} (type: {target_type})")
            logger.error(f"Failed to begin capture: {status} (type: {target_type})")
            return False
        return status == IBSU_STATUS_OK or status == IBSU_ERR_CAPTURE_STILL_RUNNING

    def block_get_image(self, ignore_preview=True):
        if not self._dll or self._handle is None:
            return False, None, 0, 0, False, -1
            
        img = IBSU_ImageData()
        img_type = ctypes.c_int(0)
        split_image_array = (IBSU_ImageData * 4)()
        split_count = ctypes.c_int(4)
        finger_state = ctypes.c_int(0)
        quality_array = (ctypes.c_int * 4)()
        quality_count = ctypes.c_int(4)
        
        status = self._dll.IBSU_BGetImage(
            self._handle, 
            ctypes.byref(img), 
            ctypes.byref(img_type), 
            ctypes.byref(split_image_array), 
            ctypes.byref(split_count), 
            ctypes.byref(finger_state), 
            ctypes.byref(quality_array), 
            ctypes.byref(quality_count)
        )
        
        if status != IBSU_STATUS_OK:
            if status not in (-8, 300, -205):
                print(f"BGetImage returned status: {status}")
            return False, None, 0, 0, False, -1
            
        if ignore_preview and img.IsFinal == 0:
            return False, None, 0, 0, False, -1
            
        if ignore_preview and finger_state.value != 0:
            print(f"Capture rejected: finger_state was {finger_state.value}")
            return False, None, 0, 0, False, -1
            
        image_bytes = None
        size = img.Width * img.Height
        if size > 0 and img.Buffer:
            image_bytes = ctypes.string_at(img.Buffer, size)
            
        return True, image_bytes, img.Width, img.Height, (img.IsFinal != 0), finger_state.value

    def take_result_image_manually(self) -> bool:
        if not self._dll or self._handle is None:
            return False
        status = self._dll.IBSU_TakeResultImageManually(self._handle)
        if status != IBSU_STATUS_OK:
            print(f"TakeResultImageManually failed: {status}")
            return False
        return True

    def cancel_capture(self) -> bool:
        if not self._dll or self._handle is None:
            return False
        if hasattr(self._dll, "IBSU_CancelCaptureImage"):
            status = self._dll.IBSU_CancelCaptureImage(self._handle)
            return status == IBSU_STATUS_OK
        return False

    def close_device(self):
        if self._dll and self._handle is not None:
            self.cancel_capture()
            self._dll.IBSU_CloseDevice(self._handle)
            self._handle = None
