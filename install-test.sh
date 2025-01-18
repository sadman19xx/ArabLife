#!/usr/bin/env bash
set -e

echo "Setting up ArabLife Discord Bot for testing..."

# Remove existing venv if it exists
if [ -d "venv" ]; then
    echo "Removing existing virtual environment..."
    rm -rf venv
fi

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Verify venv creation
if [ ! -f "venv/bin/activate" ]; then
    echo "❌ Failed to create virtual environment"
    echo "Trying alternative method..."
    rm -rf venv
    virtualenv venv
    if [ ! -f "venv/bin/activate" ]; then
        echo "❌ Virtual environment creation failed. Please check your Python installation."
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
. venv/bin/activate

# Verify activation
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ Virtual environment activation failed"
    exit 1
fi

# Install Python requirements
echo "Installing Python packages..."
pip3 install --upgrade pip
pip3 install -r requirements.txt

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p logs
mkdir -p data

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "Created .env file. Please update it with your bot settings."
    echo "Use Discord Developer Mode to get the correct role and channel IDs"
fi

# Make validation script executable
chmod +x validate_env.py

# Validate environment variables
echo "Validating environment variables..."
python3 validate_env.py
if [ $? -ne 0 ]; then
    echo "❌ Environment validation failed"
    echo "Please fix the errors in your .env file and run install-test.sh again"
    echo "Make sure all role and channel IDs are actual Discord IDs (numbers)"
    echo "Enable Developer Mode in Discord to get IDs (User Settings > App Settings > Advanced)"
    exit 1
fi

# Check if welcome.mp3 exists
if [ ! -f "welcome.mp3" ]; then
    echo "Warning: welcome.mp3 not found. Please add a welcome sound file."
fi

# Set correct permissions
chmod +x run.sh

echo "✅ Installation complete!"
echo "Please make sure your .env file is configured with correct Discord bot settings"
echo "You can now run the bot using: ./run.sh"
