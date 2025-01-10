# ArabLife Discord Bot

A Discord bot for managing roles, voice channels, tickets, and more.

## Quick Setup

1. Make scripts executable:
```bash
chmod +x *.sh dashboard/frontend/setup-frontend.sh
```

2. Copy requirements to backend directory:
```bash
./copy-requirements.sh
```

3. Run server setup:
```bash
sudo ./setup-server.sh
```

4. Start the dashboard:
```bash
./dev.sh
```

The dashboard will be available at:
- Web Interface: http://45.76.83.149
- API Documentation: http://45.76.83.149/docs

## Detailed Setup Steps

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

### 3. Server Setup

The setup process will:
1. Install system dependencies (Python, Node.js, nginx)
2. Configure nginx as a reverse proxy
3. Set up Python virtual environment
4. Install Python dependencies
5. Set up frontend development environment
6. Configure permissions

### 4. Running the Bot

Start everything with one command:
```bash
./dev.sh
```

This will:
- Start the FastAPI backend server
- Start the React frontend server
- Configure nginx routing
- Set up all required services

## Features

- Role management
- Voice channel controls
- Ticket system
- Welcome messages
- Security features
- Leveling system
- Auto-moderation

## Development

The development environment includes:

1. Backend (FastAPI):
- Running on port 8000
- Auto-reload enabled
- API documentation at /docs

2. Frontend (React):
- Running on port 80 (through nginx)
- Hot reload enabled
- Material-UI components

3. Nginx Configuration:
- Reverse proxy for both services
- Proper header forwarding
- WebSocket support

## Troubleshooting

If you encounter issues:

1. Check services status:
```bash
sudo systemctl status nginx  # Check nginx
./start.sh status          # Check bot status
```

2. View logs:
```bash
# Nginx logs
sudo tail -f /var/log/nginx/error.log

# Bot logs
screen -r arablife

# Backend logs
cd dashboard/backend
source venv/bin/activate
python3 -m uvicorn app.main:app --reload

# Frontend logs
cd dashboard/frontend
npm start
```

3. Common Issues:
   - Port 80 in use: Check nginx configuration
   - Missing dependencies: Run setup-server.sh again
   - Virtual environment issues: Delete venv directory and rerun setup
   - Permission issues: Check file ownership and permissions

4. Reset Setup:
```bash
# Stop all services
./start.sh stop
sudo systemctl stop nginx

# Clean up
rm -rf dashboard/backend/venv
rm -rf dashboard/frontend/node_modules

# Restart setup
./copy-requirements.sh
sudo ./setup-server.sh
./dev.sh
```

## Security Notes

- Keep your bot token secret
- Never share your .env file
- Reset token if accidentally exposed
- Regularly check bot permissions
- Monitor audit logs for unusual activity
- Keep the server updated
- Use strong SSH keys for server access
