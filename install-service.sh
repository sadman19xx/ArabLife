#!/bin/bash

# Create log files and set permissions
sudo touch /var/log/arablife-bot.log
sudo touch /var/log/arablife-bot.error.log
sudo chmod 644 /var/log/arablife-bot.log
sudo chmod 644 /var/log/arablife-bot.error.log

# Copy service file to systemd directory
sudo cp arablife-bot.service /etc/systemd/system/

# Reload systemd daemon
sudo systemctl daemon-reload

# Enable and start the service
sudo systemctl enable arablife-bot
sudo systemctl start arablife-bot

# Check status
sudo systemctl status arablife-bot

echo "Service installation complete. View logs with:"
echo "sudo journalctl -u arablife-bot -f"
echo "or check the log files:"
echo "tail -f /var/log/arablife-bot.log"
echo "tail -f /var/log/arablife-bot.error.log"
