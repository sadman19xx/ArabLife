# ArabLife Discord Bot

A Discord bot for managing roles, voice channels, tickets, and more.

## Installation

1. Clone this repository to your server
2. Make the install script executable:
```bash
chmod +x install.sh
```

3. Run the installation script as root:
```bash
sudo ./install.sh
```

The script will:
- Install required system dependencies
- Set up Python virtual environment
- Install Python packages
- Create configuration file
- Clean up unnecessary files
- Set up the bot in /opt/arablife

During installation, you'll need to provide:
- Discord Bot Token
- Server (Guild) ID
- Role IDs
- Channel IDs

## Usage

The bot can be controlled using the following commands:

```bash
# Start the bot
./start.sh start

# Stop the bot
./start.sh stop

# Restart the bot
./start.sh restart

# Check bot status
./start.sh status
```

To view the bot console:
1. Type: `screen -r arablife`
2. To detach from console: Press `Ctrl+A` then `D`

## Required Permissions

The bot requires the following permissions:
- Manage Roles
- Manage Channels
- View Channels
- Send Messages
- Manage Messages
- Read Message History
- Connect to Voice
- Speak in Voice

## Features

- Role management
- Voice channel controls
- Ticket system
- Welcome messages
- Security features
- Leveling system
- Auto-moderation

## Support

If you encounter any issues:
1. Check the bot console for error messages
2. Verify all IDs in the .env file are correct
3. Ensure the bot has the required permissions
4. Check if all dependencies are installed correctly
