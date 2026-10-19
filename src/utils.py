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


def play_audio_file(file_path: str):
    """Play an mp3/wav audio file asynchronously using native Windows winmm."""
    if sys.platform != "win32" or not os.path.exists(file_path):
        return False
    try:
        import time
        winmm = ctypes.windll.winmm
        alias = f"rf_{os.getpid()}_{int(time.time() * 1000) % 100000}"
        abs_path = os.path.abspath(file_path)
        winmm.mciSendStringW(f'open "{abs_path}" type mpegvideo alias {alias}', None, 0, None)
        winmm.mciSendStringW(f'play {alias} wait', None, 0, None)
        winmm.mciSendStringW(f'close {alias}', None, 0, None)
        return True
    except Exception:
        return False


def speak(text: str):
    """Play speech asynchronously using ElevenLabs (with smart disk cache) or native Windows SAPI."""
    if not text or sys.platform != "win32":
        return
    import threading
    import hashlib
    from pathlib import Path

    def _run():
        # 1. Check if matching pre-recorded audio exists in assets/audio/
        phrase_key = None
        lower = text.lower()
        if "welcome to randaframes" in lower:
            phrase_key = "welcome_system.mp3"
        elif "goodbye" in lower:
            phrase_key = "goodbye.mp3"
        elif "welcome" in lower:
            phrase_key = "welcome_user.mp3"
        elif "already clocked" in lower:
            phrase_key = "already_clocked.mp3"
        elif "not recognized" in lower:
            phrase_key = "scan_error.mp3"

        if phrase_key:
            asset_audio = get_asset_path(os.path.join("assets", "audio", phrase_key))
            if os.path.exists(asset_audio) and play_audio_file(asset_audio):
                return

        # 2. Check ElevenLabs API Key and local cache
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("ELEVENLABS_API_KEY", "")
        voice_id = os.getenv("ELEVENLABS_VOICE_ID", "t2zuPBtbBvwLINfk1lqx")  # Default: Adeola (Nigerian)

        if api_key and voice_id:
            try:
                cache_dir = Path(os.getenv("LOCALAPPDATA", Path.home())) / "RandaframesAttendance" / "audio_cache"
                cache_dir.mkdir(parents=True, exist_ok=True)
                cache_hash = hashlib.md5(f"{voice_id}_{text}".encode("utf-8")).hexdigest()
                cached_file = cache_dir / f"{cache_hash}.mp3"

                if cached_file.exists() and cached_file.stat().st_size > 0:
                    if play_audio_file(str(cached_file)):
                        return

                # Fetch from ElevenLabs API
                import urllib.request
                import json
                url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                headers = {
                    "xi-api-key": api_key,
                    "Content-Type": "application/json"
                }
                payload = json.dumps({
                    "text": text,
                    "model_id": "eleven_turbo_v2_5"
                }).encode("utf-8")
                req = urllib.request.Request(url, data=payload, headers=headers)
                audio_bytes = urllib.request.urlopen(req, timeout=8).read()
                if audio_bytes:
                    cached_file.write_bytes(audio_bytes)
                    if play_audio_file(str(cached_file)):
                        return
            except Exception:
                pass  # Fall back to native voice if plan limitation, offline, etc.

        # 3. Fallback: Fast native Windows SAPI voice (<100ms startup)
        f = None
        try:
            import tempfile
            import subprocess
            safe_text = text.replace('"', '""')
            f = tempfile.NamedTemporaryFile(suffix='.vbs', delete=False, mode='w', encoding='utf-8')
            f.write(f'CreateObject("SAPI.SpVoice").Speak "{safe_text}"\n')
            f.close()
            flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
            subprocess.run(["wscript", f.name], creationflags=flags, timeout=10)
        except Exception:
            pass
        finally:
            if f and os.path.exists(f.name):
                try:
                    os.unlink(f.name)
                except Exception:
                    pass

    threading.Thread(target=_run, daemon=True).start()


