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

# Install backend dependencies if venv doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Setting up Python virtual environment...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Create frontend .env file
echo -e "${YELLOW}Creating frontend environment configuration...${NC}"
cat > dashboard/frontend/.env << EOL
REACT_APP_API_URL=http://${SERVER_IP}:8000
EOL

# Install frontend dependencies if node_modules doesn't exist
cd dashboard/frontend
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    bash setup-frontend.sh
fi

# Start backend server
echo -e "${YELLOW}Starting backend server...${NC}"
cd ../backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &

# Start frontend server
echo -e "${YELLOW}Starting frontend server...${NC}"
cd ../frontend
PORT=80 HOST=${SERVER_IP} npm start &

echo -e "${GREEN}Development servers are running!${NC}"
echo -e "Backend: ${GREEN}http://${SERVER_IP}:8000${NC}"
echo -e "Frontend: ${GREEN}http://${SERVER_IP}${NC}"
echo -e "\nPress ${YELLOW}Ctrl+C${NC} to stop both servers\n"

# Wait for both servers
wait
