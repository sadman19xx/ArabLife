#!/bin/bash

# Install Python dependencies if requirements.txt exists
if [[ -f requirements.txt ]]; then
    echo "Installing Python dependencies..."
    pip install -U --prefix .local -r requirements.txt
fi

# Start the bot
echo "Starting bot..."
python bot.py
