@echo off
chcp 65001 >nul
title Workflow Manager GUI

echo ======================================================================
echo   WORKFLOW MANAGER - Giao Diện Quản Lý Workflow
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

echo [INFO] Đang khởi động GUI...
echo.

REM Chạy GUI
python workflow_gui.py

if errorlevel 1 (
    echo.
    echo [ERROR] Có lỗi xảy ra!
    pause
)

