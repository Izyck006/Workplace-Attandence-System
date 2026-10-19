@echo off
echo Building Randaframes Attendance Executable...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\build_windows.ps1"
if errorlevel 1 exit /b 1
echo Installer is in release\RandaframesAttendance-Setup-2.0.0.exe
pause
