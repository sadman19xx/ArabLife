#!/bin/bash

# Git operations if needed
if [[ -d .git ]] && [[ "${AUTO_UPDATE}" == "1" ]]; then
    echo "Pulling latest changes..."
    git pull
fi

# Install dependencies
if [[ -f requirements.txt ]]; then
    echo "Installing dependencies..."
    pip install --disable-pip-version-check -U --prefix .local -r requirements.txt
fi

# Start the bot
echo "Starting bot..."
/usr/local/bin/python /home/container/bot.py
