# ArabLife Discord Bot

A custom Discord bot based on MEE6 functionality, with enhanced features and Arabic language support.

## Features

- **Advanced AutoMod**
  - Customizable word/domain filters with wildcard support
  - Message similarity detection for spam prevention
  - Role and channel exemptions
  - Configurable mute durations
  - Raid protection

- **Leveling System**
  - Channel-specific XP rates
  - Role-based XP multipliers
  - Customizable role rewards
  - Visual progress tracking
  - Detailed rank cards

- **Custom Commands**
  - Admin management interface
  - Permission controls
  - Command usage tracking

- **Welcome System**
  - Customizable welcome messages
  - Welcome images with user avatars
  - Role assignment

- **Ticket System**
  - Department-based routing
  - Staff management
  - Ticket logging

## Requirements

### Bot Requirements
- Python 3.8 or higher
- FFmpeg (for voice features)
- Ubuntu Server 20.04 or higher

### Dashboard Requirements
- Node.js 18 or higher
- Nginx
- Domain name for dashboard access
- SSL certificate (recommended)

## Step-by-Step Installation

### 1. System Preparation

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install required system packages
sudo apt install -y python3 python3-pip python3-venv ffmpeg nginx certbot python3-certbot-nginx

# Install Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Verify installations
python3 --version
node --version
npm --version
nginx -v
```

### 2. Bot Installation

```bash
# Clone repository
git clone https://github.com/yourusername/arablife-bot.git
cd arablife-bot

# Make scripts executable
chmod +x setup.sh run.sh dev.sh
chmod +x dashboard/setup.sh

# Run bot setup
./setup.sh

# Copy and edit environment file
cp .env.example .env
nano .env
```

### Getting Your Bot Token

Before configuring the bot, you need to create a Discord application and get your bot token:

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" section in the left sidebar
4. Click "Add Bot" or "Reset Token"
5. Click "Copy" to copy your bot token
   - ⚠️ Keep this token secret! Never share it or commit it to git
   - The token should look like: `MTIzNDU2Nzg5MDEyMzQ1Njc4.ABCDEF.ghijklmnopqrstuvwxyz123456`

### Bot Permissions Setup

1. Go to the "OAuth2" section in the left sidebar
2. In "Scopes", select "bot" and "applications.commands"
3. In "Bot Permissions", select:
   - Manage Roles
   - Manage Channels
   - Kick Members
   - Ban Members
   - Manage Messages
   - Embed Links
   - Attach Files
   - Read Message History
   - Add Reactions
   - Connect
   - Speak
4. Copy the generated URL and open it in a browser to add the bot to your server

### Configure Environment

Configure your `.env` file with:
```env
# Required: Your bot token from Discord Developer Portal
TOKEN=MTIzNDU2Nzg5MDEyMzQ1Njc4.ABCDEF.ghijklmnopqrstuvwxyz123456

# Required: Your Discord server (guild) ID
GUILD_ID=123456789  # Right-click server name -> Copy ID

# Required: Role IDs (Enable Developer Mode to get these)
ROLE_IDS_ALLOWED=123456789,987654321  # Admin/mod role IDs
ROLE_ID_TO_GIVE=123456789  # Auto-assign role ID
ROLE_ID_REMOVE_ALLOWED=123456789  # Role that can remove others
```

⚠️ **Important**: All role and channel IDs must be actual Discord IDs (numbers), not placeholder text. To get IDs:
1. Enable Developer Mode in Discord (User Settings > App Settings > Advanced > Developer Mode)
2. Right-click on a role/channel and select "Copy ID"
3. Replace the example IDs in .env with your actual Discord IDs

Example of correct values:
```env
ROLE_ID_TO_GIVE=123456789
PLAYER_REPORT_ROLE_ID=987654321
```

Example of incorrect values that will cause errors:
```env
ROLE_ID_TO_GIVE=role_id
PLAYER_REPORT_ROLE_ID=role_id
```

### 3. Dashboard Installation

```bash
# Navigate to dashboard directory
cd dashboard

# Run dashboard setup
./setup.sh

# Configure frontend environment
cd frontend
cp .env.example .env
nano .env

