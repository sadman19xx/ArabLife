# ArabLife Discord Bot

A Discord bot for managing roles, voice channels, tickets, and more.

## Step-by-Step Setup Guide

### 1. Create Discord Bot Application

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
   - Name your application (e.g., "ArabLife")
   - Click "Create"
3. Go to "Bot" section in left sidebar
   - Click "Add Bot"
   - Click "Yes, do it!"
4. Under the bot's username:
   - Click "Copy" to copy your bot token (or "Reset Token" if needed)
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

### 3. Server Installation

1. Connect to your server via SSH

2. Clone the repository:
```bash
git clone https://github.com/your-username/ArabLife.git
cd ArabLife
```

3. Make scripts executable:
```bash
chmod +x install.sh start.sh
```

4. Run installation script:
```bash
sudo ./install.sh
```

5. During installation, you'll be prompted for:
   - Discord Bot Token (from step 1)
   - Server ID (from step 2)
   - Role IDs (from step 2)
   - Channel IDs (from step 2)

### 4. Verify Installation

Before running the bot, verify everything is set up correctly:
```bash
chmod +x verify.sh
./verify.sh
```

This will check:
- System dependencies
- Python environment
- Configuration files
- Required bot files
- Cog files
- Bot status

Fix any issues reported by the verification script.

### 5. Running the Bot

After verification passes, start the bot:
```bash
./start.sh start
```

Other commands:
```bash
./start.sh stop     # Stop the bot
./start.sh restart  # Restart the bot
./start.sh status   # Check bot status
```

View bot console:
1. Type: `screen -r arablife`
2. To detach from console: Press `Ctrl+A` then `D`

## Features

- Role management
- Voice channel controls
- Ticket system
- Welcome messages
- Security features
- Leveling system
- Auto-moderation

## Troubleshooting

If the bot isn't working:

1. Check Bot Status:
```bash
./start.sh status
```

2. View Error Messages:
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
