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
    WELCOME_VOICE_CHANNEL_ID = int(os.getenv('WELCOME_VOICE_CHANNEL_ID', '1309595750878937240'))
    WELCOME_CHANNEL_ID = int(os.getenv('WELCOME_CHANNEL_ID', '0'))
    
    # Welcome Message settings
    WELCOME_MESSAGE = os.getenv('WELCOME_MESSAGE', 'Welcome {user} to {server}! 🎉')
    GOODBYE_MESSAGE = os.getenv('GOODBYE_MESSAGE', 'Goodbye {user}, we hope to see you again! 👋')
    WELCOME_EMBED_COLOR = int(os.getenv('WELCOME_EMBED_COLOR', '0x2ecc71'), 16)
    WELCOME_EMBED_TITLE = os.getenv('WELCOME_EMBED_TITLE', 'Welcome to {server}!')
    WELCOME_EMBED_DESCRIPTION = os.getenv('WELCOME_EMBED_DESCRIPTION', 'Welcome {user} to our community!\n\nMember Count: {member_count}')
    
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
    MAX_MENTIONS = int(os.getenv('MAX_MENTIONS', '5'))
    RAID_PROTECTION = os.getenv('RAID_PROTECTION', 'true').lower() == 'true'
    MIN_ACCOUNT_AGE = int(os.getenv('MIN_ACCOUNT_AGE', '7'))  # days
    ALLOWED_DOMAINS = os.getenv('ALLOWED_DOMAINS', 'discord.com,discord.gg').split(',')
    SPAM_DETECTION = os.getenv('SPAM_DETECTION', 'true').lower() == 'true'
    AUTO_TIMEOUT_DURATION = int(os.getenv('AUTO_TIMEOUT_DURATION', '3600'))  # seconds
    
    # Visa settings
    VISA_IMAGE_URL = os.getenv('VISA_IMAGE_URL', 'https://i.imgur.com/your_image_id.png')
    
    # Ticket settings
    TICKET_STAFF_ROLE_ID = int(os.getenv('TICKET_STAFF_ROLE_ID', '0'))  # Role that can see tickets
    TICKET_CATEGORY_ID = int(os.getenv('TICKET_CATEGORY_ID', '0'))  # Category to create tickets in
    TICKET_LOG_CHANNEL_ID = int(os.getenv('TICKET_LOG_CHANNEL_ID', '0'))  # Channel to log ticket actions
    
    # Department Role IDs
    PLAYER_REPORT_ROLE_ID = int(os.getenv('PLAYER_REPORT_ROLE_ID', '0'))  # Staff for player reports
    HEALTH_DEPT_ROLE_ID = int(os.getenv('HEALTH_DEPT_ROLE_ID', '0'))  # Health department staff
    INTERIOR_DEPT_ROLE_ID = int(os.getenv('INTERIOR_DEPT_ROLE_ID', '0'))  # Interior department staff
    FEEDBACK_ROLE_ID = int(os.getenv('FEEDBACK_ROLE_ID', '0'))  # Staff for feedback/suggestions
    
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

        # Validate ticket settings if staff role is set
        if cls.TICKET_STAFF_ROLE_ID != 0:
            if cls.TICKET_CATEGORY_ID == 0:
                raise ValueError("Ticket category ID must be set if using ticket system")
            if cls.TICKET_LOG_CHANNEL_ID == 0:
                raise ValueError("Ticket log channel ID must be set if using ticket system")
