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
    
    # Welcome settings
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
    
    # Leveling settings
    XP_PER_MESSAGE = int(os.getenv('XP_PER_MESSAGE', 15))
    XP_COOLDOWN = int(os.getenv('XP_COOLDOWN', 60))
    LEVEL_UP_CHANNEL_ID = os.getenv('LEVEL_UP_CHANNEL_ID')
    LEVEL_UP_MESSAGE = os.getenv('LEVEL_UP_MESSAGE', '🎉 {user} has reached level {level}!')
    
    # Health check settings
    HEALTH_CHECK_HOST = os.getenv('HEALTH_CHECK_HOST', '127.0.0.1')
    HEALTH_CHECK_PORT = int(os.getenv('HEALTH_CHECK_PORT', 8080))
    HEALTH_CHECK_METRICS_COOLDOWN = int(os.getenv('HEALTH_CHECK_METRICS_COOLDOWN', 60))
    
    # Blacklisted words/domains
    BLACKLISTED_WORDS = os.getenv('BLACKLISTED_WORDS', '').split(',')
    ALLOWED_DOMAINS = os.getenv('ALLOWED_DOMAINS', 'discord.com,discord.gg').split(',')
    
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
