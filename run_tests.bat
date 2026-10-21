@echo off
setlocal

REM ==========================================
REM HNI Build Automation - Test suite
REM ==========================================
REM Runs every test in the tests folder.
REM Safe to run any time: tests use temporary
REM sandbox repos and fake COP commands. They
REM never touch C:\CetDev or the Bitbucket server.

title HNI Build Automation - Tests

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

python -m unittest discover -s tests -t . -v
set EXIT_CODE=%errorlevel%

echo.
if "%EXIT_CODE%"=="0" (
    echo ALL TESTS PASSED
) else (
    echo SOME TESTS FAILED - see the list above
)
pause
exit /b %EXIT_CODE%
