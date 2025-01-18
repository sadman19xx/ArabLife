# ArabLife Discord Bot

A Discord bot for managing ArabLife server with role management, welcome system, and more.

## Features

1. Application System
   - `/accept @User` - Accepts a user's application and assigns the citizen role
   - `/reject @User [reason]` - Rejects a user's application with a specified reason
   - Automated response messages with visa images

2. Welcome System
   - Plays custom welcome sound for new members
   - Automated welcome messages
   - `/testwelcome` - Test the welcome sound system

3. Role Management
   - Role assignment commands
   - Role hierarchy management
   - Role-based permissions

4. Voice Channel Management
   - Automatic welcome sound playback for new members
   - Welcome sound when users join specific voice channel
   - Robust connection handling with auto-reconnection
   - Exponential backoff for reconnection attempts
   - Volume control and FFmpeg optimization
   - `!rejoin` command for manual reconnection
   - Shared voice client coordination

5. Status Commands
   - Server status monitoring
   - Bot health checks
   - System metrics

6. Announcement System
   - Server announcements
   - Automated notifications
   - Message management

## Requirements

- Ubuntu/Debian Linux system (20.04 LTS or higher recommended)
- Python 3.8 or higher
- FFmpeg (installed automatically via install.sh)
- Discord bot token
- Welcome sound file (MP3 format)
- Visa images (accept.png and reject.png)

Note: This bot is designed to run on Ubuntu/Debian systems only.

## Installation

1. Clone this repository
2. Run the installation script:
```bash
sudo chmod +x install.sh
sudo ./install.sh
```

The installation script will:
- Install system dependencies (Python3, FFmpeg)
- Create and configure Python virtual environment
- Install required Python packages
- Set up configuration files
- Create necessary directories
- Validate the environment

## Configuration

The `.env` file (created during installation) needs to be configured with:

```env
# Bot Configuration
TOKEN=your_bot_token_here
GUILD_ID=your_guild_id_here
APPLICATION_ID=your_application_id_here

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

## Running the Bot

### Method 1: Manual Run (Development)

```bash
./run.sh
```

The run script will:
- Verify the environment is properly set up
- Activate the virtual environment
- Start the bot

### Method 2: Systemd Service (Production Recommended)

For production environments, run the bot as a systemd service for:
- Automatic startup on system boot
- Automatic restart on crashes (3-second delay)
- Proper logging and monitoring
- Process management

Installation Steps:

1. First install the bot and configure .env:
```bash
sudo ./install.sh
# Configure your .env file
```

2. Install the service:
```bash
sudo ./install-service.sh
```

The service installation:
- Creates necessary log files in /var/log/
- Sets up proper permissions
- Creates required directories
- Configures systemd service
- Enables automatic startup
- Starts the service

Service Management:

```bash
# View detailed status
sudo systemctl status arablife-bot

# View logs (multiple options)
sudo journalctl -u arablife-bot -f             # Live systemd logs
tail -f /var/log/arablife-bot.log             # Application logs
tail -f /var/log/arablife-bot.error.log       # Error logs

# Control commands
sudo systemctl start arablife-bot              # Start the bot
sudo systemctl stop arablife-bot               # Stop the bot
sudo systemctl restart arablife-bot            # Restart the bot
```

Service Features:
- Runs in virtual environment
- Automatic directory creation
- Proper PATH and PYTHONPATH setup
- Log rotation and management
- Process monitoring and recovery

## Troubleshooting

1. Installation Issues:
   - Run install.sh with sudo
   - Check system requirements
   - Verify internet connection

2. Configuration Issues:
   - Validate .env file settings
   - Check Discord Developer Portal settings
   - Verify all IDs are correct

3. Runtime Issues:
   - Check systemd service logs: `sudo journalctl -u arablife-bot -f`
   - Check application logs: `tail -f /var/log/arablife-bot.log`
   - Check error logs: `tail -f /var/log/arablife-bot.error.log`
   - Verify bot permissions in Discord
   - Ensure FFmpeg is properly installed: `ffmpeg -version`
   - Check service configuration: `sudo systemctl cat arablife-bot`
   - Check service status: `sudo systemctl status arablife-bot`
   - Verify file permissions: `ls -la /root/ArabLife/`
   - Check virtual environment: `ls -la /root/ArabLife/venv/`

4. Voice System Issues:
   - Verify welcome.mp3 exists and is readable
   - Check FFmpeg installation and permissions
   - Verify bot has CONNECT and SPEAK permissions
   - Ensure bot is not server deafened
   - Check voice channel ID in configuration
   - Monitor voice connection logs
   - Use !rejoin command if connection issues persist
   - Check voice volume settings in .env

## Support

- Check BOT_SETUP_GUIDE.md for detailed setup instructions
- Review README_BASIC.md for hosting-specific setup
- Check logs directory for error details
- Ensure all environment variables are properly set

## Security Notes

- Keep your bot token secure
- Regularly update dependencies
- Monitor bot logs
- Back up your configuration regularly
- Use appropriate role permissions

## License

MIT License
