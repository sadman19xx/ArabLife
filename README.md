# ArabLife Discord Bot

A Discord bot for managing roles, voice channels, tickets, and more.

## Installation Methods

You can install and manage the bot in two ways:

### Method 1: Web Dashboard (Recommended)

1. Access the dashboard:
```
http://45.76.83.149
```

The web interface provides:
- Easy bot installation and configuration
- Real-time bot status monitoring
- Start/stop controls
- Live log viewer

2. Navigate to "Bot Installation" in the sidebar
3. Fill in the required information:
   - Bot Token
   - Server ID
   - Role IDs
   - Channel IDs
4. Click "Install Bot" to set up the bot
5. Use the control panel to start/stop the bot and view logs

### Method 2: Command Line

1. Connect to the server:
```bash
ssh root@45.76.83.149
```

2. Make the installation script executable:
```bash
chmod +x install.sh
```

3. Run the installation script:
```bash
sudo ./install.sh
```

4. During installation, you'll be prompted for:
   - Discord Bot Token
   - Server ID
   - Role IDs
   - Channel IDs

5. After installation, use these commands to manage the bot:
```bash
./start.sh start    # Start the bot
./start.sh stop     # Stop the bot
./start.sh restart  # Restart the bot
./start.sh status   # Check bot status
```

## Getting Required Information

### 1. Create Discord Bot Application

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
   - Name your application (e.g., "ArabLife")
   - Click "Create"
3. Go to "Bot" section in left sidebar
   - Click "Add Bot"
   - Click "Yes, do it!"
4. Under the bot's username:
   - Click "Copy" to copy your bot token
   - Save this token - you'll need it during installation
5. Enable Required Intents:
   - PRESENCE INTENT
   - SERVER MEMBERS INTENT
   - MESSAGE CONTENT INTENT
6. Add Bot to Your Server:
   - Go to "OAuth2" → "URL Generator"
   - Select scopes: "bot" and "applications.commands"
   - Select bot permissions:
     * Manage Roles
     * Manage Channels
     * View Channels
     * Send Messages
     * Manage Messages
     * Read Message History
     * Connect
     * Speak
   - Copy generated URL
   - Open URL in browser to add bot to your server

### 2. Get Required IDs

1. Enable Discord Developer Mode:
   - Open Discord Settings
   - Go to "App Settings" → "Advanced"
   - Enable "Developer Mode"

2. Get Server (Guild) ID:
   - Right-click your server name
   - Click "Copy ID"

3. Get Role IDs:
   - Right-click each role
   - Click "Copy ID"
   - You'll need:
     * Allowed Role IDs (can be multiple, separate with commas)
     * Role ID to Give
     * Role ID Remove Allowed

4. Get Channel IDs:
   - Right-click each channel
   - Click "Copy ID"
   - You'll need:
     * Role Activity Log Channel ID
     * Audit Log Channel ID

## Features

- Role management
- Voice channel controls
- Ticket system
- Welcome messages
- Security features
- Leveling system
- Auto-moderation

## Development

To work on the bot's code:

1. Connect to the server:
```bash
ssh root@45.76.83.149
```

2. Start development servers:
```bash
./dev.sh
```

This will:
- Start the FastAPI backend server (http://45.76.83.149:8000)
- Start the React frontend server (http://45.76.83.149)
- Watch for changes and reload automatically

3. Access the API documentation:
- OpenAPI docs: http://45.76.83.149:8000/docs
- ReDoc: http://45.76.83.149:8000/redoc

## Troubleshooting

If you encounter issues:

1. Check the bot's status:
```bash
./start.sh status
```

2. View error messages:
```bash
screen -r arablife
```

3. Common Issues:
   - Invalid Token: Reset token in Discord Developer Portal
   - Wrong IDs: Double-check all IDs in .env file
   - Missing Permissions: Ensure bot role is above managed roles
   - Connection Issues: Check server internet connection

4. Still Having Issues:
   - Check bot console for specific error messages
   - Verify all IDs in .env file
   - Ensure bot has required permissions
   - Verify all dependencies installed correctly

## Security Notes

- Keep your bot token secret
- Never share your .env file
- Reset token if accidentally exposed
- Regularly check bot permissions
- Monitor audit logs for unusual activity
