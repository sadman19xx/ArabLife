# ArabLife Bot - Quick Setup Guide for bot-hosting.net

## Features

1. Application System
   - Application approval/denial with visa images
   - Role assignment system
   - Staff permissions management

2. Welcome System
   - Custom welcome sounds
   - Welcome messages
   - `/testwelcome` command

3. Role Management
   - Role assignment commands
   - Role hierarchy management
   - Role-based permissions

4. Voice System
   - Voice channel management
   - Voice activity tracking
   - Robust connection handling

5. Status Commands
   - Server status monitoring
   - Bot health checks
   - System metrics

6. Announcement System
   - Server announcements
   - Automated notifications
   - Message management

## Quick Installation

### 1. Required Files
Upload these files to your bot hosting:
```
bot.py
config.py
requirements.txt
validate_env.py
welcome.mp3
cogs/
utils/
fonts/arabic.ttf
assets/accept.png
assets/reject.png
```

### 2. Environment Variables
Add to bot-hosting.net control panel:
```env
# Bot Configuration
TOKEN=your_discord_bot_token
GUILD_ID=your_guild_id
APPLICATION_ID=your_application_id

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

### 3. Bot Configuration
1. Set Python version to 3.8 or higher
2. Set startup command to: `python3 bot.py`
3. Enable required intents in Discord Developer Portal:
   - Server Members Intent (for welcome system)
   - Voice State Intent (for voice features)

### 4. Start the Bot
Click "Start" in the control panel

## Troubleshooting

### Installation Issues
- Verify all files are uploaded
- Check Python version (3.8+)
- Ensure requirements.txt is present

### Configuration Issues
- Verify TOKEN is correct
- Check all IDs are valid numbers
- Ensure all required files exist

### Runtime Issues
- Check bot logs for errors
- Verify bot permissions
- Ensure intents are enabled

### Common Problems

1. Bot Won't Start
   - Check TOKEN
   - Verify Python version
   - Check startup logs

2. Commands Don't Work
   - Verify GUILD_ID
   - Check role permissions
   - Ensure command registration

3. Welcome System Issues
   - Check WELCOME_VOICE_CHANNEL_ID
   - Verify welcome.mp3 exists
   - Check voice permissions

4. Application System Issues
   - Verify role IDs
   - Check channel permissions
   - Ensure visa images exist

## Support Tips

1. Always check logs first
2. Verify all IDs are correct
3. Ensure files are in correct locations
4. Never share your bot token
5. Keep Python packages updated

For detailed setup:
- See full README.md
- Check BOT_SETUP_GUIDE.md
- Review error logs
