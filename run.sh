#!/usr/bin/env bash
set -e

# Check if virtual environment exists and is valid
if [ ! -f "venv/bin/activate" ]; then
    echo "❌ Virtual environment not found or corrupted. Please run: sudo ./install.sh"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please run: sudo ./install.sh"
    exit 1
fi

echo "Starting ArabLife Discord Bot..."

# Activate virtual environment
echo "Activating virtual environment..."
. venv/bin/activate

# Verify activation
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ Virtual environment activation failed"
    echo "Please run: sudo ./install.sh"
    exit 1
fi

# Run the bot
python3 bot.py
