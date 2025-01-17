#!/bin/bash

# Stop the bot service
systemctl stop arablife-bot

# Disable service from auto-starting
systemctl disable arablife-bot

# Kill any remaining bot processes
pkill -f "python3 /root/ArabLife/bot.py"

# Check status to verify it's stopped
systemctl status arablife-bot

echo "Bot service has been stopped and disabled"
