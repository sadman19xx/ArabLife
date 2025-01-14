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
    APPLICATION_ID = int(os.getenv('APPLICATION_ID', 0))  # Required for slash commands
    
    # Command cooldowns (in seconds)
    ROLE_COMMAND_COOLDOWN = int(os.getenv('ROLE_COMMAND_COOLDOWN', 5))
    SOUND_COMMAND_COOLDOWN = int(os.getenv('SOUND_COMMAND_COOLDOWN', 5))
    STATUS_COMMAND_COOLDOWN = int(os.getenv('STATUS_COMMAND_COOLDOWN', 5))
    TICKET_COMMAND_COOLDOWN = int(os.getenv('TICKET_COMMAND_COOLDOWN', 5))
    SECURITY_COMMAND_COOLDOWN = int(os.getenv('SECURITY_COMMAND_COOLDOWN', 5))
    AUTOMOD_COMMAND_COOLDOWN = int(os.getenv('AUTOMOD_COMMAND_COOLDOWN', 5))
    
    # Welcome settings
    WELCOME_CHANNEL_ID = int(os.getenv('WELCOME_CHANNEL_ID', 0))
    WELCOME_VOICE_CHANNEL_ID = int(os.getenv('WELCOME_VOICE_CHANNEL_ID', 1309595750878937240))
    WELCOME_SOUND_PATH = os.getenv('WELCOME_SOUND_PATH', 'welcome.mp3')
    DEFAULT_VOLUME = float(os.getenv('DEFAULT_VOLUME', 0.5))
    
    # Logging settings
    LOG_TO_FILE = bool(int(os.getenv('LOG_TO_FILE', 1)))
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    LOG_DIR = os.getenv('LOG_DIR', 'logs')
    ROLE_ACTIVITY_LOG_CHANNEL_ID = int(os.getenv('ROLE_ACTIVITY_LOG_CHANNEL_ID', 0))
    AUDIT_LOG_CHANNEL_ID = int(os.getenv('AUDIT_LOG_CHANNEL_ID', 0))
    ERROR_LOG_CHANNEL_ID = int(os.getenv('ERROR_LOG_CHANNEL_ID', 0))
    
    # AutoMod settings
    AUTOMOD_ENABLED = bool(int(os.getenv('AUTOMOD_ENABLED', 1)))
    AUTOMOD_ACTION = os.getenv('AUTOMOD_ACTION', 'warn')
    AUTOMOD_SPAM_THRESHOLD = int(os.getenv('AUTOMOD_SPAM_THRESHOLD', 5))
    AUTOMOD_SPAM_INTERVAL = int(os.getenv('AUTOMOD_SPAM_INTERVAL', 5))
    AUTOMOD_RAID_THRESHOLD = int(os.getenv('AUTOMOD_RAID_THRESHOLD', 10))
    AUTOMOD_RAID_INTERVAL = int(os.getenv('AUTOMOD_RAID_INTERVAL', 10))
    
    # Health check settings
    HEALTH_CHECK_HOST = os.getenv('HEALTH_CHECK_HOST', '127.0.0.1')
    HEALTH_CHECK_PORT = int(os.getenv('HEALTH_CHECK_PORT', 8080))
    HEALTH_CHECK_METRICS_COOLDOWN = int(os.getenv('HEALTH_CHECK_METRICS_COOLDOWN', 60))
    
    # Blacklisted words/domains
    BLACKLISTED_WORDS = os.getenv('BLACKLISTED_WORDS', '').split(',')
    ALLOWED_DOMAINS = os.getenv('ALLOWED_DOMAINS', 'discord.com,discord.gg').split(',')
    
    # Role settings
    VISA_IMAGE_URL = os.getenv('VISA_IMAGE_URL', 'https://i.imgur.com/default_visa.png')
    
    # Voice settings
    FFMPEG_PATH = os.getenv('FFMPEG_PATH', '/usr/bin/ffmpeg')  # Default Linux path
    
    # FiveM Integration settings
    FIVEM_API_PORT = int(os.getenv('FIVEM_API_PORT', 3033))
    FIVEM_API_HOST = os.getenv('FIVEM_API_HOST', '127.0.0.1')
    
    @classmethod
    def validate_config(cls) -> None:
        """Validate required configuration settings"""
        if not cls.TOKEN:
            raise ValueError("Bot token not found in environment variables")
            
        if not cls.GUILD_ID:
            raise ValueError("Guild ID not found in environment variables")
            
        if not cls.APPLICATION_ID:
            raise ValueError("Application ID not found in environment variables")
            
        # Check welcome sound file
        if not os.path.exists(cls.WELCOME_SOUND_PATH):
            raise ValueError(f"Welcome sound file not found: {cls.WELCOME_SOUND_PATH}")
            
        # Check font file
        font_path = os.path.join('fonts', 'arabic.ttf')
        if not os.path.exists(font_path):
            raise ValueError(f"Arabic font file not found: {font_path}")
            
        # Create log directory if logging to file
        if cls.LOG_TO_FILE:
            os.makedirs(cls.LOG_DIR, exist_ok=True)
