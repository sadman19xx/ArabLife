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

# Remove old virtual environment if it exists
if [ -d "${DIR}/dashboard/backend/venv" ]; then
    echo -e "${YELLOW}Removing old virtual environment...${NC}"
    rm -rf "${DIR}/dashboard/backend/venv"
fi

# Create and activate virtual environment
echo -e "${YELLOW}Creating new virtual environment...${NC}"
cd "${DIR}/dashboard/backend"
python3 -m venv venv
source venv/bin/activate || {
    echo -e "${RED}Failed to activate virtual environment${NC}"
    exit 1
}

# Install backend dependencies
echo -e "${YELLOW}Installing backend dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt || {
    echo -e "${RED}Failed to install backend dependencies${NC}"
    exit 1
}

cd "${DIR}"

# Setup frontend
echo -e "${YELLOW}Setting up frontend...${NC}"
cd "${DIR}/dashboard/frontend"

# Create .env file
echo -e "${YELLOW}Creating environment configuration...${NC}"
cat > .env << EOL
DANGEROUSLY_DISABLE_HOST_CHECK=true
HOST=${SERVER_IP}
PORT=3000
REACT_APP_API_URL=http://${SERVER_IP}:8000
EOL

# Create public directory and required files
echo -e "${YELLOW}Setting up public directory...${NC}"
mkdir -p public
cat > public/index.html << EOL
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="ArabLife Bot Dashboard" />
    <title>ArabLife Bot</title>
    <link
      rel="stylesheet"
      href="https://fonts.googleapis.com/css?family=Roboto:300,400,500,700&display=swap"
    />
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
EOL

cat > public/manifest.json << EOL
{
  "short_name": "ArabLife Bot",
  "name": "ArabLife Discord Bot Dashboard",
  "start_url": ".",
  "display": "standalone",
  "theme_color": "#000000",
  "background_color": "#ffffff"
}
EOL

# Install frontend dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    npm install || {
        echo -e "${RED}Failed to install frontend dependencies${NC}"
        exit 1
    }
fi

cd "${DIR}"

# Start backend server
echo -e "${YELLOW}Starting backend server...${NC}"
cd "${DIR}/dashboard/backend"
source venv/bin/activate
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &

# Wait for backend to start
sleep 5

# Start frontend server
echo -e "${YELLOW}Starting frontend server...${NC}"
cd "${DIR}/dashboard/frontend"
BROWSER=none npm start &

# Wait for frontend to start
sleep 5

echo -e "${GREEN}Development servers are running!${NC}"
echo -e "Backend: ${GREEN}http://${SERVER_IP}:8000${NC}"
echo -e "Frontend: ${GREEN}http://${SERVER_IP}${NC} (proxied through nginx)"
echo -e "\nPress ${YELLOW}Ctrl+C${NC} to stop both servers\n"

# Wait for both servers
wait
