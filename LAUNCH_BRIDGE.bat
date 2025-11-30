@echo off
title BRIDGE - WooCommerce & Capital ERP Product Manager
color 0A

echo =========================================
echo   BRIDGE - Product Management System
echo   WooCommerce & Capital ERP Integration
echo =========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Checking dependencies...

REM Install required packages if needed
pip show customtkinter >nul 2>&1
if errorlevel 1 (
    echo Installing customtkinter...
    pip install customtkinter
)

pip show requests >nul 2>&1
if errorlevel 1 (
    echo Installing requests...
    pip install requests
)

echo.
echo Starting BRIDGE application...
echo.

REM Run the application
python bridge_app.py

if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)
