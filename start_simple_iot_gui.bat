@echo off
chcp 65001 >nul
title Simple IoT Controller GUI

echo ============================================================
echo    🎯 SIMPLE IOT CONTROLLER GUI
echo ============================================================
echo 🚀 Đang khởi chạy Simple IoT Controller GUI...
echo.

REM Kiểm tra Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python 3.7+ from python.org
    pause
    exit /b 1
)

REM Chuyển đến thư mục IOTController_Python và chạy GUI
cd IOTController_Python
if exist "simple_iot_gui.py" (
    python simple_iot_gui.py
) else (
    echo [ERROR] File simple_iot_gui.py not found in IOTController_Python directory!
    pause
    exit /b 1
)

echo.
echo 👋 Tạm biệt!
pause
