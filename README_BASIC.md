# ArabLife Discord Bot

## Overview
ArabLife Bot is a powerful Discord bot designed to enhance server management and user experience. The bot provides welcome messages, role management, announcements, voice channel controls, and application systems.

## Features

### Welcome System
- Automatic welcome messages for new members
- Custom welcome audio
- Member verification system

### Role Management
- Self-assignable roles
- Automatic role assignment
- Role hierarchy management

### Announcements
- Rich embedded announcements
- Scheduled announcements
- Role-specific announcements

### Voice Features
- Dynamic voice channel creation
- Voice activity tracking
- Audio playback capabilities

### Application System
- Server join applications
- Staff applications
- Application review process

## Setup

### Prerequisites
- Python 3.8 or higher
- PostgreSQL database
- Discord Bot Token

### Installation
1. Clone the repository
2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and configure:
   ```
   DISCORD_TOKEN=your_bot_token
   DATABASE_URL=your_database_url
   ```
4. Initialize the database:
   ```bash
   python -m utils.database
   ```
5. Run the bot:
   ```bash
   python bot.py
   ```

## Basic Commands

### Welcome
- `/welcome`: Configure welcome settings
- `/verify`: Verify new members

### Roles
- `/role add`: Add assignable role
- `/role remove`: Remove role
- `/role list`: List available roles

### Announcements
- `/announce`: Create announcement
- `/schedule`: Schedule announcement
- `/edit`: Edit announcement

### Voice
- `/voice create`: Create voice channel
- `/voice limit`: Set user limit
- `/voice lock`: Lock voice channel

### Applications
- `/apply`: Start application process
- `/review`: Review pending applications
- `/approve`: Approve application
- `/reject`: Reject application

## Support
For technical support or questions, please refer to the TECHNICAL_DOCUMENTATION.md file or open an issue on the repository.

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License
This project is licensed under the MIT License - see the LICENSE file for details.
