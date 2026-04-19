#!/bin/bash

# Enable monitor mode so background processes get their own process group.
# This prevents them from receiving SIGINT directly from the terminal, 
# preventing double-signaling which causes messy python stacktraces.
set -m

# Store PIDs
BACKEND_PID=""
FRONTEND_PID=""

# Function to safely kill child process groups
cleanup() {
    # Remove traps to prevent double execution
    trap - SIGINT SIGTERM EXIT
    
    echo -e "\nStopping all services..."
    
    if [ -n "$BACKEND_PID" ]; then
        if kill -0 "$BACKEND_PID" 2>/dev/null; then
            echo "Stopping Backend (PID: $BACKEND_PID)..."
            # Send graceful termination to the process group
            kill -TERM "-$BACKEND_PID" 2>/dev/null || true
            
            # Wait up to 3 seconds for it to exit
            for i in {1..30}; do
                if ! kill -0 "$BACKEND_PID" 2>/dev/null; then break; fi
                sleep 0.1
            done
            
            # Force kill if still running
            if kill -0 "$BACKEND_PID" 2>/dev/null; then
                echo "Backend did not stop gracefully. Force killing..."
                kill -9 "-$BACKEND_PID" 2>/dev/null || true
            fi
        fi
    fi
    
    if [ -n "$FRONTEND_PID" ]; then
        if kill -0 "$FRONTEND_PID" 2>/dev/null; then
            echo "Stopping Frontend (PID: $FRONTEND_PID)..."
            kill -TERM "-$FRONTEND_PID" 2>/dev/null || true
            
            for i in {1..30}; do
                if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then break; fi
                sleep 0.1
            done
            
            if kill -0 "$FRONTEND_PID" 2>/dev/null; then
                echo "Frontend did not stop gracefully. Force killing..."
                kill -9 "-$FRONTEND_PID" 2>/dev/null || true
            fi
        fi
    fi
    
    exit 0
}

# Trap SIGINT, SIGTERM, and EXIT
trap cleanup SIGINT SIGTERM EXIT

echo "Starting SecondMate Development Environment..."

export SECONDMATE_RESULT_CATALOG="user"
export SECONDMATE_RESULT_NAMESPACE="secondmate"

# Start Backend
echo "Starting Backend (FastAPI)..."
(
    if command -v uv >/dev/null 2>&1 && [ -f "uv.lock" ]; then
        exec uv run uvicorn secondmate.main:app --reload --host 0.0.0.0
    else
        if [ -d ".venv" ]; then
            source .venv/bin/activate
        elif [ -d "venv" ]; then
            source venv/bin/activate
        fi
        exec uvicorn secondmate.main:app --reload --host 0.0.0.0
    fi
) &
BACKEND_PID=$!

# Start Frontend
echo "Starting Frontend (Vite)..."
(
    exec npm run dev
) &
FRONTEND_PID=$!

# Wait for the first process to exit.
wait -n
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ] && [ $EXIT_CODE -lt 128 ]; then
    echo "A service exited unexpectedly (exit code $EXIT_CODE). Shutting down..."
fi
