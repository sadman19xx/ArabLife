#!/bin/bash

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Please run ./install.sh first."
    exit 1
fi

# Check if welcome.mp3 exists
if [ ! -f "welcome.mp3" ]; then
    echo "Warning: welcome.mp3 not found. Welcome sounds will not work."
fi

# Check if arabic.ttf exists
if [ ! -f "fonts/arabic.ttf" ]; then
    echo "Warning: arabic.ttf not found. Welcome messages may not display correctly."
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Error: .env file not found. Please run ./install.sh first."
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Start the bot
echo "Starting ArabLife bot..."
python bot.py
