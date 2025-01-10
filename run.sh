#!/bin/bash

# Exit on error
set -e

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found"
    echo "Please run setup.sh first"
    exit 1
fi

# Run the bot
echo "Starting ArabLife Discord Bot..."
python3 bot.py
