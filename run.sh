#!/bin/bash

# Function to check if a command exists
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo "Error: $1 is not installed. Please install it first."
        echo "You can install it with: sudo apt-get install $1"
        exit 1
    fi
}

# Check required system dependencies
echo "Checking system dependencies..."
check_command ffmpeg
check_command python3

# Check if virtual environment exists and is valid
if [ ! -d "venv" ] || [ ! -f "venv/bin/python" ]; then
    echo "Virtual environment not found or invalid. Please run ./install.sh first."
    exit 1
fi

# Check if welcome.mp3 exists
if [ ! -f "welcome.mp3" ]; then
    echo "Warning: welcome.mp3 not found. Welcome sounds will not work."
    echo "Please place your welcome sound file at: $(pwd)/welcome.mp3"
fi

# Check if arabic.ttf exists
if [ ! -f "fonts/arabic.ttf" ]; then
    echo "Warning: arabic.ttf not found. Welcome messages may not display correctly."
    echo "Please place your Arabic font file at: $(pwd)/fonts/arabic.ttf"
fi

# Check if .env exists and has required fields
if [ ! -f ".env" ]; then
    echo "Error: .env file not found. Please run ./install.sh first."
    exit 1
fi

# Validate .env file
if ! grep -q "^TOKEN=" .env || ! grep -q "^GUILD_ID=" .env; then
    echo "Error: .env file is missing required fields (TOKEN and/or GUILD_ID)"
    echo "Please edit .env file and add your bot token and guild ID"
    exit 1
fi

# Check if required directories exist
for dir in "data" "logs" "fonts"; do
    if [ ! -d "$dir" ]; then
        echo "Creating missing directory: $dir"
        mkdir -p "$dir"
    fi
done

# Use venv python directly instead of activating
echo "Starting ArabLife bot..."
exec ./venv/bin/python bot.py
