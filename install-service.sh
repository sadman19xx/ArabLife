#!/bin/bash

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo ./install-service.sh)"
    exit 1
fi

echo "Installing ArabLife Discord Bot Service..."

# Create log files and set permissions
echo "Setting up log files..."
touch /var/log/arablife-bot.log
touch /var/log/arablife-bot.error.log
chmod 644 /var/log/arablife-bot.log
chmod 644 /var/log/arablife-bot.error.log

# Ensure the virtual environment exists
if [ ! -d "/root/ArabLife/venv" ]; then
    echo "Virtual environment not found. Please run install.sh first."
    exit 1
fi

# Ensure required directories exist
echo "Creating required directories..."
mkdir -p /root/ArabLife/logs
mkdir -p /root/ArabLife/data
chmod 755 /root/ArabLife/logs
chmod 755 /root/ArabLife/data

# Copy service file
echo "Installing systemd service..."
cp arablife-bot.service /etc/systemd/system/

# Reload systemd daemon
echo "Reloading systemd daemon..."
systemctl daemon-reload

# Enable and start service
echo "Enabling and starting service..."
systemctl enable arablife-bot
systemctl start arablife-bot

# Check service status
echo "Service status:"
systemctl status arablife-bot

echo "
Installation complete! You can manage the service with:
- View status: sudo systemctl status arablife-bot
- View logs: 
  * sudo journalctl -u arablife-bot -f
  * tail -f /var/log/arablife-bot.log
  * tail -f /var/log/arablife-bot.error.log
- Start: sudo systemctl start arablife-bot
- Stop: sudo systemctl stop arablife-bot
- Restart: sudo systemctl restart arablife-bot
"
