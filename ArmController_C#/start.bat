echo Building My_Arm...
@echo off
REM Build My_Arm project and run the console app (uses dotnet CLI)
setlocal
echo Building My_Arm...
dotnet build "%~dp0My_Arm.csproj" -c Debug
if %ERRORLEVEL% neq 0 (
    echo Build failed with errorlevel %ERRORLEVEL%.
    pause
    exit /b %ERRORLEVEL%
)

echo Running My_Arm...
"%~dp0bin\Debug\net472\My_Arm.exe"
endlocal
pause
