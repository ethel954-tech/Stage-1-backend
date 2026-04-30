@echo off
REM Start Django Backend Server - Windows

cd stage-3-backend

if not exist "venv" (
    echo Error: Virtual environment not found
    echo Run setup_local.bat first
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo ======================================
echo Starting Django Backend Server
echo ======================================
echo.
echo Backend will be available at:
echo   http://127.0.0.1:8000
echo   http://localhost:8000
echo.
echo Endpoints to test:
echo   http://localhost:8000/auth/github?client_type=web
echo   http://localhost:8000/auth/github/callback?code=test_code^&state=test
echo.
echo Press Ctrl+C to stop the server
echo.

python manage.py runserver 0.0.0.0:8000
