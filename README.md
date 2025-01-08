# How to Start ArabLife Bot

## Quick Start Guide

### 1. Install FFmpeg (MOST IMPORTANT - DO THIS FIRST)

**Simple FFmpeg Installation:**
1. Download FFmpeg:
   - Go to [BtbN/FFmpeg-Builds](https://github.com/BtbN/FFmpeg-Builds/releases)
   - Download `ffmpeg-master-latest-win64-gpl.zip`

2. Set up FFmpeg:
   - Extract the zip file
   - Inside the extracted folder, find the `bin` folder
   - Copy these 3 files from the `bin` folder:
     - `ffmpeg.exe`
     - `ffplay.exe`
     - `ffprobe.exe`
   - Create a new folder: `C:\ffmpeg`
   - Paste the 3 files directly in `C:\ffmpeg`

3. Add to System PATH:
   - Press Windows key + X
   - Click "System"
   - Click "Advanced system settings"
   - Click "Environment Variables"
   - Under "System Variables", find "Path"
   - Click "Edit"
   - Click "New"
   - Type: `C:\ffmpeg`
   - Click "OK" on all windows
   - **RESTART YOUR COMPUTER**

4. Test FFmpeg:
   - After restarting, open Command Prompt
   - Type: `ffmpeg -version`
   - Should see FFmpeg version information

### 2. Install Python
- Download Python 3.8 or higher from [python.org](https://python.org)
- During installation, CHECK "Add Python to PATH"
- Open cmd and type `python --version` to verify

### 3. Install Bot Dependencies
- Open cmd in your bot folder
- Run this command:
```bash
pip install discord.py[voice] python-dotenv PyNaCl
```

### 4. Set Up Bot Files
1. Download these files:
```
bot.py
config.py
utils/logger.py
cogs/role_commands.py
cogs/voice_commands.py
cogs/status_commands.py
cogs/help_commands.py
```

2. Keep this folder structure:
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
    └── help_commands.py
```

### 5. Create .env File
Create a file named `.env` in your bot folder:
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

# FFmpeg Settings (IMPORTANT)
FFMPEG_PATH=C:\ffmpeg\ffmpeg.exe

# Optional Settings
WELCOME_SOUND_PATH=welcome.mp3
DEFAULT_VOLUME=0.5
```

### 6. Add Welcome Sound
- Put `welcome.mp3` in your bot folder
- Or use a different name and update WELCOME_SOUND_PATH in .env

### 7. Add Visa Image
1. Upload image to imgur.com
2. Right-click → Copy image address
3. Add to .env as VISA_IMAGE_URL

### 8. Start the Bot
```bash
python bot.py
```

## Testing

### 1. Test FFmpeg First
1. Open new Command Prompt
2. Type: `ffmpeg -version`
3. If you see an error:
   - Double-check PATH setup
   - Make sure you restarted your computer
   - Verify files are in C:\ffmpeg
   - Try full path: `C:\ffmpeg\ffmpeg -version`

### 2. Test Bot Commands
1. Voice Test:
   - Join a voice channel
   - Type `/testsound`
   - Should hear welcome sound

2. Role Commands:
   - `/مقبول @user` - Give role
   - `/مرفوض @user` - Remove role

3. Help Command:
   - Type `/help`

## Common Problems

### FFmpeg Issues
If `ffmpeg -version` doesn't work:
1. Open Command Prompt as Administrator
2. Run these commands:
```cmd
setx PATH "%PATH%;C:\ffmpeg"
```
3. Restart your computer
4. Try `ffmpeg -version` again

If still not working:
1. Delete C:\ffmpeg folder
2. Follow installation steps again
3. Make sure you copy ONLY the 3 .exe files
4. Restart computer

### No Sound Playing
1. Check FFmpeg:
```cmd
C:\ffmpeg\ffmpeg -version
```
2. Update .env:
```env
FFMPEG_PATH=C:\ffmpeg\ffmpeg.exe
```
3. Verify welcome.mp3 exists
4. Restart bot

### Other Issues
- Make sure all dependencies are installed
- Check bot permissions in Discord
- Verify all IDs in .env
- Check log channels for errors

Need help? [Discord.py Voice Guide](https://discordpy.readthedocs.io/en/stable/api.html#voice)
