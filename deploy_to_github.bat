@echo off
title Deploy to GitHub
echo ========================================
echo    Deploy to GitHub Helper
echo ========================================
echo.

echo This script will help you upload your app to GitHub for deployment.
echo.

REM Check if Git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git is not installed!
    echo Please install Git from https://git-scm.com
    pause
    exit /b 1
)

echo Step 1: Checking current Git status...
git status >nul 2>&1
if errorlevel 1 (
    echo Initializing Git repository...
    git init
) else (
    echo Git repository already exists.
)

echo.
echo Step 2: Adding all files to Git...
git add .

echo.
echo Step 3: Committing changes...
git commit -m "Update app for deployment"

echo.
echo Step 4: Setting up main branch...
git branch -M main

echo.
echo ========================================
echo    GitHub Repository Setup
echo ========================================
echo.
echo Now you need to:
echo.
echo 1. Go to https://github.com
echo 2. Create a new repository named: class-cancellation-app
echo 3. Make it PUBLIC (important for free hosting)
echo 4. Copy the repository URL
echo.
echo Once you have the repository URL, run this command:
echo git remote add origin YOUR_REPOSITORY_URL
echo git push -u origin main
echo.
echo Replace YOUR_REPOSITORY_URL with your actual GitHub repository URL.
echo.

set /p repo_url="Enter your GitHub repository URL (or press Enter to skip): "
if not "%repo_url%"=="" (
    echo.
    echo Adding remote origin...
    git remote add origin %repo_url%
    
    echo.
    echo Pushing to GitHub...
    git push -u origin main
    
    echo.
    echo ========================================
    echo    Success! Your code is on GitHub.
    echo ========================================
    echo.
    echo Next steps:
    echo 1. Follow the DEPLOY_TO_PUBLIC.md guide
    echo 2. Deploy backend to Render
    echo 3. Deploy frontend to Vercel
    echo.
) else (
    echo.
    echo Skipping remote setup.
    echo You can add the remote later with:
    echo git remote add origin YOUR_REPOSITORY_URL
    echo git push -u origin main
)

echo.
echo Press any key to continue...
pause >nul 