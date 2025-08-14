# 🚀 Quick Start Guide - Class Cancellation App

## 📋 Prerequisites

Before running the app, make sure you have installed:

1. **Python 3.8+** - Download from [python.org](https://python.org)
2. **Node.js 14+** - Download from [nodejs.org](https://nodejs.org)

## 🖱️ Option 1: One-Click App Launcher (Recommended)

### For Complete App (Backend + Frontend):
1. **Double-click** `start_app.bat`
2. The script will automatically:
   - Install all dependencies
   - Start the backend server (port 8000)
   - Start the frontend server (port 3000)
   - Open your browser to the app

### For Backend Only:
1. **Double-click** `start_backend_only.bat`
2. The backend server will start on `http://localhost:8000`

## 💻 Option 2: Manual Command Line

### Running the Backend:

1. **Open Command Prompt/PowerShell** in the project folder
2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Start the backend server:**
   ```bash
   python -m uvicorn backend:app --host 0.0.0.0 --port 8000 --reload
   ```

### Running the Frontend:

1. **Open a new Command Prompt/PowerShell** in the project folder
2. **Navigate to frontend folder:**
   ```bash
   cd frontend
   ```
3. **Install Node.js dependencies:**
   ```bash
   npm install
   ```
4. **Start the frontend server:**
   ```bash
   npm start
   ```

## 🌐 Accessing Your App

- **Frontend (Web Interface):** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs

## 📁 Important Files

- `Class Cancellation App.xlsx` - Your data file (make sure this exists)
- `backend.py` - FastAPI backend server
- `requirements.txt` - Python dependencies
- `frontend/` - React frontend application

## 🔧 Troubleshooting

### If the app doesn't start:

1. **Check Python installation:**
   ```bash
   python --version
   ```

2. **Check Node.js installation:**
   ```bash
   node --version
   ```

3. **Make sure Excel file exists:**
   - Verify `Class Cancellation App.xlsx` is in the project folder

4. **Check if ports are available:**
   - Backend uses port 8000
   - Frontend uses port 3000
   - Make sure these ports aren't used by other applications

### Common Issues:

- **"Python not found"** - Install Python and add to PATH
- **"Node not found"** - Install Node.js and add to PATH
- **"Port already in use"** - Close other applications using ports 8000/3000
- **"Excel file not found"** - Make sure the Excel file is in the correct location

## 🛑 Stopping the App

- **If using batch files:** Close the command windows
- **If using manual commands:** Press `Ctrl+C` in each terminal window

## 📞 Support

If you encounter any issues, check:
1. All prerequisites are installed
2. Excel file is in the correct location
3. No other applications are using the required ports 