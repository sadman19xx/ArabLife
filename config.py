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
    WELCOME_SOUND_VOLUME = float(os.getenv('WELCOME_SOUND_VOLUME', '0.5'))  # Default to 50% volume
    
    # Voice settings
    FFMPEG_PATH = os.getenv('FFMPEG_PATH')  # Will be detected automatically if not set
    DEFAULT_VOLUME = float(os.getenv('DEFAULT_VOLUME', '0.5'))  # Default to 50% volume
    SOUND_COMMAND_COOLDOWN = int(os.getenv('SOUND_COMMAND_COOLDOWN', '30'))  # Default 30 seconds cooldown
    VOICE_TIMEOUT = int(os.getenv('VOICE_TIMEOUT', '20'))  # Voice connection timeout in seconds
    MAX_RECONNECT_ATTEMPTS = int(os.getenv('MAX_RECONNECT_ATTEMPTS', '10'))  # Maximum reconnection attempts
    RECONNECT_DELAY = int(os.getenv('RECONNECT_DELAY', '1'))  # Initial reconnection delay in seconds
    MAX_RECONNECT_DELAY = int(os.getenv('MAX_RECONNECT_DELAY', '30'))  # Maximum reconnection delay in seconds
    
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
            
        # Check FFMPEG installation if path is provided
        if cls.FFMPEG_PATH:
            if not os.path.exists(cls.FFMPEG_PATH):
                raise ValueError(f"FFMPEG not found at specified path: {cls.FFMPEG_PATH}")
        else:
            # Try to detect FFmpeg
            import shutil
            ffmpeg_path = shutil.which('ffmpeg')
            if not ffmpeg_path:
                # Check common locations
                common_paths = [
                    r"C:\ffmpeg\bin\ffmpeg.exe",  # Windows custom install
                    r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",  # Windows program files
                    r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",  # Windows program files x86
                    "/usr/bin/ffmpeg",  # Linux default
                    "/usr/local/bin/ffmpeg",  # Linux alternative
                    "/opt/homebrew/bin/ffmpeg",  # macOS Homebrew
                ]
                for path in common_paths:
                    if os.path.isfile(path):
                        cls.FFMPEG_PATH = path
                        break
                if not cls.FFMPEG_PATH:
                    cls.FFMPEG_PATH = "ffmpeg"  # Default to letting system resolve it
