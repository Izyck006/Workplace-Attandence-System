import ctypes
import os
import platform
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


IBSU_MAX_STR_LEN = 256
IBSU_STATUS_OK = 0
IBSU_ERR_DEVICE_NOT_FOUND = -1
IBSU_IMAGE_TYPE_ROLL_SINGLE_FINGER = 1
IBSU_IMAGE_TYPE_FLAT_SINGLE_FINGER = 2
IBSU_IMAGE_RESOLUTION_500 = 500

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
    """
    def __init__(self):
        self._dll = None
        self._handle = None
        self._is_initialized = False
        
        self._load_library()
        
    def _load_library(self):
        try:
            if platform.system() == "Windows":
                
                default_path = r"C:\Program Files\Integrated Biometrics\IBScanUltimateSDK_x64\Bin\IBScanUltimate.dll"
                if not os.path.exists(default_path):
                    logger.warning(f"IBScanUltimate.dll not found at {default_path}")
                    return
                self._dll = ctypes.windll.LoadLibrary(default_path)
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

    def begin_capture(self, image_type: int = 4) -> bool:
        if not self._dll or self._handle is None:
            return False
        
        
        status = self._dll.IBSU_BeginCaptureImage(self._handle, image_type, 500, 3)
        if status != IBSU_STATUS_OK and status not in (-303, -205): 
            print(f"Failed to begin capture: {status}")
            logger.error(f"Failed to begin capture: {status}")
            return False
        return status == IBSU_STATUS_OK or status == -303

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

    def close_device(self):
        if self._dll and self._handle is not None:
            self._dll.IBSU_CloseDevice(self._handle)
            self._handle = None
