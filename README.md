# ArabLife Discord Bot

A Discord bot for managing roles, voice channels, tickets, and more.

## Server Setup

Before installing the bot, you need to set up the server:

1. Connect to the server:
```bash
ssh root@45.76.83.149
```

2. Clone the repository:
```bash
git clone https://github.com/your-username/ArabLife.git
cd ArabLife
```

3. Make scripts executable:
```bash
chmod +x setup-server.sh install.sh start.sh dev.sh dashboard/frontend/setup-frontend.sh
```

4. Run the server setup script:
```bash
sudo ./setup-server.sh
```
This will:
- Install system dependencies (Python, Node.js, nginx, etc.)
- Configure nginx as a reverse proxy
- Set up proper port forwarding

## Installation Methods

After setting up the server, you can install and manage the bot in two ways:

### Method 1: Web Dashboard (Recommended)

1. Start the development servers:
```bash
./dev.sh
```

2. Access the dashboard:
```
http://45.76.83.149
```

The web interface provides:
- Easy bot installation and configuration
- Real-time bot status monitoring
- Start/stop controls
- Live log viewer

3. Navigate to "Bot Installation" in the sidebar
4. Fill in the required information:
   - Bot Token (see "Getting Required Information" below)
   - Server ID
   - Role IDs
   - Channel IDs
5. Click "Install Bot" to set up the bot
6. Use the control panel to start/stop the bot and view logs

### Method 2: Command Line

If you prefer using the command line:

1. Run the installation script:
```bash
sudo ./install.sh
```

2. During installation, you'll be prompted for:
   - Discord Bot Token
   - Server ID
   - Role IDs
   - Channel IDs

3. After installation, use these commands to manage the bot:
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

1. Start development servers:
```bash
./dev.sh
```

This will:
- Start the FastAPI backend server (http://45.76.83.149:8000)
- Start the React frontend server (http://45.76.83.149)
- Watch for changes and reload automatically

2. Access the API documentation:
- OpenAPI docs: http://45.76.83.149:8000/docs
- ReDoc: http://45.76.83.149:8000/redoc

## Troubleshooting

If you encounter issues:

1. Check the server setup:
```bash
sudo nginx -t              # Test nginx configuration
sudo systemctl status nginx # Check nginx status
```

2. Check the bot's status:
```bash
./start.sh status
```

3. View bot logs:
```bash
screen -r arablife
```

4. View development server logs:
```bash
# Frontend logs
cd dashboard/frontend
npm run start

# Backend logs
cd dashboard/backend
uvicorn app.main:app --reload
```

5. Common Issues:
   - Invalid Token: Reset token in Discord Developer Portal
   - Wrong IDs: Double-check all IDs in .env file
   - Missing Permissions: Ensure bot role is above managed roles
   - Connection Issues: Check server internet connection
   - Port Issues: Make sure ports 80, 3000, and 8000 are not in use
   - Nginx Issues: Check /var/log/nginx/error.log

6. Still Having Issues:
   - Check bot console for specific error messages
   - Verify all IDs in .env file
   - Ensure bot has required permissions
   - Verify all dependencies installed correctly
   - Check nginx configuration in /etc/nginx/sites-available/arablife

## Security Notes

- Keep your bot token secret
- Never share your .env file
- Reset token if accidentally exposed
- Regularly check bot permissions
- Monitor audit logs for unusual activity
- Keep the server updated with security patches
- Use strong SSH keys for server access
