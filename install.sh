#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Check if welcome.mp3 exists
if [ ! -f "welcome.mp3" ]; then
    echo "Warning: welcome.mp3 not found. Please add a welcome sound file."
fi

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Created .env file. Please update it with your bot settings."
fi

echo "Installation complete!"
