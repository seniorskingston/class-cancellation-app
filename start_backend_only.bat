@echo off
title Class Cancellation Backend Server
echo ========================================
echo    Class Cancellation Backend Server
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

echo Starting the Backend Server...
echo.

REM Install Python dependencies if needed
echo Installing Python dependencies...
pip install -r requirements.txt

echo.
echo Starting backend server on http://localhost:8000
echo.
echo API Endpoints:
echo - GET  http://localhost:8000/api/cancellations
echo - POST http://localhost:8000/api/refresh
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the backend server
python -m uvicorn backend:app --host 0.0.0.0 --port 8000 --reload 