import os
import sys
import ctypes

def get_asset_path(filename):
    if getattr(sys, "frozen", False):
        base_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        path = os.path.join(base_dir, filename)
        if os.path.exists(path):
            return path
        exe_dir = os.path.dirname(sys.executable)
        path = os.path.join(exe_dir, filename)
        if os.path.exists(path):
            return path
    
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    path = os.path.join(project_root, filename)
    if os.path.exists(path):
        return path
        
    return filename

def apply_window_icon(window):
    from PySide6.QtGui import QIcon
    icon_path = get_asset_path("icon.ico")
    if os.path.exists(icon_path):
        icon = QIcon(icon_path)
        window.setWindowIcon(icon)
        if sys.platform == "win32":
            try:
                hwnd = int(window.winId())
                hicon = ctypes.windll.user32.LoadImageW(None, os.path.abspath(icon_path), 1, 0, 0, 0x00000010 | 0x00000040)
                if hicon:
                    ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 1, hicon)
                    ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 0, hicon)
            except Exception:
                pass
