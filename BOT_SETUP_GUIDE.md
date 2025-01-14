# ArabLife Bot Setup Guide

This guide will walk you through setting up the ArabLife Discord bot.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- A Discord account
- A Discord application and bot token

## Step 1: Create a Discord Application

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" section and click "Add Bot"
4. Copy your bot token (you'll need this later)
5. Enable necessary Privileged Gateway Intents:
   - Presence Intent
   - Server Members Intent
   - Message Content Intent

## Step 2: Clone and Configure the Bot

1. Clone the repository to your local machine
2. Create a `.env` file in the root directory using `.env.example` as a template:
   ```
   # Copy the .env.example file
   cp .env.example .env
   ```
3. Open the `.env` file and fill in your configuration:
   - `DISCORD_TOKEN`: Your bot token from Step 1
   - Other required environment variables as specified in the file

## Step 3: Installation

1. Run the installation script:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```
   This will:
   - Create a virtual environment
   - Install required Python packages
   - Set up the database

## Step 4: Running the Bot

1. Start the bot using the run script:
   ```bash
   chmod +x run.sh
   ./run.sh
   ```

## Available Commands

The bot includes several modules with different functionalities:

- **Application Commands**: Handle user applications
- **Help Commands**: Display bot commands and usage
- **Role Commands**: Manage server roles
- **Security Commands**: Security features
- **Status Commands**: Bot and server status
- **Voice Commands**: Voice channel management
- **Welcome Commands**: Welcome new members

## Troubleshooting

If you encounter any issues:

1. Verify your `.env` file is properly configured
2. Check the bot logs for error messages
3. Ensure all required permissions are granted to the bot
4. Verify Python version compatibility
5. Check if all dependencies are properly installed

## System Service (Linux)

For Linux systems, you can set up the bot as a system service:

1. Copy the service file:
   ```bash
   sudo cp arablife-bot.service /etc/systemd/system/
   ```
2. Enable and start the service:
   ```bash
   sudo systemctl enable arablife-bot
   sudo systemctl start arablife-bot
   ```
3. Check service status:
   ```bash
   sudo systemctl status arablife-bot
   ```

## Logging Configuration

The bot uses specific Discord channels for different types of logs:

1. Error Logs Channel (ID: 1327648816874262549)
   - Critical errors and exceptions
   - System warnings
   - Important runtime issues

2. Audit Logs Channel (ID: 1286684861234417704)
   - Administrative actions
   - Rule changes
   - Server configuration updates
   - Moderation actions

Note: The bot is configured to minimize log spam by only logging important events.

## Environment Validation

Before running the bot, you can validate your environment configuration:
```bash
python validate_env.py
```

## Support

If you need help or encounter issues:
1. Check the documentation in README.md
2. Review error logs in the logs directory
3. Verify all environment variables are properly set
4. Ensure all required bot permissions are configured in Discord

## Security Notes

1. Never share your bot token
2. Keep your `.env` file secure
3. Regularly update dependencies
4. Monitor bot logs for suspicious activity
5. Regularly backup your database
