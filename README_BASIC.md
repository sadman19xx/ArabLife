# ArabLife Bot - Quick Setup Guide

## Quick Installation on bot-hosting.net

### 1. Upload Files
Zip and upload these files to your bot hosting:
- All files in the main directory (bot.py, config.py)
- All files in the `cogs` folder
- All files in the `utils` folder
- The `fonts` folder with arabic.ttf

### 2. Set Required Environment Variables
In the bot-hosting.net control panel, add these variables:
```
TOKEN=your_discord_bot_token
GUILD_ID=your_guild_id
ROLE_IDS_ALLOWED=role_id1,role_id2
ROLE_ID_TO_GIVE=role_id
ROLE_ID_REMOVE_ALLOWED=role_id
ROLE_ACTIVITY_LOG_CHANNEL_ID=channel_id
AUDIT_LOG_CHANNEL_ID=channel_id
```

### 3. Set Python Version
Set Python version to 3.10 or higher

### 4. Set Startup Command
Set to: `python bot.py`

### 5. Start the Bot
Click the Start button in the control panel

### Common Issues
1. Bot won't start:
   - Check if TOKEN is correct
   - Make sure all files are uploaded
   - Verify Python version is 3.10+

2. Commands don't work:
   - Check if GUILD_ID is correct
   - Verify role IDs are correct
   - Make sure channel IDs are correct

3. Database errors:
   - Create a `data` folder if it doesn't exist
   - Make sure the bot has write permissions

### Need More Help?
- Check the full README.md for detailed instructions
- Contact support with specific error messages
- Make sure to never share your bot token

### Features
- AutoMod (spam, raid protection)
- Leveling system with rewards
- Welcome messages
- Voice commands
- Ticket system
- Role management
- Custom commands

### Optional Settings
See the full README.md for optional settings like:
- Welcome messages
- Voice settings
- AutoMod configuration
- Leveling system settings
- Ticket system setup
