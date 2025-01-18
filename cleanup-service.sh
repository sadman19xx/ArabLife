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

# Main execution
check_root
cleanup_service
