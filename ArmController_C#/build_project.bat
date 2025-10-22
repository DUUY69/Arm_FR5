@echo off
chcp 65001 >nul
title Fairino Robot Control - Build C# Project

echo ================================================
echo    FAIRINO ROBOT CONTROL - BUILD PROJECT
echo ================================================
echo.

REM Kiểm tra MSBuild
where msbuild >nul 2>&1
if errorlevel 1 (
    echo [ERROR] MSBuild not found in PATH
    echo.
    echo Please install Visual Studio 2019+ or Build Tools
    echo Or add MSBuild to PATH manually
    echo.
    echo Typical MSBuild locations:
    echo - C:\Program Files (x86)\Microsoft Visual Studio\2019\Professional\MSBuild\Current\Bin\MSBuild.exe
    echo - C:\Program Files\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\MSBuild.exe
    pause
    exit /b 1
)

echo [OK] MSBuild found
msbuild -version

echo.
echo Building project...

REM Build solution
if exist "fairino.sln" (
    echo Building fairino.sln...
    msbuild fairino.sln /p:Configuration=Release /p:Platform="Any CPU"
) else if exist "My_Arm.csproj" (
    echo Building My_Arm.csproj...
    msbuild My_Arm.csproj /p:Configuration=Release
) else (
    echo [ERROR] No project file found!
    echo Looking for: fairino.sln or My_Arm.csproj
    pause
    exit /b 1
)

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    echo Please check the error messages above
    pause
    exit /b 1
) else (
    echo.
    echo [SUCCESS] Build completed successfully!
    echo.
    echo Executable should be available at:
    echo - dist\My_Arm.exe (if copied)
    echo - bin\Release\net472\My_Arm.exe
    echo - bin\Debug\net472\My_Arm.exe
    echo.
    echo You can now run start_app.bat to launch the application
)

pause
