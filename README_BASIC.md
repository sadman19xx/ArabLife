# ArabLife Bot - Quick Setup Guide for bot-hosting.net

## Features

1. Application System
   - Application approval/denial with visa images
   - Role assignment system
   - Staff permissions management

2. Welcome System
   - Custom welcome sounds
   - Welcome messages
   - Custom welcome images

3. Role & Security
   - Role management
   - Anti-spam protection
   - Audit logging

4. Voice & Leveling
   - Voice channel management
   - Experience tracking
   - Level-based roles

5. FiveM Integration
   - Server status
   - Player management
   - Server info display

6. Support Features
   - Ticket system
   - Custom commands
   - AutoMod protection

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
RESPONSE_CHANNEL_ID=response_channel_id
AUDIT_LOG_CHANNEL_ID=audit_log_id
ROLE_ACTIVITY_LOG_CHANNEL_ID=role_log_id

# Role IDs
STAFF_ROLE_ID=staff_role_id
CITIZEN_ROLE_ID=citizen_role_id
ROLE_ID_TO_GIVE=default_role_id
ROLE_IDS_ALLOWED=mod_role_ids

# FiveM Settings
FIVEM_SERVER_IP=your_server_ip
FIVEM_SERVER_PORT=your_server_port

# File Paths
WELCOME_SOUND_PATH=welcome.mp3
FFMPEG_PATH=/usr/bin/ffmpeg
```

### 3. Bot Configuration
1. Set Python version to 3.8 or higher
2. Set startup command to: `python3 bot.py`
3. Enable required intents in Discord Developer Portal:
   - Presence Intent
   - Server Members Intent
   - Message Content Intent

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
