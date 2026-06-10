@echo off
echo --- PMS Dependency Installer ---
echo Looking for Python 3.12...
py -3.12 --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Python 3.12 found. Installing dependencies...
    py -3.12 -m pip install -r requirements.txt
) else (
    echo Python 3.12 not found. Trying default Python...
    py -m pip install -r requirements.txt
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] pip could not be executed.
    echo Trying to fix pip using get-pip.py...
    powershell -Command "Invoke-WebRequest -Uri https://bootstrap.pypa.io/get-pip.py -OutFile get-pip.py"
    py -3.12 get-pip.py
    py -3.12 -m pip install -r requirements.txt
)

pause
