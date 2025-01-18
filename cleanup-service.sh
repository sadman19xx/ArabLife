#!/bin/bash

# Function to check if script is run as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo "Please run as root (use sudo)"
        exit 1
    fi
}

# Function to stop and disable service
cleanup_service() {
    echo "=== Cleaning up arablife-bot service ==="
    echo "Stopping arablife-bot service..."
    systemctl stop arablife-bot.service

    echo "Disabling arablife-bot service..."
    systemctl disable arablife-bot.service

    echo "Removing service file..."
    rm -f /etc/systemd/system/arablife-bot.service

    echo "Reloading systemd daemon..."
    systemctl daemon-reload

    # Kill any remaining bot processes
    echo "Cleaning up any remaining processes..."
    pkill -f "python.*bot\.py"

    echo "Service cleanup completed!"
}

# Function to clean virtual environment
cleanup_venv() {
    echo "=== Cleaning up virtual environment ==="
    
    # Deactivate venv if it's active
    if [ -n "$VIRTUAL_ENV" ]; then
        echo "Deactivating virtual environment..."
        deactivate 2>/dev/null || true
    fi

    # Remove venv directory in current location
    if [ -d "venv" ]; then
        echo "Removing virtual environment directory..."
        rm -rf venv
    fi

    # Remove venv directory in /root/ArabLife if it exists
    if [ -d "/root/ArabLife/venv" ]; then
        echo "Removing virtual environment directory in /root/ArabLife..."
        rm -rf /root/ArabLife/venv
    fi

    # Remove any Python cache files
    echo "Removing Python cache files..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    find . -type f -name "*.pyd" -delete
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".coverage" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name ".coverage" -delete

    echo "Virtual environment cleanup completed!"
}

# Main execution
check_root
cleanup_service
cleanup_venv

echo "=== All cleanup tasks completed! ==="
