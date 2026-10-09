#!/bin/bash

# Script to start SignBridge with backend integration
set -e

echo "🚀 Starting SignBridge..."

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Function to cleanup on exit
cleanup() {
    echo "🛑 Cleaning up..."
    if [ ! -z "$BACKEND_PID" ]; then
        echo "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        echo "Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check if backend is already running
if curl -s http://127.0.0.1:8000/ >/dev/null 2>&1; then
    echo "✅ Backend already running on port 8000"
else
    echo "🔧 Starting backend..."
    
    # Activate Python environment and start backend
    cd backend
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    elif [ -f "py311_venv/bin/activate" ]; then
        source py311_venv/bin/activate
    elif [ -f "../.venv_exp/bin/activate" ]; then
        source ../.venv_exp/bin/activate
    fi
    
    # Start backend in background
    python run_backend.py &
    BACKEND_PID=$!
    cd ..
    
    echo "⏳ Waiting for backend to start..."
    
    # Wait for backend to be ready
    for i in {1..30}; do
        if curl -s http://127.0.0.1:8000/health >/dev/null 2>&1; then
            echo "✅ Backend started successfully (PID: $BACKEND_PID)"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "❌ Backend failed to start within 30 seconds"
            cleanup
        fi
        sleep 1
    done
fi

# Test backend functionality
echo "🧪 Testing backend health..."
if curl -s http://127.0.0.1:8000/health | grep -q "healthy"; then
    echo "✅ Backend API health check successful"
else
    echo "❌ Backend API health check failed"
    cleanup
fi

# Start Frontend
echo "🎨 Starting Frontend (Vite)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "🎉 SignBridge started successfully!"
echo "🔧 Backend running on http://127.0.0.1:8000"
echo "🌐 Frontend running on http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user to stop
wait 