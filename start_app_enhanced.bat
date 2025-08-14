@echo off
title Class Cancellation App Launcher (Enhanced)
echo ========================================
echo    Class Cancellation App Launcher
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

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org
    pause
    exit /b 1
)

echo Starting the Class Cancellation App...
echo.

REM Check if Excel file exists
if not exist "Class Cancellation App.xlsx" (
    echo WARNING: Excel file 'Class Cancellation App.xlsx' not found!
    echo Make sure the file is in the project folder.
    echo.
)

REM Install Python dependencies if needed
echo Installing Python dependencies...
pip install -r requirements.txt

REM Start the backend server in a new window
echo Starting backend server...
start "Backend Server" cmd /k "cd /d "%~dp0" && python -m uvicorn backend:app --host 0.0.0.0 --port 8000 --reload"

REM Wait for backend to start
echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

REM Check if backend is running
echo Checking if backend is running...
curl -s http://localhost:8000/docs >nul 2>&1
if errorlevel 1 (
    echo WARNING: Backend might not be fully started yet.
    echo This is normal, it will be ready in a few more seconds.
) else (
    echo Backend is running successfully!
)

REM Navigate to frontend directory
cd frontend

REM Install frontend dependencies if needed
if not exist node_modules (
    echo Installing Node.js dependencies...
    npm install
    if errorlevel 1 (
        echo ERROR: Failed to install Node.js dependencies
        pause
        exit /b 1
    )
) else (
    echo Node.js dependencies already installed.
)

REM Start the frontend development server
echo Starting frontend server...
start "Frontend Server" cmd /k "cd /d "%~dp0frontend" && npm start"

REM Wait for frontend to start
echo Waiting for frontend to start...
timeout /t 10 /nobreak >nul

REM Try to open browser multiple times
echo Opening browser...
start http://localhost:3000

REM Wait a bit more and try again (in case first attempt failed)
timeout /t 3 /nobreak >nul
start http://localhost:3000

echo.
echo ========================================
echo    App is starting up!
echo ========================================
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo If the browser didn't open automatically, please visit:
echo http://localhost:3000
echo.
echo Keep the command windows open while using the app.
echo.
echo Press any key to close this launcher...
pause >nul 