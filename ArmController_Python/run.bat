@echo off
chcp 65001 >nul
title Fairino Robot Control - Python

echo ================================================
echo    FAIRINO ROBOT CONTROL - PYTHON VERSION
echo ================================================
echo.

REM Kiểm tra Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python 3.7+ from python.org
    pause
    exit /b 1
)

echo [OK] Python found
python --version

echo.
echo Starting Python Application...
echo.

REM Thử script với SDK trước
if exist "robot_with_sdk.py" (
    echo [INFO] Using SDK version...
    python robot_with_sdk.py
) else if exist "simple_robot.py" (
    echo [INFO] Using simple version...
    python simple_robot.py
) else if exist "robot_control.py" (
    echo [INFO] Using control version...
    python robot_control.py
) else (
    echo [ERROR] No Python script found!
    pause
    exit /b 1
)

echo.
echo Application closed
pause
