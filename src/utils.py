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


def speak(text: str):
    """Play speech asynchronously using native Windows SAPI voice (sub-100ms startup)."""
    if not text or sys.platform != "win32":
        return
    import threading
    import subprocess
    import tempfile
    def _run():
        f = None
        try:
            safe_text = text.replace('"', '""')
            f = tempfile.NamedTemporaryFile(suffix='.vbs', delete=False, mode='w', encoding='utf-8')
            f.write(f'CreateObject("SAPI.SpVoice").Speak "{safe_text}"\n')
            f.close()
            flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
            subprocess.run(["wscript", f.name], creationflags=flags, timeout=10)
        except Exception:
            try:
                safe_ps = text.replace("'", "''").replace('"', '')
                ps_cmd = f"Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{safe_ps}')"
                flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
                subprocess.run(
                    ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                    creationflags=flags,
                    timeout=12
                )
            except Exception:
                pass
        finally:
            if f and os.path.exists(f.name):
                try:
                    os.unlink(f.name)
                except Exception:
                    pass
    threading.Thread(target=_run, daemon=True).start()

