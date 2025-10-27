@echo off
chcp 65001 >nul
title Thả 5 Viên Đá - Ice Maker

echo.
echo ============================================================
echo    ❄️ ICE MAKER - THẢ 5 VIÊN ĐÁ
echo ============================================================
echo.
echo 🚀 Đang chạy script thả 5 viên đá...
echo.

cd /d "%~dp0"
python test_ice_maker_5_cubes.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ Lỗi!
    echo 💡 Kiểm tra Python và dependencies
    echo.
    pause
)

echo.
echo 👋 Hoàn thành!
pause
