# ArabLife Bot - Detailed Setup Guide

This guide provides comprehensive instructions for setting up the ArabLife Discord bot on your own server.

## Prerequisites

1. System Requirements
   - Ubuntu/Debian Linux system
   - Python 3.8 or higher
   - Internet connection
   - Sudo privileges

2. Discord Requirements
   - Discord account
   - Server with admin permissions
   - Bot token from Discord Developer Portal

## Step 1: Discord Application Setup

1. Create Application
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Click "New Application"
   - Name your application "ArabLife Bot" (or your preferred name)

2. Bot Setup
   - Go to the "Bot" section
   - Click "Add Bot"
   - Save the token (you'll need this later)

3. Enable Required Intents
   - Presence Intent
   - Server Members Intent
   - Message Content Intent

4. Invite Bot to Server
   - Go to OAuth2 > URL Generator
   - Select scopes: `bot`, `applications.commands`
   - Select required permissions:
     - Manage Roles
     - Manage Channels
     - Send Messages
     - Connect
     - Speak
     - Use Voice Activity
   - Copy and use the generated URL

## Step 2: Installation

1. Clone Repository
```bash
git clone [repository-url]
cd ArabLife
```

2. Run Installation Script
```bash
sudo chmod +x install.sh
sudo ./install.sh
```

The installation script will:
- Install system dependencies
- Set up Python environment
- Install required packages
- Create configuration files
- Set up directories
- Configure permissions

## Step 3: Configuration

1. Environment Setup
   - The install script creates `.env` from `.env.example`
   - Edit `.env` with your settings:
```env
# Bot Configuration
TOKEN=your_bot_token
GUILD_ID=your_server_id
APPLICATION_ID=your_bot_application_id

# Channel IDs
WELCOME_VOICE_CHANNEL_ID=voice_channel_id
RESPONSE_CHANNEL_ID=response_channel_id
AUDIT_LOG_CHANNEL_ID=audit_log_id
ROLE_ACTIVITY_LOG_CHANNEL_ID=role_log_id

# Role IDs
STAFF_ROLE_ID=staff_role_id
CITIZEN_ROLE_ID=citizen_role_id
ROLE_ID_TO_GIVE=default_role_id
ROLE_IDS_ALLOWED=mod_role_ids

# FiveM Settings (if using FiveM integration)
FIVEM_SERVER_IP=your_server_ip
FIVEM_SERVER_PORT=your_server_port
```

2. Required Files
   - Place welcome.mp3 in the bot directory
   - Add visa images to assets/
     - assets/accept.png
     - assets/reject.png
   - Verify fonts/arabic.ttf exists

3. Validate Configuration
```bash
python3 validate_env.py
```

## Step 4: Running the Bot

1. Start the Bot
```bash
./run.sh
```

2. Verify Operation
   - Check bot comes online in Discord
   - Test basic commands
   - Verify welcome system
   - Check role assignments

## Step 5: System Service Setup (Optional)

1. Copy Service File
```bash
sudo cp arablife-bot.service /etc/systemd/system/
```

2. Edit Service File
```bash
sudo nano /etc/systemd/system/arablife-bot.service
```
Update paths in the service file to match your installation.

3. Enable and Start Service
```bash
sudo systemctl enable arablife-bot
sudo systemctl start arablife-bot
```

4. Check Status
```bash
sudo systemctl status arablife-bot
```

## Feature Configuration

### 1. Application System
- Set up application channels
- Configure role permissions
- Test approval/denial process

### 2. Welcome System
- Configure welcome channel
- Test welcome sound
- Verify image generation

### 3. Role Management
- Set up role hierarchy
- Configure auto-roles
- Test role commands

### 4. Security Features
- Configure audit logging
- Set up anti-spam
- Test verification system

### 5. Voice System
- Set up voice channels
- Configure permissions
- Test dynamic creation

### 6. FiveM Integration
- Configure server connection
- Test status commands
- Verify player tracking

## Troubleshooting

### Common Issues

1. Bot Won't Start
   - Check logs in logs/
   - Verify TOKEN is correct
   - Ensure Python version compatibility
   - Check file permissions

2. Permission Errors
   - Verify bot role position
   - Check channel permissions
   - Verify role hierarchy

3. Feature Issues
   - Check specific feature logs
   - Verify required channels exist
   - Test with admin permissions

### Maintenance

1. Regular Tasks
   - Monitor log files
   - Update dependencies
   - Backup configuration
   - Check disk space

2. Updates
   - Pull latest changes
   - Run install script
   - Check for breaking changes
   - Test all features

## Security Best Practices

1. Token Security
   - Never share your bot token
   - Rotate token if compromised
   - Use environment variables

2. Permission Management
   - Use minimal permissions
   - Regular audit of roles
   - Monitor bot activities

3. System Security
   - Keep system updated
   - Monitor logs
   - Regular backups
   - Secure file permissions

## Support Resources

- Check README.md for overview
- Review logs for errors
- Join support server
- Check GitHub issues
