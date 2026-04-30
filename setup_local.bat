@echo off
REM Quick Start Script for Local Testing - Windows

echo.
echo ======================================
echo Insighta Labs+ - Local Testing Setup
echo ======================================
echo.

REM Step 1: Check if we're in the right directory
if not exist "stage-3-backend" (
    echo Error: Run this script from the backend2 root directory
    echo Current directory: %cd%
    exit /b 1
)

echo [Step 1] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Please install Python 3.8+
    exit /b 1
)
echo OK: Python installed

echo.
echo [Step 2] Creating .env file...
cd stage-3-backend

if exist ".env" (
    echo .env already exists (skipping)
) else (
    echo Creating .env from .env.example...
    copy .env.example .env >nul
    echo OK: .env created
)

REM Check if BACKEND_URL is set
findstr /M "BACKEND_URL" .env >nul
if errorlevel 1 (
    echo Adding BACKEND_URL to .env...
    echo. >> .env
    echo BACKEND_URL=http://127.0.0.1:8000 >> .env
    echo WEB_PORTAL_URL=http://localhost:5500 >> .env
)

echo.
echo [Step 3] Setting up Python virtual environment...
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo [Step 4] Installing dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install dependencies
    exit /b 1
)
echo OK: Dependencies installed

echo.
echo [Step 5] Running migrations...
python manage.py migrate >nul 2>&1
if errorlevel 1 (
    echo Warning: Migrations may have failed (check migrations folder)
) else (
    echo OK: Migrations applied
)

echo.
echo ======================================
echo Setup Complete!
echo ======================================
echo.
echo Next: Start the backend server
echo    python manage.py runserver 0.0.0.0:8000
echo.
echo Then open frontend in another terminal:
echo    cd ..\web-portal
echo    python -m http.server 5500
echo.
echo Then open: http://localhost:5500
echo.
pause
