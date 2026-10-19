@echo off
cd /d "%~dp0"
python -m uvicorn src.server.app:app --host 127.0.0.1 --port 8000 --no-access-log
