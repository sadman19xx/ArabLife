import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration settings for the bot"""
    
    # Bot token and application settings
    TOKEN = os.getenv('TOKEN')
    GUILD_ID = int(os.getenv('GUILD_ID', 0))
    APPLICATION_ID = int(os.getenv('APPLICATION_ID', 0))
    
    # Welcome settings
    WELCOME_VOICE_CHANNEL_ID = int(os.getenv('WELCOME_VOICE_CHANNEL_ID', 1309595750878937240))
    WELCOME_SOUND_PATH = os.getenv('WELCOME_SOUND_PATH', 'welcome.mp3')
    
    # Voice settings
    FFMPEG_PATH = os.getenv('FFMPEG_PATH', '/usr/bin/ffmpeg')  # Default Ubuntu path
    
    # Logging settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')  # Set to INFO to reduce spam, only ERROR and above go to error channel
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_TO_FILE = os.getenv('LOG_TO_FILE', 'false').lower() == 'true'
    LOG_DIR = os.getenv('LOG_DIR', 'logs')
    
    @classmethod
    def validate_config(cls) -> None:
        """Validate required configuration settings"""
        if not cls.TOKEN:
            raise ValueError("Bot token not found in environment variables")
            
        if not cls.GUILD_ID:
            raise ValueError("Guild ID not found in environment variables")
            
        if not cls.APPLICATION_ID:
            raise ValueError("Application ID not found in environment variables")
            
        # Check welcome sound file with absolute path
        welcome_sound_absolute = os.path.abspath(cls.WELCOME_SOUND_PATH)
        if not os.path.exists(welcome_sound_absolute):
            raise ValueError(f"Welcome sound file not found: {welcome_sound_absolute}")
            
        # Check FFMPEG installation
        if not os.path.exists(cls.FFMPEG_PATH):
            raise ValueError(f"FFMPEG not found at: {cls.FFMPEG_PATH}")
