# ArabLife Bot - Quick Setup Guide for bot-hosting.net

## Quick Installation

### 1. Upload Files
Zip and upload these files to your bot hosting:
- All files in the main directory (bot.py, config.py)
- All files in the `cogs` folder
- All files in the `utils` folder
- The `fonts` folder with arabic.ttf
- The `assets` folder with visa images (accept.png, reject.png)

### 2. Set Required Environment Variables
In the bot-hosting.net control panel, add these variables:
```
# Bot Configuration
TOKEN=your_discord_bot_token
GUILD_ID=your_guild_id
APPLICATION_ID=your_application_id

# Welcome Voice Settings
WELCOME_VOICE_CHANNEL_ID=your_voice_channel_id
WELCOME_SOUND_PATH=welcome.mp3

# Application System Role IDs
STAFF_ROLE_ID=1287486561914589346
CITIZEN_ROLE_ID=1309555494586683474

# Application System Channel ID
RESPONSE_CHANNEL_ID=1309556312027430922
```

### 3. Set Python Version
Set Python version to 3.8 or higher

### 4. Set Startup Command
Set to: `python bot.py`

### 5. Start the Bot
Click the Start button in the control panel

### Common Issues
1. Bot won't start:
   - Check if TOKEN is correct
   - Make sure all files are uploaded
   - Verify Python version is 3.8+

2. Commands don't work:
   - Check if GUILD_ID is correct
   - Verify role IDs are correct
   - Make sure channel IDs are correct

3. Welcome sound doesn't play:
   - Verify WELCOME_VOICE_CHANNEL_ID is correct
   - Check if welcome.mp3 is uploaded
   - Make sure the bot has voice permissions

4. Application commands don't work:
   - Verify STAFF_ROLE_ID and CITIZEN_ROLE_ID are correct
   - Check if RESPONSE_CHANNEL_ID is correct
   - Ensure visa images are in the assets folder

### Features
1. Application Approval/Denial System
   - `/accept @User` - Accepts a user's application
   - `/reject @User [reason]` - Rejects a user's application
   - Automated responses with visa images
   - Role-based staff permissions

2. Welcome Voice System
   - Plays welcome sound for new members
   - Auto-disconnects after playing

### Need More Help?
- Check the full README.md for detailed setup
- Contact support with specific error messages
- Never share your bot token
