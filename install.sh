#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting ArabLife Bot Installation...${NC}"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install system dependencies
install_system_deps() {
    echo -e "${YELLOW}Installing system dependencies...${NC}"
    if command_exists apt-get; then
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip python3-venv git ffmpeg screen
    elif command_exists yum; then
        sudo yum update -y
        sudo yum install -y python3 python3-pip git ffmpeg screen
    else
        echo -e "${RED}Unsupported package manager. Please install dependencies manually:${NC}"
        echo "- python3"
        echo "- python3-pip"
        echo "- python3-venv"
        echo "- git"
        echo "- ffmpeg"
        echo "- screen"
        exit 1
    fi
}

# Function to set up Python virtual environment
setup_venv() {
    echo -e "${YELLOW}Setting up Python virtual environment...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
}

# Function to create .env file
create_env() {
    echo -e "${YELLOW}Setting up environment configuration...${NC}"
    echo -e "Please enter the following information:"
    
    read -p "Discord Bot Token: " token
    read -p "Discord Server (Guild) ID: " guild_id
    read -p "Allowed Role IDs (comma-separated): " role_ids_allowed
    read -p "Role ID to Give: " role_id_to_give
    read -p "Role ID Remove Allowed: " role_id_remove_allowed
    read -p "Role Activity Log Channel ID: " role_activity_log_channel_id
    read -p "Audit Log Channel ID: " audit_log_channel_id
    
    cat > .env << EOL
TOKEN=${token}
GUILD_ID=${guild_id}
ROLE_IDS_ALLOWED=${role_ids_allowed}
ROLE_ID_TO_GIVE=${role_id_to_give}
ROLE_ID_REMOVE_ALLOWED=${role_id_remove_allowed}
ROLE_ACTIVITY_LOG_CHANNEL_ID=${role_activity_log_channel_id}
AUDIT_LOG_CHANNEL_ID=${audit_log_channel_id}
VISA_IMAGE_URL=https://i.imgur.com/default.png
EOL

    echo -e "${GREEN}Environment configuration created successfully!${NC}"
}

# Function to clean up unnecessary files
cleanup() {
    echo -e "${YELLOW}Cleaning up unnecessary files...${NC}"
    rm -rf dashboard/
    rm -f docker-compose.yml Dockerfile
    rm -f test_bot.py
    rm -f README_BASIC.md
    rm -f setup.sh
    rm -f run.sh
}

# Main installation process
main() {
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then 
        echo -e "${RED}Please run as root or with sudo${NC}"
        exit 1
    }

    # Install system dependencies
    install_system_deps

    # Create bot directory if it doesn't exist
    echo -e "${YELLOW}Creating bot directory...${NC}"
    mkdir -p /opt/arablife
    cd /opt/arablife

    # Set up Python environment
    setup_venv

    # Create environment configuration
    create_env

    # Clean up unnecessary files
    cleanup

    # Make start script executable
    chmod +x start.sh

    echo -e "${GREEN}Installation completed successfully!${NC}"
    echo -e "${YELLOW}To start the bot:${NC}"
    echo -e "1. cd /opt/arablife"
    echo -e "2. Run: ${GREEN}./start.sh start${NC}"
    echo -e "\nTo view bot console:"
    echo -e "1. Run: ${GREEN}screen -r arablife${NC}"
    echo -e "2. To detach from console: Press ${GREEN}Ctrl+A${NC} then ${GREEN}D${NC}"
}

# Run the installation
main
