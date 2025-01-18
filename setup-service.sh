#!/bin/bash

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo ./setup-service.sh)"
    exit 1
fi

echo "=== Starting complete ArabLife Bot setup process ==="

# Step 1: Run the installation script
echo "Step 1: Running installation script..."
./install.sh
if [ $? -ne 0 ]; then
    echo "❌ Installation failed. Please check the errors above."
    exit 1
fi
echo "✅ Installation completed successfully"

# Step 2: Install the service
echo -e "\nStep 2: Setting up systemd service..."
./install-service.sh
if [ $? -ne 0 ]; then
    echo "❌ Service installation failed. Please check the errors above."
    exit 1
fi
echo "✅ Service setup completed successfully"

echo -e "\n=== Setup Complete! ==="
echo "Your ArabLife Bot is now installed and running as a service."
echo "You can manage it using the following commands:"
echo "- Check status: sudo systemctl status arablife-bot"
echo "- View logs: sudo journalctl -u arablife-bot -f"
echo "- Start: sudo systemctl start arablife-bot"
echo "- Stop: sudo systemctl stop arablife-bot"
echo "- Restart: sudo systemctl restart arablife-bot"
