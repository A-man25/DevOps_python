@echo off
setlocal

REM ==========================================
REM HNI Build Automation
REM ==========================================
REM Runs main.py in a normal console window so
REM COP can draw its live build status cleanly.
REM Double-click this file to start a build.

title HNI Build Automation

REM Run from the folder this .bat file is in
cd /d "%~dp0"

REM Python must be installed and on the PATH
where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found.
    echo Install Python 3.10 or newer and tick "Add python.exe to PATH".
    echo.
    pause
    exit /b 1
)

python main.py
set EXIT_CODE=%errorlevel%

echo.
if "%EXIT_CODE%"=="0" (
    echo Finished.
) else (
    echo Stopped. Exit code %EXIT_CODE%.
)
pause
exit /b %EXIT_CODE%
