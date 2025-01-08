import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
class Config:
    # Token and Guild settings
    TOKEN = os.getenv('TOKEN')
    GUILD_ID = int(os.getenv('GUILD_ID'))
    
    # Role settings
    ROLE_IDS_ALLOWED = list(map(int, os.getenv('ROLE_IDS_ALLOWED', '').split(',')))
    ROLE_ID_TO_GIVE = int(os.getenv('ROLE_ID_TO_GIVE'))
    ROLE_ID_REMOVE_ALLOWED = int(os.getenv('ROLE_ID_REMOVE_ALLOWED'))
    
    # Channel IDs
    ROLE_ACTIVITY_LOG_CHANNEL_ID = int(os.getenv('ROLE_ACTIVITY_LOG_CHANNEL_ID'))
    AUDIT_LOG_CHANNEL_ID = int(os.getenv('AUDIT_LOG_CHANNEL_ID'))
    
    # Voice settings
    WELCOME_SOUND_PATH = os.getenv('WELCOME_SOUND_PATH', 'welcome.mp3')
    DEFAULT_VOLUME = float(os.getenv('DEFAULT_VOLUME', '0.5'))
    FFMPEG_PATH = os.getenv('FFMPEG_PATH', None)  # Optional custom FFmpeg path
    
    # Command cooldowns (in seconds)
    ROLE_COMMAND_COOLDOWN = int(os.getenv('ROLE_COMMAND_COOLDOWN', '5'))
    STATUS_COMMAND_COOLDOWN = int(os.getenv('STATUS_COMMAND_COOLDOWN', '10'))
    SOUND_COMMAND_COOLDOWN = int(os.getenv('SOUND_COMMAND_COOLDOWN', '5'))
    
    # Security settings
    MAX_STATUS_LENGTH = int(os.getenv('MAX_STATUS_LENGTH', '100'))
    BLACKLISTED_WORDS = os.getenv('BLACKLISTED_WORDS', '').split(',')
    
    # Visa settings
    VISA_IMAGE_URL = os.getenv('VISA_IMAGE_URL', 'https://i.imgur.com/your_image_id.png')
    
    @classmethod
    def validate_config(cls):
        """Validate required configuration values"""
        required_fields = [
            ('TOKEN', cls.TOKEN),
            ('GUILD_ID', cls.GUILD_ID),
            ('ROLE_ID_TO_GIVE', cls.ROLE_ID_TO_GIVE),
            ('ROLE_ID_REMOVE_ALLOWED', cls.ROLE_ID_REMOVE_ALLOWED),
            ('ROLE_ACTIVITY_LOG_CHANNEL_ID', cls.ROLE_ACTIVITY_LOG_CHANNEL_ID),
            ('AUDIT_LOG_CHANNEL_ID', cls.AUDIT_LOG_CHANNEL_ID),
            ('VISA_IMAGE_URL', cls.VISA_IMAGE_URL)
        ]
        
        missing_fields = [field for field, value in required_fields if not value]
        
        if missing_fields:
            raise ValueError(f"Missing required configuration: {', '.join(missing_fields)}")
            
        if not cls.ROLE_IDS_ALLOWED:
            raise ValueError("At least one allowed role ID must be configured")

        # Validate FFmpeg if path is provided
        if cls.FFMPEG_PATH and not os.path.isfile(cls.FFMPEG_PATH):
            raise ValueError(f"FFmpeg not found at specified path: {cls.FFMPEG_PATH}")

        # Validate welcome sound file
        if not os.path.isfile(cls.WELCOME_SOUND_PATH):
            raise ValueError(f"Welcome sound file not found at: {cls.WELCOME_SOUND_PATH}")
