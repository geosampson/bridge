@echo off
title BRIDGE - WooCommerce & Capital ERP Product Manager
color 0A

echo =========================================
echo   BRIDGE - Product Management System
echo   WooCommerce ^& Capital ERP Integration
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
echo.

REM Check and install required packages
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

pip show urllib3 >nul 2>&1
if errorlevel 1 (
    echo Installing urllib3...
    pip install urllib3
)

pip show pyodbc >nul 2>&1
if errorlevel 1 (
    echo Installing pyodbc...
    pip install pyodbc
)

echo.
echo All dependencies installed!
echo.
echo Starting BRIDGE application...
echo.

REM Run the application
python bridge_app.py

if errorlevel 1 (
    echo.
    echo ==========================================
    echo Application exited with an error.
    echo Please check INSTALLATION.md for help.
    echo ==========================================
    pause
)
