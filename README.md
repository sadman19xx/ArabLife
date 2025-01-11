# ArabLife Discord Bot

A custom Discord bot based on MEE6 with specialized features for Arabic communities.

## Features

- **Welcome System**
  - Custom welcome images with Arabic text support
  - Welcome sound effects in voice channels
  - Configurable welcome/goodbye messages

- **Role Management**
  - Visa role system
  - Role tracking and logging
  - Permission-based role commands

- **Security**
  - Raid protection
  - Spam detection
  - Warning system
  - Blacklisted words with wildcard support
  - Auto-moderation

- **Ticket System**
  - Department-based tickets
  - Ticket logging
  - Staff management

## Requirements

- Python 3.8 or higher
- FFmpeg (for voice features)
- Arabic font file (for welcome messages)
- Welcome sound file (MP3 format)

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/arablife.git
cd arablife
```

2. Run the installation script:
```bash
./install.sh
```

3. Configure the bot:
   - Edit the `.env` file with your bot token and other settings
   - Place `welcome.mp3` in the root directory
   - Place `arabic.ttf` in the `fonts` directory

4. Start the bot:
```bash
./run.sh
```

## File Structure

- `welcome.mp3` - Welcome sound file (place in root directory)
- `fonts/arabic.ttf` - Arabic font file for welcome messages
- `.env` - Bot configuration and tokens
- `data/` - Database and persistent data
- `logs/` - Bot logs and error tracking

## Configuration

The `.env` file contains all bot settings:

```env
# Bot Configuration
TOKEN=your_bot_token_here
GUILD_ID=your_guild_id_here

# Channel IDs
WELCOME_CHANNEL_ID=channel_id
WELCOME_VOICE_CHANNEL_ID=voice_channel_id
ROLE_ACTIVITY_LOG_CHANNEL_ID=log_channel_id
AUDIT_LOG_CHANNEL_ID=audit_channel_id

# Role IDs
ROLE_IDS_ALLOWED=role_id1,role_id2
ROLE_ID_TO_GIVE=visa_role_id
ROLE_ID_REMOVE_ALLOWED=admin_role_id

# Security Settings
RAID_PROTECTION=true
SPAM_DETECTION=true
WARNING_THRESHOLD=3
WARNING_ACTION=timeout
WARNING_DURATION=3600
```

## Commands

### Welcome Commands
- `/setwelcomechannel` - Set welcome message channel
- `/setwelcomebackground` - Set welcome image background
- `/testwelcome` - Test welcome system

### Role Commands
- `مقبول` - Give visa role
- `مرفوض` - Remove visa role

### Security Commands
- `/raidmode` - Toggle raid protection
- `/warnings` - Check user warnings
- `/clearwarnings` - Clear user warnings
- `/blacklist` - Manage blacklisted words

### AutoMod Commands
- `/automod_toggle` - Enable/disable automod
- `/automod_action` - Set automod action
- `/automod_exempt` - Add role/channel exemptions
- `/automod_status` - View automod settings

## Development

The bot uses:
- `discord.py` for Discord API
- SQLite for data storage
- Pillow for image processing
- FFmpeg for audio processing

## Troubleshooting

1. **Welcome Sound Not Working**
   - Ensure `welcome.mp3` is in the root directory
   - Check FFmpeg installation
   - Verify voice channel permissions

2. **Welcome Images Not Displaying**
   - Verify `arabic.ttf` is in the fonts directory
   - Check image processing permissions
   - Ensure bot has message permissions

3. **Database Errors**
   - Check write permissions in data directory
   - Verify SQLite installation
   - Check disk space

## Support

For issues and support:
1. Check the logs in `logs/bot.log`
2. Verify all configuration in `.env`
3. Ensure all required files are in place
4. Check bot permissions in Discord

## License

This project is licensed under the MIT License - see the LICENSE file for details.
