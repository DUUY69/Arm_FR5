@echo off
chcp 65001 >nul
title Command Builder GUI

echo.
echo ============================================================
echo    🖥️ COMMAND BUILDER GUI - IOT CONTROLLER
echo ============================================================
echo.
echo 🚀 Đang khởi chạy Command Builder GUI...
echo.

cd /d "%~dp0\IOTController_Python"
python command_builder_gui.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ Lỗi khởi chạy Command Builder GUI!
    echo 💡 Kiểm tra Python và dependencies
    echo.
    pause
)

echo.
echo 👋 Tạm biệt!
pause
