@echo off
cd /d "%~dp0"
if not exist "backup" mkdir "backup"
if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" src\services\backup.py >> "backup\backup.log" 2>&1
) else if exist "C:\Python314\python.exe" (
    "C:\Python314\python.exe" src\services\backup.py >> "backup\backup.log" 2>&1
) else (
    python src\services\backup.py >> "backup\backup.log" 2>&1
)
