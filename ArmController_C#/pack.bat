@echo off
setlocal
set BASE=%~dp0
set DIST=%BASE%dist\
if exist "%DIST%" rd /s /q "%DIST%"
mkdir "%DIST%"

echo Copying My_Arm exe...
copy "%BASE%bin\Debug\net472\My_Arm.exe" "%DIST%" /Y
copy "%BASE%bin\Debug\net472\My_Arm.exe.config" "%DIST%" /Y

echo Copying libfairino (SDK dll)...
copy "%~dp0..\src\FRRobot\bin\Debug\libfairino.dll" "%DIST%" /Y

echo Copying XML-RPC DLL...
copy "%~dp0..\packages\xmlrpcnet.3.0.0.266\lib\net20\CookComputing.XmlRpcV2.dll" "%DIST%" /Y

echo Creating run.bat...
echo @echo off> "%DIST%run.bat"
echo setlocal>> "%DIST%run.bat"
echo "%%~dp0My_Arm.exe" >> "%DIST%run.bat"
echo pause>> "%DIST%run.bat"

echo Creating README.txt...
echo My_Arm distribution > "%DIST%README.txt"
echo - Copy these files to a Windows machine with .NET Framework 4.7.2 installed. >> "%DIST%README.txt"
echo - Run run.bat to start the console app. >> "%DIST%README.txt"

echo Done. Distribution created in %DIST%
endlocal
pause
