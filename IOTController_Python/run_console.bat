@echo off
setlocal
cd /d %~dp0
echo Starting IOTController Launcher...
python launcher.py %*
pause
endlocal
