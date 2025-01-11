#!/bin/bash

# Exit on error
set -e

echo "Setting up ArabLife Discord Bot..."

# Update package list
sudo apt update

# Install system dependencies
echo "Installing system dependencies..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv ffmpeg

# Verify FFmpeg installation
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ FFmpeg installation failed"
    echo "Trying alternative installation method..."
    sudo apt install -y software-properties-common
    sudo add-apt-repository ppa:mc3man/trusty-media
    sudo apt update
    sudo apt install -y ffmpeg
    if ! command -v ffmpeg &> /dev/null; then
        echo "❌ FFmpeg installation failed. Please install manually."
        exit 1
    fi
fi
echo "✅ FFmpeg installed successfully"

# Set correct FFmpeg path in .env
if [ -f .env ]; then
    sed -i 's|^FFMPEG_PATH=.*|FFMPEG_PATH=/usr/bin/ffmpeg|' .env
    echo "✅ Updated FFmpeg path in .env"
fi

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python packages..."
pip install -r requirements.txt

# Make validation script executable
chmod +x validate_env.py

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "Please edit .env file with your Discord bot settings"
    echo "Use Discord Developer Mode to get the correct role and channel IDs"
    exit 1
fi

# Validate environment variables
echo "Validating environment variables..."
python3 validate_env.py
if [ $? -ne 0 ]; then
    echo "❌ Environment validation failed"
    echo "Please fix the errors in your .env file and run setup.sh again"
    echo "Make sure all role and channel IDs are actual Discord IDs (numbers)"
    echo "Enable Developer Mode in Discord to get IDs (User Settings > App Settings > Advanced)"
    exit 1
fi

echo "✅ Environment validation successful"

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

echo "Setup complete!"
echo "Please edit the .env file with your bot settings"
echo "Then run the bot with: ./run.sh"
echo "For production deployment, consider setting up a systemd service"
