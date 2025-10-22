@echo off
REM Chạy MyArm_Python bằng Python
cd /d %~dp0
REM Add local SDK windows folder to PYTHONPATH so imports work when double-clicked
set SCRIPT_DIR=%~dp0
set SDK_PATH=%SCRIPT_DIR%..\fairino-python-sdk-main\fairino-python-sdk-main\windows
if exist "%SDK_PATH%" (
	echo Adding SDK path to PYTHONPATH: %SDK_PATH%
	set PYTHONPATH=%SDK_PATH%;%PYTHONPATH%
)
python myarm.py
pause
