# ArabLife Discord Bot

Discord bot for Arabic communities with welcome system, role management, and security features.

## Ubuntu Installation

1. Update system and install dependencies:
```bash
sudo apt update
sudo apt install -y git python3 python3-pip python3-venv ffmpeg
```

2. Clone and setup:
```bash
git clone https://github.com/yourusername/arablife.git
cd arablife
chmod +x install.sh run.sh
./install.sh
```

3. Add required files:
- Place `welcome.mp3` in the root directory
- Place `arabic.ttf` in the `fonts` directory
- Edit `.env` with your bot settings

4. Start the bot:
```bash
./run.sh
```

## Features

### Welcome System
- Custom welcome images with Arabic text
- Welcome sound in voice channel
- Configurable messages

### Role Management
- Visa role system (`مقبول`, `مرفوض`)
- Role tracking
- Permission-based commands

### Security
- Raid protection
- Spam detection
- Warning system
- Word blacklist

### Ticket System
- Department-based tickets
- Ticket logging
- Staff management

## Commands

### Welcome
- `/setwelcomechannel` - Set welcome channel
- `/setwelcomebackground` - Set background
- `/testwelcome` - Test system

### Roles
- `مقبول` - Give visa role
- `مرفوض` - Remove visa role

### Security
- `/raidmode` - Toggle raid mode
- `/warnings` - Check warnings
- `/clearwarnings` - Clear warnings
- `/blacklist` - Manage blacklist

### AutoMod
- `/automod_toggle` - Toggle automod
- `/automod_action` - Set action
- `/automod_exempt` - Add exemptions
- `/automod_status` - View settings

## Troubleshooting

1. **Welcome Sound Issues**
   - Check `welcome.mp3` exists
   - Verify FFmpeg installation
   - Check voice permissions

2. **Welcome Images Issues**
   - Verify `arabic.ttf` exists
   - Check bot permissions

3. **Database Issues**
   - Check directory permissions
   - Verify disk space

For support:
1. Check `logs/bot.log`
2. Verify `.env` settings
3. Check Discord permissions
