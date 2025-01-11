#!/bin/bash

# Update package list
echo "Updating package list..."
sudo apt-get update

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get install -y python3 python3-pip python3-venv ffmpeg

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install dependencies
echo "Installing Python dependencies..."
pip install wheel
pip install -r requirements.txt

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
echo "4. Run the bot with: python bot.py"
