#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting ArabLife Bot Setup...${NC}"

# Update package list and install required packages
echo -e "${YELLOW}Installing system dependencies...${NC}"
sudo apt update
sudo apt install -y python3 python3-pip git ffmpeg python3-venv screen

# Create bot directory if it doesn't exist
echo -e "${YELLOW}Creating bot directory...${NC}"
mkdir -p ~/bots
cd ~/bots

# Clone repository if it doesn't exist
if [ ! -d "ArabLife" ]; then
    echo -e "${YELLOW}Cloning repository...${NC}"
    git clone https://github.com/sadman19xx/ArabLife.git
fi

cd ArabLife

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    echo "Please enter the following information:"
    
    read -p "Discord Bot Token: " token
    read -p "Guild ID: " guild_id
    read -p "Role IDs Allowed (comma-separated): " role_ids_allowed
    read -p "Role ID to Give: " role_id_to_give
    read -p "Role ID Remove Allowed: " role_id_remove_allowed
    read -p "Role Activity Log Channel ID: " role_activity_log_channel_id
    read -p "Audit Log Channel ID: " audit_log_channel_id
    read -p "Visa Image URL: " visa_image_url

    cat > .env << EOL
TOKEN=${token}
GUILD_ID=${guild_id}
ROLE_IDS_ALLOWED=${role_ids_allowed}
ROLE_ID_TO_GIVE=${role_id_to_give}
ROLE_ID_REMOVE_ALLOWED=${role_id_remove_allowed}
ROLE_ACTIVITY_LOG_CHANNEL_ID=${role_activity_log_channel_id}
AUDIT_LOG_CHANNEL_ID=${audit_log_channel_id}
VISA_IMAGE_URL=${visa_image_url}
EOL
fi

# Make start script executable
chmod +x start.sh

echo -e "${GREEN}Setup completed successfully!${NC}"
echo -e "${YELLOW}To start the bot, run: ./start.sh${NC}"
