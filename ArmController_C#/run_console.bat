@echo off
cd /d %~dp0
set EXE=bin\Debug\net472\My_Arm.exe
if not exist %EXE% set EXE=bin\Release\net472\My_Arm.exe
if not exist %EXE% echo Cannot find My_Arm.exe! & pause & exit /b
"%EXE%"
pause