#!/usr/bin/env bash
set -e

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run: sudo ./install.sh"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please run: sudo ./install.sh"
    exit 1
fi

echo "Starting ArabLife Discord Bot..."

# Activate virtual environment
source venv/bin/activate

# Run the bot
python3 bot.py
