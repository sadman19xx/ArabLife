# How to Start ArabLife Bot

## Quick Start Guide

1. **Download the Files**
   - Download all these files:
     ```
     bot.py
     config.py
     utils/logger.py
     cogs/role_commands.py
     cogs/voice_commands.py
     cogs/status_commands.py
     ```
   - Keep the same folder structure:
     ```
     ArabLife/
     ├── bot.py
     ├── config.py
     ├── utils/
     │   └── logger.py
     └── cogs/
         ├── role_commands.py
         ├── voice_commands.py
         └── status_commands.py
     ```

2. **Install Python**
   - Download Python from [python.org](https://python.org)
   - During installation, check "Add Python to PATH"
   - Verify installation by opening cmd and typing: `python --version`

3. **Install FFmpeg**
   - Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)
   - Extract the files
   - Copy the path to the bin folder (e.g., `C:\ffmpeg\bin`)
   - Add to PATH:
     1. Search "Environment Variables" in Windows
     2. Click "Environment Variables"
     3. Under "System Variables" find "Path"
     4. Click "Edit" → "New"
     5. Paste the FFmpeg bin path
     6. Click "OK" on all windows

4. **Install Bot Dependencies**
   - Open cmd in your bot folder
   - Run this command:
     ```
     pip install discord.py python-dotenv
     ```

5. **Create .env File**
   - Create a new file named `.env` in your bot folder
   - Copy this template:
     ```
     TOKEN=your_bot_token
     GUILD_ID=your_guild_id
     ROLE_IDS_ALLOWED=role_id1,role_id2,role_id3
     ROLE_ID_TO_GIVE=role_id_to_give
     ROLE_ID_REMOVE_ALLOWED=role_id_for_remove_command
     ROLE_ACTIVITY_LOG_CHANNEL_ID=log_channel_id
     AUDIT_LOG_CHANNEL_ID=audit_channel_id
     ```
   - Replace values with your Discord IDs:
     - To get IDs, enable Developer Mode in Discord:
       1. Settings → App Settings → Advanced
       2. Turn on Developer Mode
     - Right-click on roles/channels and click "Copy ID"

6. **Add Welcome Sound**
   - Put your welcome sound file in the bot folder
   - Name it `welcome.mp3`
   - Or if using a different name, add to .env:
     ```
     WELCOME_SOUND_PATH=your_sound_file.mp3
     ```

7. **Start the Bot**
   - Open cmd in your bot folder
   - Type this command:
     ```
     python bot.py
     ```
   - You should see "Logged in as [bot name]"

## Common Problems

1. **"python not recognized"**
   - Reinstall Python and check "Add Python to PATH"
   - Or add Python to PATH manually

2. **"No module named discord"**
   - Run: `pip install discord.py python-dotenv`

3. **"No such file .env"**
   - Make sure you created the .env file
   - Make sure it's in the same folder as bot.py

4. **"FFmpeg not found"**
   - Make sure you added FFmpeg to PATH
   - Try restarting your computer

5. **Bot not responding**
   - Check if your TOKEN is correct
   - Make sure all IDs in .env are correct
   - Check if bot has correct permissions in Discord

Need more help? Check the [Discord.py Documentation](https://discordpy.readthedocs.io/)
