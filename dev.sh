#!/bin/bash

# Store PIDs
BACKEND_PID=""
FRONTEND_PID=""

# Function to kill child processes
cleanup() {
    echo ""
    echo "Stopping all services..."
    if [ -n "$BACKEND_PID" ]; then
        echo "Stopping Backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null
    fi
    if [ -n "$FRONTEND_PID" ]; then
        echo "Stopping Frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null
    fi
    exit 0
}

# Trap SIGINT and SIGTERM
trap cleanup SIGINT SIGTERM

echo "Starting SecondMate Development Environment..."

# Start Backend
echo "Starting Backend (FastAPI)..."
(
    # Activate virtual environment if it exists
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    elif [ -d "venv" ]; then
        source venv/bin/activate
    fi
    uvicorn secondmate.main:app --reload --host 0.0.0.0
) &
BACKEND_PID=$!

# Start Frontend
echo "Starting Frontend (Vite)..."
(
    npm run dev
) &
FRONTEND_PID=$!

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID
