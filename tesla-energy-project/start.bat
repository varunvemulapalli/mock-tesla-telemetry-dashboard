@echo off
REM Tesla Energy Device Software - Quick Start Script (Windows)

echo Starting Tesla Energy Device Software Dashboard...
echo.

REM Check if .env files exist
if not exist "backend\.env" (
    echo Warning: backend\.env not found. Creating from .env.example...
    if exist "backend\.env.example" (
        copy backend\.env.example backend\.env
        echo Created backend\.env - Please update with your OpenAI API key!
    )
)

if not exist "frontend\.env" (
    echo Warning: frontend\.env not found. Creating from .env.example...
    if exist "frontend\.env.example" (
        copy frontend\.env.example frontend\.env
        echo Created frontend\.env
    )
)

REM Start backend
echo.
echo Starting backend...
cd backend
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat
pip install -q -r requirements.txt

echo Starting FastAPI server...
start "Backend API" cmd /k "uvicorn app.main:app --reload --port 8000"
cd ..

timeout /t 3 /nobreak >nul

REM Start frontend
echo.
echo Starting frontend...
cd frontend
if not exist "node_modules" (
    echo Installing npm dependencies...
    call npm install
)

echo Starting React development server...
start "Frontend" cmd /k "npm start"
cd ..

echo.
echo Services starting...
echo.
echo Backend API: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Frontend: http://localhost:3000
echo.
echo Close the command windows to stop services
pause

