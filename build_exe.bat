@echo off
echo Building Randaframes Attendance Executable...
python -m PyInstaller --name "RandaframesAttendance" --windowed --noconfirm main.py
echo Build complete. The executable is located in the 'dist\RandaframesAttendance' folder.
echo Make sure to copy the '.env' file into the 'dist\RandaframesAttendance' folder so it can connect to the database!
pause
