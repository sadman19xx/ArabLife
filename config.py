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
    
    # Voice settings
    FFMPEG_PATH = os.getenv('FFMPEG_PATH', shutil.which('ffmpeg') or 'ffmpeg')
    DEFAULT_VOLUME = float(os.getenv('DEFAULT_VOLUME', '0.5'))
    SOUND_COMMAND_COOLDOWN = int(os.getenv('SOUND_COMMAND_COOLDOWN', '30'))
    VOICE_TIMEOUT = int(os.getenv('VOICE_TIMEOUT', '20'))
    MAX_RECONNECT_ATTEMPTS = int(os.getenv('MAX_RECONNECT_ATTEMPTS', '10'))
    RECONNECT_DELAY = int(os.getenv('RECONNECT_DELAY', '1'))
    MAX_RECONNECT_DELAY = int(os.getenv('MAX_RECONNECT_DELAY', '30'))
    
    # Role management settings
    ROLE_COMMAND_COOLDOWN = int(os.getenv('ROLE_COMMAND_COOLDOWN', '60'))
    ROLE_ID_TO_GIVE = int(os.getenv('ROLE_ID_TO_GIVE', '0'))
    ROLE_IDS_ALLOWED = [int(id) for id in os.getenv('ROLE_IDS_ALLOWED', '').split(',') if id]
    
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
            
        # Check welcome sound file exists
        welcome_sound_absolute = os.path.abspath(cls.WELCOME_SOUND_PATH)
        if not os.path.exists(welcome_sound_absolute):
            raise ValueError(f"Welcome sound file not found: {welcome_sound_absolute}")
