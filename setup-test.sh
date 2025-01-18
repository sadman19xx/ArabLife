#!/bin/bash

echo "=== Setting up ArabLife Bot for testing ==="

# Ensure all scripts are executable
echo "Ensuring scripts have correct permissions..."
chmod +x install-test.sh run.sh cleanup-service.sh

# Step 1: Clean up any existing service installation (requires sudo)
echo "Step 1: Cleaning up any existing service installation..."
if [ "$EUID" -ne 0 ]; then
    echo "Cleanup requires root privileges. Please enter your password:"
    sudo ./cleanup-service.sh
else
    ./cleanup-service.sh
fi
if [ $? -ne 0 ]; then
    echo "❌ Cleanup failed. Please check the errors above."
    exit 1
fi
echo "✅ Cleanup completed successfully"

# Step 2: Run fresh installation for testing
echo -e "\nStep 2: Setting up fresh installation..."
./install-test.sh
if [ $? -ne 0 ]; then
    echo "❌ Installation failed. Please check the errors above."
    exit 1
fi
echo "✅ Installation completed successfully"

echo -e "\n=== Setup Complete! ==="
echo "Your ArabLife Bot is now ready for testing."
echo "You can run the bot using: ./run.sh"
