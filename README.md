# ArabLife Discord Bot

A Discord bot for managing server roles and welcoming new members.

## Features

1. Application Approval/Denial System
   - `/accept @User` - Accepts a user's application and assigns the citizen role
   - `/reject @User [reason]` - Rejects a user's application with a specified reason
   - Automated response messages with visa images
   - Role-based permissions for staff members

2. Welcome Voice System
   - Plays a custom welcome sound when new members join
   - Automatically disconnects after playing the sound

## Requirements

- Python 3.8 or higher
- FFmpeg installed on your system
- A Discord bot token
- Welcome sound file (MP3 format)
- Visa images (accept.png and reject.png)

## Setup

1. Clone this repository
2. Run the installation script:
```bash
chmod +x install.sh
./install.sh
```

3. Configure your bot:
   - Copy `.env.example` to `.env` (done automatically by install script)
   - Update the following settings in `.env`:
     - `TOKEN`: Your Discord bot token
     - `GUILD_ID`: Your Discord server ID
     - `APPLICATION_ID`: Your bot's application ID
     - `WELCOME_VOICE_CHANNEL_ID`: Voice channel ID for welcome sounds
     - `WELCOME_SOUND_PATH`: Path to welcome sound file (default: welcome.mp3)
     - `FFMPEG_PATH`: Path to FFmpeg executable (optional)

4. Add required files:
   - Place welcome sound file as `welcome.mp3` in the bot directory
   - Place visa images in the `assets` directory:
     - `accept.png` - Image shown for accepted applications
     - `reject.png` - Image shown for rejected applications

## Running the Bot

```bash
chmod +x run.sh
./run.sh
```

## Configuration

All configuration is done through environment variables in the `.env` file:

```env
# Bot Configuration
TOKEN=your_bot_token_here
GUILD_ID=your_guild_id_here
APPLICATION_ID=your_application_id_here

# Welcome Voice Settings
WELCOME_VOICE_CHANNEL_ID=your_voice_channel_id_here
WELCOME_SOUND_PATH=welcome.mp3

# Voice Settings (Optional)
FFMPEG_PATH=/path/to/ffmpeg

# Role IDs
STAFF_ROLE_ID=1287486561914589346
CITIZEN_ROLE_ID=1309555494586683474

# Channel IDs
RESPONSE_CHANNEL_ID=1309556312027430922
```

## License

MIT License