# Configure backend environment
cd ../backend
cp .env.example .env
nano .env
```

Configure frontend `.env`:
```env
REACT_APP_API_URL=https://your-domain/api
REACT_APP_DISCORD_CLIENT_ID=your_client_id
REACT_APP_DISCORD_REDIRECT_URI=https://your-domain/callback
```

Configure backend `.env`:
```env
DATABASE_URL=sqlite:///./dashboard.db
DISCORD_CLIENT_ID=your_client_id
DISCORD_CLIENT_SECRET=your_client_secret
DISCORD_REDIRECT_URI=https://your-domain/callback
JWT_SECRET=your_secure_secret
```

### 4. SSL Setup

```bash
# Install SSL certificate
sudo certbot --nginx -d your-domain.com

# Test renewal
sudo certbot renew --dry-run
```

### 5. Start Services

```bash
# Start bot service
sudo systemctl start arablife-bot
sudo systemctl enable arablife-bot

# Start dashboard API
sudo systemctl start arablife-dashboard-api
sudo systemctl enable arablife-dashboard-api

# Start/reload nginx
sudo systemctl reload nginx
```

### 6. Verify Installation

```bash
# Check bot status
sudo systemctl status arablife-bot

# Check API status
sudo systemctl status arablife-dashboard-api

# Check nginx status
sudo systemctl status nginx

# View logs
sudo journalctl -u arablife-bot -f
sudo journalctl -u arablife-dashboard-api -f
```

## Development Mode

### Bot Development
```bash
# Run bot with auto-reload
./dev.sh
```

### Dashboard Development
```bash
# Run backend API
cd dashboard/backend
source venv/bin/activate
uvicorn app.main:app --reload

# Run frontend
cd dashboard/frontend
npm start
```

## Commands

### AutoMod Commands
- `/automod_toggle` - Enable/disable AutoMod
- `/automod_action` - Set action for violations
- `/automod_exempt` - Add/remove role or channel exemptions
- `/automod_word` - Manage banned words/phrases
- `/automod_link` - Manage banned domains
- `/automod_spam` - Configure spam detection
- `/automod_raid` - Configure raid protection
- `/automod_status` - View current settings

### Leveling Commands
- `/rank` - Check your or another user's rank
- `/leaderboard` - Show server leaderboard
- `/setxp` - Set a user's XP (Admin)
- `/setmultiplier` - Set XP multiplier for role/channel

### Custom Commands
- `/addcommand` - Add a custom command
- `/editcommand` - Edit existing command
- `/removecommand` - Remove a command
- `/listcommands` - List all custom commands
- `/commandinfo` - Get command details

### Welcome Commands
- `/setwelcomechannel` - Set welcome message channel
- `/setwelcomebackground` - Set welcome image background
- `/testwelcome` - Test welcome message

## Troubleshooting

### Common Issues

1. "Improper token has been passed" error:
   - Your bot token is invalid or malformed
   - Get a new token from Discord Developer Portal -> Bot section
   - Token should be ~70 characters long with letters, numbers, and dots
   - Never use placeholder text like "your_bot_token"

2. "Invalid literal for int()" error:
   - You have placeholder text instead of actual Discord IDs
   - All role and channel IDs must be numbers (e.g., 123456789)
   - Enable Developer Mode in Discord to get IDs:
     1. User Settings -> App Settings -> Advanced
     2. Turn on Developer Mode
     3. Right-click roles/channels -> Copy ID

3. Other startup issues:
   - Run `python3 validate_env.py` to check your configuration
   - Verify .env matches the format in .env.example
   - Check Python virtual environment
   - Ensure all required packages are installed
   - Check logs: `sudo journalctl -u arablife-bot -f`

2. Dashboard API issues:
   - Check logs: `sudo journalctl -u arablife-dashboard-api -f`
   - Verify database connection
   - Check Discord OAuth2 settings

3. Frontend not loading:
   - Check nginx error logs: `sudo tail -f /var/log/nginx/error.log`
   - Verify API URL in frontend .env
   - Check SSL certificate status

4. Permission issues:
   - Check file permissions in project directory
   - Verify systemd service user permissions
   - Check nginx worker permissions

## Support

For support:
1. Check the troubleshooting section above
2. Join our Discord server
3. Open an issue on GitHub
4. Check the logs for detailed error messages

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request
