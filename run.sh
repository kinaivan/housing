#!/bin/bash

# Colors for pretty output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Housing Market Simulation...${NC}\n"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Redis is running
if ! docker ps | grep -q redis; then
    echo -e "${BLUE}Starting Redis...${NC}"
    docker run -d -p 6379:6379 --name housing-redis redis
    sleep 2
fi

# Initialize trap to handle shutdown
cleanup() {
    echo "Shutting down services..."
    
    # Kill all background processes in this session
    if [ -n "$(jobs -p)" ]; then
        kill $(jobs -p) 2>/dev/null
    fi
    
    # Additional cleanup for any hanging Python/Node processes
    echo "Checking for hanging processes..."
    
    # Check and kill any process using the backend port (8000)
    if lsof -ti:8000 >/dev/null; then
        echo "Cleaning up backend process..."
        lsof -ti:8000 | xargs kill -9 2>/dev/null
    fi
    
    # Check and kill any process using the frontend port (5173)
    if lsof -ti:5173 >/dev/null; then
        echo "Cleaning up frontend process..."
        lsof -ti:5173 | xargs kill -9 2>/dev/null
    fi
    
    echo "Shutdown complete"
    exit 0
}

# Set up trap for clean shutdown
trap cleanup SIGINT SIGTERM

# Activate virtual environment
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

# Install frontend dependencies if needed
if [ ! -d "frontend/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

# Start backend server
echo "Starting backend server..."
cd backend
# Add both the project root and backend directories to PYTHONPATH
export PYTHONPATH=$PWD:$PWD/..
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &

# Start Celery worker
echo "Starting Celery worker..."
celery -A celery_app worker --loglevel=info &
cd ..

# Start frontend development server
echo "Starting frontend server..."
cd frontend
npm run dev &
cd ..

echo "All services started!"
echo "Frontend: http://localhost:5173"
echo "Backend documentation: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for any background process to exit
wait 