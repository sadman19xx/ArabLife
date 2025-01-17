#!/bin/bash

# Create virtual environment directory if it doesn't exist
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

echo "Virtual environment setup complete. Use 'source venv/bin/activate' to activate it"
