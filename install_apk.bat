@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ====================================
echo Install APK
echo ====================================
echo.
echo Select installation mode:
echo   1. Install latest version
echo   2. Install specific version
set /p choice="Enter option (1/2): "

if "%choice%"=="2" (
    set /p version="Enter version (format: x.x.x-xxx, e.g. 1.0.0-1): "
    echo.
    echo Installing version %version% ...
    "E:\AndroidAuto_new\venv\Scripts\python.exe" main.py --install --version %version%
) else (
    echo.
    echo Installing latest version ...
    "E:\AndroidAuto_new\venv\Scripts\python.exe" main.py --install
)

pause
