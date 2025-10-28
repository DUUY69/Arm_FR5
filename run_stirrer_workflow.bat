@echo off
chcp 65001 >nul
title Stirrer Workflow - Máy Khuấy Tự Động

echo ======================================================================
echo   STIRRER WORKFLOW - Máy Khuấy Tự Động
echo ======================================================================
echo.

REM Kiểm tra Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python không được tìm thấy!
    echo Vui lòng cài đặt Python trước.
    pause
    exit /b 1
)

echo [INFO] Đang chạy workflow...
echo.

REM Chạy Python script
python run_stirrer_workflow.py

echo.
echo [INFO] Hoàn tất!
pause

