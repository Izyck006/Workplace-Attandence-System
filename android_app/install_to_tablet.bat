@echo off
set "ADB=C:\Users\T470\AppData\Local\Android\Sdk\platform-tools\adb.exe"
set "APK=app\build\outputs\apk\debug\app-debug.apk"

%ADB% devices
%ADB% install -r %APK%
%ADB% shell am start -n com.randaframes.attendance/.MainActivity
pause
