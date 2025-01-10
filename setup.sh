#!/bin/bash

# Exit on error
set -e

echo "Setting up ArabLife Discord Bot..."

# Update package list
sudo apt update

# Install system dependencies
echo "Installing system dependencies..."
sudo apt install -y python3 python3-pip python3-venv ffmpeg

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python packages..."
pip install -r requirements.txt

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p logs
mkdir -p data

# Set up environment file
if [ ! -f .env ]; then
    echo "Creating .env file..."
    echo "TOKEN=" > .env
    echo "GUILD_ID=" >> .env
    echo "ROLE_IDS_ALLOWED=" >> .env
    echo "ROLE_ID_TO_GIVE=" >> .env
    echo "ROLE_ID_REMOVE_ALLOWED=" >> .env
    echo "ROLE_ACTIVITY_LOG_CHANNEL_ID=" >> .env
    echo "AUDIT_LOG_CHANNEL_ID=" >> .env
    echo "WELCOME_CHANNEL_ID=" >> .env
    echo "WELCOME_BACKGROUND_URL=" >> .env
    echo "Please edit .env file with your bot settings"
fi

# Set up systemd service
echo "Setting up systemd service..."
sudo tee /etc/systemd/system/arablife-bot.service > /dev/null << EOL
[Unit]
Description=ArabLife Discord Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=$(pwd)/venv/bin/python3 bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOL

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable arablife-bot.service

echo "Setup complete!"
echo "Please edit the .env file with your bot settings"
echo "Then start the bot with: sudo systemctl start arablife-bot"
echo "Check status with: sudo systemctl status arablife-bot"
echo "View logs with: sudo journalctl -u arablife-bot -f"
