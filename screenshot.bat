@echo off
chcp 65001 >nul
cd /d %~dp0
echo ====================================
echo Take Screenshot
echo ====================================
echo.

set SCREENSHOT_DIR=%~dp0screenshots
set DATE_STR=%date:~0,4%-%date:~5,2%-%date:~8,2%
set TIME_STR=%time:~0,2%%time:~3,2%%time:~6,2%
set TIME_STR=%TIME_STR: =0%
set FILENAME=screenshot_%DATE_STR%_%TIME_STR%.png

if not exist "%SCREENSHOT_DIR%" mkdir "%SCREENSHOT_DIR%"

echo Saving screenshot to: %SCREENSHOT_DIR%\%FILENAME%
call "E:\AndroidAuto_new\venv\Scripts\python.exe" main.py --screenshot "%SCREENSHOT_DIR%\%FILENAME%"

pause
