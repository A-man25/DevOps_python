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

python main.py
set EXIT_CODE=%errorlevel%

echo.
pause
exit /b %EXIT_CODE%
