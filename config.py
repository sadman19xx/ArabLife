import os
import shutil
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration settings for the bot"""
    
    # Bot token and application settings
    TOKEN = os.getenv('TOKEN')
    GUILD_ID = int(os.getenv('GUILD_ID', '0'))
    APPLICATION_ID = int(os.getenv('APPLICATION_ID', '0'))
    
    # Welcome settings
    WELCOME_VOICE_CHANNEL_ID = int(os.getenv('WELCOME_VOICE_CHANNEL_ID', '0'))
    WELCOME_SOUND_PATH = os.getenv('WELCOME_SOUND_PATH', 'welcome.mp3')
    WELCOME_SOUND_VOLUME = float(os.getenv('WELCOME_SOUND_VOLUME', '0.5'))
    
    # Voice System Settings
    FFMPEG_PATH = os.getenv('FFMPEG_PATH', shutil.which('ffmpeg') or '/usr/bin/ffmpeg')
    DEFAULT_VOLUME = float(os.getenv('DEFAULT_VOLUME', '0.5'))
    VOICE_TIMEOUT = int(os.getenv('VOICE_TIMEOUT', '30'))  # Increased for better stability
    MAX_RECONNECT_ATTEMPTS = int(os.getenv('MAX_RECONNECT_ATTEMPTS', '5'))  # Balanced retry attempts
    RECONNECT_DELAY = int(os.getenv('RECONNECT_DELAY', '5'))  # Initial delay
    MAX_RECONNECT_DELAY = int(os.getenv('MAX_RECONNECT_DELAY', '60'))  # Increased max delay
    
    # Voice State Settings
    VOICE_DEAF_CHECK_INTERVAL = 2  # More frequent deafen checks
    VOICE_HEALTH_CHECK_INTERVAL = 5  # More frequent health checks
    VOICE_CLEANUP_DELAY = 2  # Delay before cleaning up old connections
    VOICE_STABILIZATION_DELAY = 2  # Delay to let connection stabilize
    
    # Role management settings
    ROLE_COMMAND_COOLDOWN = int(os.getenv('ROLE_COMMAND_COOLDOWN', '60'))
    ROLE_ID_TO_GIVE = int(os.getenv('ROLE_ID_TO_GIVE', '0'))
    ROLE_IDS_ALLOWED = [int(id) for id in os.getenv('ROLE_IDS_ALLOWED', '').split(',') if id]
    
    # Status command settings
    STATUS_COMMAND_COOLDOWN = 60
    MAX_STATUS_LENGTH = 100
    BLACKLISTED_WORDS = []
    
    # Logging settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
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
            
        if not cls.ROLE_ID_TO_GIVE:
            raise ValueError("Role ID to give not found in environment variables")
            
        # Validate welcome channel
        if not cls.WELCOME_VOICE_CHANNEL_ID:
            raise ValueError("Welcome voice channel ID not found in environment variables")
            
        # Validate welcome sound
        welcome_sound_absolute = os.path.abspath(cls.WELCOME_SOUND_PATH)
        if not os.path.exists(welcome_sound_absolute):
            raise ValueError(f"Welcome sound file not found: {welcome_sound_absolute}")
            
        # Validate FFmpeg
        if not shutil.which(cls.FFMPEG_PATH):
            raise ValueError(f"FFmpeg not found at {cls.FFMPEG_PATH}")
            
        # Validate volume settings
        if not 0.0 <= cls.WELCOME_SOUND_VOLUME <= 2.0:
            raise ValueError("Welcome sound volume must be between 0.0 and 2.0")
        if not 0.0 <= cls.DEFAULT_VOLUME <= 2.0:
            raise ValueError("Default volume must be between 0.0 and 2.0")
            
        # Validate timing settings
        if cls.VOICE_TIMEOUT < 5:
            raise ValueError("Voice timeout must be at least 5 seconds")
        if cls.RECONNECT_DELAY < 1:
            raise ValueError("Reconnect delay must be at least 1 second")
        if cls.MAX_RECONNECT_DELAY < cls.RECONNECT_DELAY:
            raise ValueError("Max reconnect delay must be greater than initial delay")
