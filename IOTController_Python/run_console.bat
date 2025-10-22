@echo off
setlocal
cd /d %~dp0\..
python IOTController_Python\iot_menu.py %*
endlocal
