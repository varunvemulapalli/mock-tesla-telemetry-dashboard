#!/bin/bash

echo "Starting Tesla Energy Device Software Dashboard..."
echo ""

if [ ! -f "backend/.env" ]; then
    echo "backend/.env not found. Creating from .env.example..."
    if [ -f "backend/.env.example" ]; then
        cp backend/.env.example backend/.env
        echo "Created backend/.env - Please update with your OpenAI API key!"
    fi
fi

if [ ! -f "frontend/.env" ]; then
    echo "frontend/.env not found. Creating from .env.example..."
    if [ -f "frontend/.env.example" ]; then
        cp frontend/.env.example frontend/.env
        echo "Created frontend/.env"
    fi
fi

echo ""
echo "Starting backend..."
cd backend
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

echo "Starting FastAPI server..."
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

sleep 3

echo ""
echo "Starting frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
fi

echo "Starting React development server..."
npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "Services starting..."
echo ""
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo "Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait

