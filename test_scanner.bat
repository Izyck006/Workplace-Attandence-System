@echo off
title Columbo Scanner Diagnostic Tool
echo Starting Fingerprint Scanner Test GUI...
python test_scanner_gui.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo GUI closed or encountered an error. Running CLI test instead...
    python test_scanner.py
    pause
)
