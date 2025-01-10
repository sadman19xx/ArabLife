#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Get the directory of the script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Create backend directory if it doesn't exist
mkdir -p "${DIR}/dashboard/backend"

# Copy requirements.txt to backend directory
echo -e "${YELLOW}Copying requirements.txt to backend directory...${NC}"
cp "${DIR}/requirements.txt" "${DIR}/dashboard/backend/requirements.txt"

echo -e "${GREEN}Requirements copied successfully!${NC}"
echo -e "Now you can run ${YELLOW}sudo ./setup-server.sh${NC} to complete the setup"
