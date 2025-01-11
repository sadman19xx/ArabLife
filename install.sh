#!/bin/bash

# Update package list
echo "Updating package list..."
sudo apt-get update

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Installing..."
    sudo apt-get install -y python3
fi

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get install -y python3-full python3-pip python3-venv ffmpeg

# Remove old venv if it exists
if [ -d "venv" ]; then
    echo "Removing old virtual environment..."
    rm -rf venv
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Check if venv was created successfully
if [ ! -d "venv" ]; then
    echo "Failed to create virtual environment. Please ensure python3-venv is installed."
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Verify we're in the virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Failed to activate virtual environment"
    exit 1
fi

# Upgrade pip in the virtual environment
echo "Upgrading pip..."
./venv/bin/pip install --upgrade pip

# Install dependencies in the virtual environment
echo "Installing Python dependencies..."
./venv/bin/pip install wheel
./venv/bin/pip install -r requirements.txt

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p data
mkdir -p logs
mkdir -p fonts

# Check if welcome.mp3 exists
if [ ! -f "welcome.mp3" ]; then
    echo "Warning: welcome.mp3 not found in root directory"
    echo "Please place your welcome sound file at: $(pwd)/welcome.mp3"
fi

# Check if arabic.ttf exists
if [ ! -f "fonts/arabic.ttf" ]; then
    echo "Warning: arabic.ttf not found in fonts directory"
    echo "Please place your Arabic font file at: $(pwd)/fonts/arabic.ttf"
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOL
# Bot Configuration
TOKEN=your_bot_token_here
GUILD_ID=your_guild_id_here

# Channel IDs
WELCOME_CHANNEL_ID=0
WELCOME_VOICE_CHANNEL_ID=0
ROLE_ACTIVITY_LOG_CHANNEL_ID=0
AUDIT_LOG_CHANNEL_ID=0
ERROR_LOG_CHANNEL_ID=0

# Role IDs
ROLE_IDS_ALLOWED=
ROLE_ID_TO_GIVE=0
ROLE_ID_REMOVE_ALLOWED=0

# Welcome Settings
WELCOME_BACKGROUND_URL=https://i.imgur.com/your_background.png
WELCOME_MESSAGE=Welcome {user} to {server}! 🎉
WELCOME_EMBED_COLOR=0x2ecc71

# Security Settings
RAID_PROTECTION=true
SPAM_DETECTION=true
WARNING_THRESHOLD=3
WARNING_ACTION=timeout
WARNING_DURATION=3600
EOL
    echo "Please edit .env file with your configuration"
fi

echo "Installation complete!"
echo "Next steps:"
echo "1. Edit the .env file with your bot token and other settings"
echo "2. Place welcome.mp3 in the root directory for welcome sounds"
echo "3. Place arabic.ttf in the fonts directory for welcome messages"
echo "4. Run the bot with: ./venv/bin/python bot.py"

# Add venv activation to .bashrc if it doesn't exist
if ! grep -q "source $(pwd)/venv/bin/activate" ~/.bashrc; then
    echo "# Activate ArabLife bot virtual environment" >> ~/.bashrc
    echo "source $(pwd)/venv/bin/activate" >> ~/.bashrc
    echo "Added virtual environment activation to .bashrc"
fi
