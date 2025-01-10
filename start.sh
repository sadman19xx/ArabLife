#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0m'
NC='\033[0m'

# Get the directory of the script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Function to check if a screen session exists
screen_exists() {
    screen -list | grep -q "$1"
}

# Kill existing screen sessions if they exist
if screen_exists "arablife-backend"; then
    screen -S arablife-backend -X quit
fi
if screen_exists "arablife-frontend"; then
    screen -S arablife-frontend -X quit
fi

# Build frontend
echo -e "${YELLOW}Building frontend...${NC}"
cd "${DIR}/dashboard/frontend"
npm run build

# Start backend server
echo -e "${YELLOW}Starting backend server...${NC}"
cd "${DIR}/dashboard/backend"
source venv/bin/activate
screen -dmS arablife-backend bash -c "cd '${DIR}/dashboard/backend' && source venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000"
deactivate

# Start frontend using serve
echo -e "${YELLOW}Starting frontend server...${NC}"
cd "${DIR}/dashboard/frontend"
if ! command -v serve &> /dev/null; then
    npm install -g serve
fi
screen -dmS arablife-frontend bash -c "cd '${DIR}/dashboard/frontend' && serve -s build -l 3000"

# Wait for servers to start
sleep 5

# Check if servers are running
if screen_exists "arablife-backend"; then
    echo -e "${GREEN}Backend server is running${NC}"
    echo -e "API available at: ${GREEN}http://45.76.83.149/api${NC}"
    echo -e "API docs available at: ${GREEN}http://45.76.83.149/docs${NC}"
else
    echo -e "${RED}Backend server failed to start${NC}"
fi

if screen_exists "arablife-frontend"; then
    echo -e "${GREEN}Frontend server is running${NC}"
    echo -e "Dashboard available at: ${GREEN}http://45.76.83.149${NC}"
else
    echo -e "${RED}Frontend server failed to start${NC}"
fi

echo -e "\n${YELLOW}To view server logs:${NC}"
echo -e "Backend: ${GREEN}screen -r arablife-backend${NC}"
echo -e "Frontend: ${GREEN}screen -r arablife-frontend${NC}"
echo -e "\nTo detach from a screen session: ${GREEN}Ctrl+A then D${NC}"
