# ArabLife Bot Installation Guide

## Installation on bot-hosting.net

### 1. Required Files
Upload the following files and directories to your bot hosting:
```
├── bot.py
├── config.py
├── requirements.txt
├── cogs/
│   ├── automod_commands.py
│   ├── help_commands.py
│   ├── leveling_commands.py
│   ├── role_commands.py
│   ├── security_commands.py
│   ├── status_commands.py
│   ├── ticket_commands.py
│   ├── voice_commands.py
│   └── welcome_commands.py
├── utils/
│   └── logger.py
├── data/
└── fonts/
    └── arabic.ttf
```

### 2. Create requirements.txt
Create a `requirements.txt` file with these dependencies:
```
discord.py==2.3.2
python-dotenv==1.0.0
aiosqlite==0.19.0
```

### 3. Environment Variables
In the bot-hosting.net control panel, set up these environment variables:

Required Variables:
```
TOKEN=your_discord_bot_token
GUILD_ID=your_guild_id
ROLE_IDS_ALLOWED=comma,separated,role,ids
ROLE_ID_TO_GIVE=role_id
ROLE_ID_REMOVE_ALLOWED=role_id
ROLE_ACTIVITY_LOG_CHANNEL_ID=channel_id
AUDIT_LOG_CHANNEL_ID=channel_id
```

Optional Variables (with defaults):
```
# Welcome Settings
WELCOME_CHANNEL_ID=0
WELCOME_BACKGROUND_URL=https://i.imgur.com/your_background.png
WELCOME_MESSAGE=Welcome {user} to {server}! 🎉
GOODBYE_MESSAGE=Goodbye {user}, we hope to see you again! 👋
WELCOME_EMBED_COLOR=0x2ecc71
WELCOME_EMBED_TITLE=Welcome to {server}!
WELCOME_EMBED_DESCRIPTION=Welcome {user} to our community!\n\nMember Count: {member_count}

# Voice Settings
WELCOME_SOUND_PATH=welcome.mp3
DEFAULT_VOLUME=0.5

# Command Cooldowns
ROLE_COMMAND_COOLDOWN=5
STATUS_COMMAND_COOLDOWN=10
SOUND_COMMAND_COOLDOWN=5

# Security Settings
MAX_STATUS_LENGTH=100
BLACKLISTED_WORDS=word1,word2,word3
MAX_MENTIONS=5
RAID_PROTECTION=true
MIN_ACCOUNT_AGE=7
ALLOWED_DOMAINS=discord.com,discord.gg
SPAM_DETECTION=true
AUTO_TIMEOUT_DURATION=3600

# AutoMod Settings
AUTOMOD_ENABLED=true
AUTOMOD_SPAM_THRESHOLD=5
AUTOMOD_SPAM_INTERVAL=5
AUTOMOD_RAID_THRESHOLD=10
AUTOMOD_RAID_INTERVAL=30
AUTOMOD_ACTION=warn

# Leveling Settings
LEVELING_ENABLED=true
XP_PER_MESSAGE=15
XP_COOLDOWN=60
LEVEL_UP_MESSAGE=Congratulations {user}! You reached level {level}!
ROLE_REWARDS=[]

# Ticket Settings
TICKET_STAFF_ROLE_ID=0
TICKET_CATEGORY_ID=0
TICKET_LOG_CHANNEL_ID=0

# Department Role IDs
PLAYER_REPORT_ROLE_ID=0
HEALTH_DEPT_ROLE_ID=0
INTERIOR_DEPT_ROLE_ID=0
FEEDBACK_ROLE_ID=0
```

### 4. Python Version
Set Python version to 3.10 or higher in the bot-hosting.net control panel.

### 5. Startup Command
Set the startup command to:
```bash
python bot.py
```

### 6. File Permissions
Make sure all files have the correct permissions:
```bash
chmod +x bot.py
chmod -R 755 cogs/
chmod -R 755 utils/
chmod -R 777 data/
```

### 7. Database Setup
The bot will automatically create the required database files in the `data/` directory on first run.

### 8. Starting the Bot
1. Upload all files to your bot hosting
2. Set all environment variables
3. Set Python version to 3.10+
4. Set startup command
5. Start the bot from the control panel

### 9. Verifying Installation
After starting the bot:
1. Check the console logs for any errors
2. Verify the bot comes online in your Discord server
3. Test basic commands like `/help`
4. Check if the database files are created in the `data/` directory

### 10. Troubleshooting
If you encounter issues:
1. Check the console logs for error messages
2. Verify all required environment variables are set
3. Ensure all required files are uploaded
4. Check file permissions
5. Verify Python version is 3.10 or higher

### 11. Dashboard Setup (Optional)
The dashboard requires additional setup and a separate hosting service. Contact support if you need help setting up the dashboard.

### 12. Support
If you need help:
1. Check the error logs in the bot-hosting.net control panel
2. Review the configuration in the control panel
3. Contact support with specific error messages

### Security Note
Never share your bot token or sensitive environment variables. Keep your `.env` file secure and never commit it to version control.
