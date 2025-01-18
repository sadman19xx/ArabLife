#!/bin/bash

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo ./setup-test.sh)"
    exit 1
fi

echo "=== Setting up ArabLife Bot for testing ==="

# Step 1: Clean up any existing service installation
echo "Step 1: Cleaning up any existing service installation..."
./cleanup-service.sh
if [ $? -ne 0 ]; then
    echo "❌ Cleanup failed. Please check the errors above."
    exit 1
fi
echo "✅ Cleanup completed successfully"

# Step 2: Run fresh installation for testing
echo -e "\nStep 2: Setting up fresh installation..."
./install.sh
if [ $? -ne 0 ]; then
    echo "❌ Installation failed. Please check the errors above."
    exit 1
fi
echo "✅ Installation completed successfully"

echo -e "\n=== Setup Complete! ==="
echo "Your ArabLife Bot is now ready for testing."
echo "You can run the bot using: ./run.sh"
