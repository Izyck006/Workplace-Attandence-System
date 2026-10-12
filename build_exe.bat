@echo off
echo Building Randaframes Attendance Executable...
python -m PyInstaller --name "RandaframesAttendance" --windowed --clean --icon="icon.ico" --add-data "randaframes logo.jpg;." --add-data "icon.ico;." --noconfirm main.py
if exist ".env" (
    copy /y ".env" "dist\RandaframesAttendance\"
)
echo Build complete. The executable is located in the 'dist\RandaframesAttendance' folder.
pause
