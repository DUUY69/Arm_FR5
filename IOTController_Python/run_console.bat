@echo off
setlocal
cd /d %~dp0\..
python IOTController_Python\cli.py %*
endlocal
