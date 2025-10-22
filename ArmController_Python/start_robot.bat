@echo off
chcp 65001 >nul
title Fairino Robot Control - Python

echo ================================================
echo    FAIRINO ROBOT CONTROL - PYTHON
echo ================================================
echo.

REM Kiểm tra Python có cài đặt không
python --version >nul 2>&1
if errorlevel 1 (
    echo [LOI] Python chua duoc cai dat hoac khong co trong PATH
    echo Vui long cai dat Python 3.7+ va thu lai
    pause
    exit /b 1
)

echo [OK] Python da duoc cai dat
python --version

REM Kiểm tra file robot_control.py
if not exist "robot_control.py" (
    echo [LOI] File robot_control.py khong ton tai
    echo Vui long chay script nay trong thu muc MyArm_Python
    pause
    exit /b 1
)

echo [OK] File robot_control.py ton tai

REM Kiểm tra thư mục lua_scripts
if not exist "lua_scripts" (
    echo [INFO] Tao thu muc lua_scripts...
    mkdir lua_scripts
)

echo [OK] Thu muc lua_scripts san sang

echo.
echo Dang khoi dong chuong trinh...
echo.

REM Chạy chương trình Python
python robot_control.py

echo.
echo Chuong trinh da ket thuc
pause
