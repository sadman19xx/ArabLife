Fahad, a beacon shining bright,
Strength and kindness in your light.
```

# ArabLife Bot Basic Setup Guide
*Developed by Fahad and Sadman*

## 1. Install FFmpeg (REQUIRED)

1. Download FFmpeg:
   - Go to [BtbN/FFmpeg-Builds](https://github.com/BtbN/FFmpeg-Builds/releases)
   - Download `ffmpeg-master-latest-win64-gpl.zip`

2. Set up FFmpeg:
   - Extract the zip file
   - Inside the extracted folder, find the `bin` folder
   - Copy these 3 files from `bin`:
     - `ffmpeg.exe`
     - `ffplay.exe`
     - `ffprobe.exe`
   - Create folder: `C:\ffmpeg`
   - Paste the 3 files in `C:\ffmpeg`

3. Add to System PATH:
   - Press Windows key + X
   - Click "System"
   - Click "Advanced system settings"
   - Click "Environment Variables"
   - Under "System Variables", find "Path"
   - Click "Edit" → "New"
   - Type: `C:\ffmpeg`
   - Click "OK" on all windows
   - **RESTART YOUR COMPUTER**

4. Test FFmpeg:
   ```cmd
   ffmpeg -version
   ```

## 2. Install Python
1. Download Python 3.8+ from [python.org](https://python.org)
2. During installation:
   - ✅ CHECK "Add Python to PATH"
   - ✅ CHECK "Install pip"
3. Verify installation:
   ```cmd
   python --version
   pip --version
   ```

## 3. Install Bot Dependencies
```bash
pip install discord.py[voice] python-dotenv PyNaCl
```

## 4. Setup Bot Files

1. Create this folder structure:
```
ArabLife/
├── bot.py
├── config.py
├── utils/
│   └── logger.py
└── cogs/
    ├── role_commands.py
    ├── voice_commands.py
    ├── status_commands.py
    ├── ticket_commands.py
    └── help_commands.py
```

2. Create `.env` file:
```env
# Required Settings
TOKEN=your_bot_token
GUILD_ID=your_guild_id
ROLE_IDS_ALLOWED=role_id1,role_id2,role_id3
ROLE_ID_TO_GIVE=role_id_to_give
ROLE_ID_REMOVE_ALLOWED=role_id_for_remove_command
ROLE_ACTIVITY_LOG_CHANNEL_ID=log_channel_id
AUDIT_LOG_CHANNEL_ID=audit_channel_id
VISA_IMAGE_URL=your_visa_image_url

# Voice Settings
FFMPEG_PATH=C:\ffmpeg\ffmpeg.exe
WELCOME_SOUND_PATH=welcome.mp3
DEFAULT_VOLUME=0.5
WELCOME_VOICE_CHANNEL_ID=1309595750878937240

# Ticket Settings (Optional)
TICKET_STAFF_ROLE_ID=staff_role_id
TICKET_CATEGORY_ID=category_id
TICKET_LOG_CHANNEL_ID=log_channel_id
```

## 5. Get Discord IDs

1. Enable Developer Mode:
   - Open Discord
   - Go to Settings → App Settings → Advanced
   - Turn ON "Developer Mode"

2. Get IDs:
   - Right-click on roles/channels
   - Click "Copy ID"
   - Paste in `.env` file

## 6. Add Welcome Sound
1. Get an MP3 file for welcome sound
2. Name it `welcome.mp3`
3. Put it in the bot folder
4. Or use different name and update in .env:
   ```env
   WELCOME_SOUND_PATH=your_sound.mp3
   ```

## 7. Add Visa Image
1. Upload image to imgur.com
2. Right-click → Copy image address
3. Add to .env:
   ```env
   VISA_IMAGE_URL=your_image_url
   ```

## 8. Start the Bot
```bash
python bot.py
```

## Common Issues

### FFmpeg Not Found
1. Check PATH:
   ```cmd
   echo %PATH%
   ```
   Should see `C:\ffmpeg`

2. Try direct path in .env:
   ```env
   FFMPEG_PATH=C:\ffmpeg\ffmpeg.exe
   ```

3. Verify files:
   - Check `C:\ffmpeg` has all 3 .exe files
   - Try running: `C:\ffmpeg\ffmpeg -version`

### No Sound Playing
1. Check FFmpeg:
   ```cmd
   ffmpeg -version
   ```
2. Check welcome.mp3 exists
3. Check bot's voice permissions
4. Try restarting Discord

### Bot Not Starting
1. Check Python installation
2. Verify all dependencies installed
3. Check .env file exists and has correct values
4. Check bot token is valid
5. Check log for specific errors

### Need More Help?
- [Discord.py Documentation](https://discordpy.readthedocs.io/)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [Python Documentation](https://docs.python.org/)

---
*Bot developed and maintained by Fahad and Sadman*
