#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Server IP
SERVER_IP="45.76.83.149"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for required commands
if ! command_exists python3; then
    echo -e "${RED}Error: python3 is not installed${NC}"
    exit 1
fi

if ! command_exists npm; then
    echo -e "${RED}Error: npm is not installed${NC}"
    exit 1
fi

# Function to kill background processes on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down servers...${NC}"
    kill $(jobs -p) 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Get the directory of the script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Setup backend
echo -e "${YELLOW}Setting up backend...${NC}"

# Create and activate virtual environment in the backend directory
if [ ! -d "${DIR}/dashboard/backend/venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    cd "${DIR}/dashboard/backend"
    python3 -m venv venv
    cd "${DIR}"
fi

# Activate virtual environment
source "${DIR}/dashboard/backend/venv/bin/activate" || {
    echo -e "${RED}Failed to activate virtual environment${NC}"
    exit 1
}

# Install backend dependencies
echo -e "${YELLOW}Installing backend dependencies...${NC}"
cd "${DIR}/dashboard/backend"
pip install -r requirements.txt || {
    echo -e "${RED}Failed to install backend dependencies${NC}"
    exit 1
}

cd "${DIR}"

# Setup frontend
echo -e "${YELLOW}Setting up frontend...${NC}"
cd "${DIR}/dashboard/frontend"

# Copy development environment file if it doesn't exist
if [ ! -f ".env.development" ]; then
    echo -e "${YELLOW}Creating development environment configuration...${NC}"
    cat > .env.development << EOL
PORT=3000
HOST=${SERVER_IP}
REACT_APP_API_URL=http://${SERVER_IP}:8000
WDS_SOCKET_HOST=${SERVER_IP}
WDS_SOCKET_PORT=3000
EOL
fi

# Install frontend dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    npm install || {
        echo -e "${RED}Failed to install frontend dependencies${NC}"
        exit 1
    }
fi

# Create public directory if it doesn't exist
mkdir -p public

cd "${DIR}"

# Start backend server
echo -e "${YELLOW}Starting backend server...${NC}"
cd "${DIR}/dashboard/backend"
source venv/bin/activate
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &

# Start frontend server
echo -e "${YELLOW}Starting frontend server...${NC}"
cd "${DIR}/dashboard/frontend"
BROWSER=none NODE_ENV=development npm start &

# Wait a moment to check if servers started successfully
sleep 5

# Check if servers are running
if ! pgrep -f "uvicorn" > /dev/null; then
    echo -e "${RED}Backend server failed to start${NC}"
    cleanup
fi

if ! pgrep -f "react-scripts start" > /dev/null; then
    echo -e "${RED}Frontend server failed to start${NC}"
    cleanup
fi

echo -e "${GREEN}Development servers are running!${NC}"
echo -e "Backend: ${GREEN}http://${SERVER_IP}:8000${NC}"
echo -e "Frontend: ${GREEN}http://${SERVER_IP}${NC} (proxied through nginx)"
echo -e "\nPress ${YELLOW}Ctrl+C${NC} to stop both servers\n"

# Wait for both servers
wait
