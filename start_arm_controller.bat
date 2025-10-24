@echo off
chcp 65001 >nul
title Arm Controller GUI

echo.
echo ============================================================
echo    🦾 ARM CONTROLLER GUI - FAIRINO ROBOT CONTROL
echo ============================================================
echo.
echo 🚀 Đang khởi chạy Arm Controller GUI...
echo.

cd /d "%~dp0\ArmController_Python"
python arm_controller_gui.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ Lỗi khởi chạy GUI!
    echo 💡 Kiểm tra Python và dependencies
    echo.
    pause
)

echo.
echo 👋 Tạm biệt!
pause