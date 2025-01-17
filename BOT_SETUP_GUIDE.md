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
   - Server Members Intent (for welcome system)
   - Voice State Intent (for voice features)

4. Invite Bot to Server
   - Go to OAuth2 > URL Generator
   - Select scopes: `bot`, `applications.commands`
   - Select required permissions:
     - Manage Roles
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
AUDIT_LOG_CHANNEL_ID=audit_log_id
ROLE_ACTIVITY_LOG_CHANNEL_ID=role_log_id

# Role IDs
ROLE_ID_TO_GIVE=default_role_id
ROLE_IDS_ALLOWED=mod_role_ids

# Voice Settings
WELCOME_SOUND_PATH=welcome.mp3
WELCOME_SOUND_VOLUME=0.5
FFMPEG_PATH=/usr/bin/ffmpeg
DEFAULT_VOLUME=0.5
VOICE_TIMEOUT=20
MAX_RECONNECT_ATTEMPTS=10
RECONNECT_DELAY=1
MAX_RECONNECT_DELAY=30

# Logging Settings
LOG_LEVEL=INFO
LOG_TO_FILE=false
LOG_DIR=logs
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
   - Test slash commands
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
- Test `/accept` and `/reject` commands

### 2. Welcome System
- Configure welcome channel
- Test `/testwelcome` command
- Verify welcome sound plays

### 3. Role Management
- Set up role hierarchy
- Configure role permissions
- Test role commands

### 4. Voice System

1. Voice Channel Setup
   - Create a dedicated welcome voice channel
   - Get the channel ID (Right-click > Copy ID)
   - Set WELCOME_VOICE_CHANNEL_ID in .env
   - Ensure bot has these permissions in the channel:
     * View Channel
     * Connect
     * Speak
     * Use Voice Activity
     * Priority Speaker (recommended)

2. Welcome Sound Setup
   - Place welcome.mp3 in bot directory
   - Verify file permissions: `chmod 644 welcome.mp3`
   - Test file: `ffplay welcome.mp3`
   - Configure volume in .env:
     ```env
     WELCOME_SOUND_VOLUME=0.5    # 0.1 to 2.0
     DEFAULT_VOLUME=0.5          # Default playback volume
     ```

3. FFmpeg Configuration
   - Verify FFmpeg installation: `ffmpeg -version`
   - Set path in .env: `FFMPEG_PATH=/usr/bin/ffmpeg`
   - Test FFmpeg permissions:
     ```bash
     sudo -u your-bot-user ffmpeg -version
     ```

4. Connection Settings
   - Configure timeouts and reconnection:
     ```env
     VOICE_TIMEOUT=20              # Connection timeout
     MAX_RECONNECT_ATTEMPTS=10     # Max retry attempts
     RECONNECT_DELAY=1            # Initial retry delay
     MAX_RECONNECT_DELAY=30       # Maximum retry delay
     ```

5. Testing Voice System
   - Start bot and verify it joins voice channel
   - Test welcome sound:
     * Join the welcome channel
     * Sound should play automatically
   - Test reconnection:
     * Use !rejoin command
     * Watch logs for connection status

### 5. Status Commands
- Test bot health checks
- Monitor system metrics
- Verify status reporting

### 6. Announcement System
- Configure announcement channels
- Test announcement commands
- Verify message management

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

3. Voice Issues

   a. Connection Problems
      - Verify bot permissions in server and channel
      - Check if bot is server deafened (Server Settings > Members)
      - Verify voice channel ID is correct
      - Monitor connection logs: `tail -f logs/discord.log`
      - Try manual reconnection with !rejoin
      - Check if multiple bots are trying to use same channel

   b. Audio Problems
      - Verify FFmpeg installation and permissions
      - Check welcome.mp3 file:
        ```bash
        file welcome.mp3          # Verify file type
        ffmpeg -i welcome.mp3     # Check audio details
        ```
      - Test different volume levels
      - Check system audio configuration
      - Verify bot isn't muted in Discord

   c. Performance Issues
      - Monitor system resources
      - Check network connectivity
      - Verify voice channel region
      - Monitor reconnection attempts in logs
      - Adjust timeout and retry settings

   d. Common Error Solutions
      - "FFmpeg not found": Install/reinstall FFmpeg
      - "Permission denied": Check file and directory permissions
      - "Already connected": Force disconnect and reconnect
      - "Connection timeout": Check network and increase timeout
      - "Voice websocket closed": Use !rejoin command

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
- Check GitHub issues
