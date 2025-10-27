@echo off
chcp 65001 > nul
echo ============================================================
echo   THIET LAP MOI TRUONG - SETUP ENVIRONMENT
echo ============================================================
echo.

:: Change to script directory
cd /d "%~dp0"

:: Check Python installation
echo [1/6] Kiem tra Python...
python --version
if errorlevel 1 (
    echo LOI: Python khong tim thay!
    echo Vui long cai dat Python 3.7+ tu python.org
    pause
    exit /b 1
)
echo OK: Python da duoc cai dat
echo.

:: Update pip
echo [2/6] Cap nhat pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo Canh bao: Khong the cap nhat pip
)
echo.

:: Install requirements
echo [3/6] Cai dat dependencies...
if exist requirements.txt (
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Canh bao: Co mot so packages khong the cai dat
    )
) else (
    echo Canh bao: Khong tim thay requirements.txt
)

:: Install Cython if not installed
python -c "import Cython" 2>nul
if errorlevel 1 (
    echo Cai dat Cython...
    python -m pip install Cython
    if errorlevel 1 (
        echo LOI: Khong the cai dat Cython!
        pause
        exit /b 1
    )
) else (
    echo OK: Cython da duoc cai dat
)
echo.

:: Check if SDK needs to be built
echo [4/6] Kiem tra SDK build...
set SDK_DIR=fairino_sdk\fairino
set PYD_FILE=%SDK_DIR%\Robot.cp311-win_amd64.pyd

if exist "%PYD_FILE%" (
    echo OK: SDK da duoc build (.pyd file ton tai)
) else (
    echo Dang build SDK...
    cd "%SDK_DIR%"
    
    if exist setup.py (
        echo Chay: python setup.py build_ext --inplace
        python setup.py build_ext --inplace
        
        if errorlevel 1 (
            echo LOI: Build SDK that bai!
            echo.
            echo Nguyen nhan co the:
            echo   1. Thieu Microsoft C++ Build Tools
            echo   2. Chua cai dat Visual Studio
            echo   3. Chua cai dat Windows SDK
            echo.
            echo Khuyen nghi:
            echo   - Cai dat Microsoft C++ Build Tools
            echo   - Hoac cai dat Visual Studio 2019/2022
            echo   - Hoac dung Python khac da co .pyd san
            cd ..\..
            pause
            exit /b 1
        ) else (
            echo OK: SDK da duoc build thanh cong!
        )
        cd ..\..
    ) else (
        echo Canh bao: Khong tim thay setup.py
        cd ..\..
    )
)
echo.

:: Test SDK import
echo [5/6] Test import SDK...
python -c "import sys; sys.path.insert(0, 'fairino_sdk'); from fairino import Robot; print('OK: SDK import thanh cong!')"
if errorlevel 1 (
    echo LOI: Khong the import SDK!
    echo SDK co the chua duoc build dung
    echo.
) else (
    echo OK: SDK import thanh cong!
)
echo.

:: Display summary
echo [6/6] Tom tat...
echo ============================================================
echo   THIET LAP HOAN TAT!
echo ============================================================
echo.
echo Ban co the:
echo   1. Chay GUI: python arm_controller_gui.py
echo   2. Hoac: start_arm_controller.bat
echo   3. Hoac chay test: python test_sdk_build.py
echo.
echo Neu co loi, vui long xem file: SDK_BUILD_FIX.md
echo.

pause

