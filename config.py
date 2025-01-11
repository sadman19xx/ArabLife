import os
import json
import shutil
from typing import Dict, List, Optional, Union, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def parse_int(value: Optional[str], default: int = 0) -> int:
    """Safely parse integer from environment variable"""
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default

def parse_float(value: Optional[str], default: float = 0.0) -> float:
    """Safely parse float from environment variable"""
    if not value:
        return default
    try:
        return float(value)
    except ValueError:
        return default

def parse_list(value: Optional[str], separator: str = ',') -> List[str]:
    """Safely parse list from environment variable"""
    if not value:
        return []
    return [item.strip() for item in value.split(separator) if item.strip()]

def parse_json(value: Optional[str], default: Any = None) -> Any:
    """Safely parse JSON from environment variable"""
    if not value:
        return default if default is not None else {}
    try:
        return json.loads(value)
    except json.JSONDecodeError as e:
        print(f"Warning: Failed to parse JSON: {e}")
        return default if default is not None else {}

def parse_bool(value: Optional[str], default: bool = False) -> bool:
    """Safely parse boolean from environment variable"""
    if not value:
        return default
    return value.lower() == 'true'

# Bot configuration
class Config:
    """Configuration class with type hints and safe parsing"""
    # Token and Guild settings
    TOKEN: Optional[str] = os.getenv('TOKEN')
    GUILD_ID: int = parse_int(os.getenv('GUILD_ID'))
    
    # Role settings
    ROLE_IDS_ALLOWED: List[int] = [parse_int(id_str) for id_str in parse_list(os.getenv('ROLE_IDS_ALLOWED')) if id_str]
    ROLE_ID_TO_GIVE: int = parse_int(os.getenv('ROLE_ID_TO_GIVE'))
    ROLE_ID_REMOVE_ALLOWED: int = parse_int(os.getenv('ROLE_ID_REMOVE_ALLOWED'))
    
    # Channel IDs
    ROLE_ACTIVITY_LOG_CHANNEL_ID: int = parse_int(os.getenv('ROLE_ACTIVITY_LOG_CHANNEL_ID'))
    AUDIT_LOG_CHANNEL_ID: int = parse_int(os.getenv('AUDIT_LOG_CHANNEL_ID'))
    ERROR_LOG_CHANNEL_ID: int = parse_int(os.getenv('ERROR_LOG_CHANNEL_ID'), 0)
    WELCOME_VOICE_CHANNEL_ID: int = parse_int(os.getenv('WELCOME_VOICE_CHANNEL_ID'), 1309595750878937240)
    WELCOME_CHANNEL_ID: int = parse_int(os.getenv('WELCOME_CHANNEL_ID'), 0)
    
    # Welcome Message settings
    WELCOME_BACKGROUND_URL: str = os.getenv('WELCOME_BACKGROUND_URL', 'https://i.imgur.com/your_background.png')
    WELCOME_MESSAGE: str = os.getenv('WELCOME_MESSAGE', 'Welcome {user} to {server}! 🎉')
    GOODBYE_MESSAGE: str = os.getenv('GOODBYE_MESSAGE', 'Goodbye {user}, we hope to see you again! 👋')
    WELCOME_EMBED_COLOR: int = parse_int(os.getenv('WELCOME_EMBED_COLOR', '0x2ecc71'), 0x2ecc71)
    WELCOME_EMBED_TITLE: str = os.getenv('WELCOME_EMBED_TITLE', 'Welcome to {server}!')
    WELCOME_EMBED_DESCRIPTION: str = os.getenv('WELCOME_EMBED_DESCRIPTION', 'Welcome {user} to our community!\n\nMember Count: {member_count}')
    
    # Voice settings
    WELCOME_SOUND_PATH: Optional[str] = os.getenv('WELCOME_SOUND_PATH')
    DEFAULT_VOLUME: float = parse_float(os.getenv('DEFAULT_VOLUME'), 0.5)
    FFMPEG_PATH: Optional[str] = os.getenv('FFMPEG_PATH')
    
    # JSON settings
    ROLE_REWARDS: Dict[str, Any] = parse_json(os.getenv('ROLE_REWARDS'))
    CHANNEL_MULTIPLIERS: Dict[str, float] = parse_json(os.getenv('CHANNEL_MULTIPLIERS'))
    ROLE_MULTIPLIERS: Dict[str, float] = parse_json(os.getenv('ROLE_MULTIPLIERS'))
    
    # Command cooldowns (in seconds)
    ROLE_COMMAND_COOLDOWN: int = parse_int(os.getenv('ROLE_COMMAND_COOLDOWN'), 5)
    STATUS_COMMAND_COOLDOWN: int = parse_int(os.getenv('STATUS_COMMAND_COOLDOWN'), 10)
    SOUND_COMMAND_COOLDOWN: int = parse_int(os.getenv('SOUND_COMMAND_COOLDOWN'), 5)
    TICKET_COMMAND_COOLDOWN: int = parse_int(os.getenv('TICKET_COMMAND_COOLDOWN'), 30)
    
    # Security settings
    MAX_STATUS_LENGTH: int = parse_int(os.getenv('MAX_STATUS_LENGTH'), 100)
    BLACKLISTED_WORDS: List[str] = parse_list(os.getenv('BLACKLISTED_WORDS'))
    MAX_MENTIONS: int = parse_int(os.getenv('MAX_MENTIONS'), 5)
    RAID_PROTECTION: bool = parse_bool(os.getenv('RAID_PROTECTION'), True)
    MIN_ACCOUNT_AGE: int = parse_int(os.getenv('MIN_ACCOUNT_AGE'), 7)  # days
    ALLOWED_DOMAINS: List[str] = parse_list(os.getenv('ALLOWED_DOMAINS'), ',')
    SPAM_DETECTION: bool = parse_bool(os.getenv('SPAM_DETECTION'), True)
    AUTO_TIMEOUT_DURATION: int = parse_int(os.getenv('AUTO_TIMEOUT_DURATION'), 3600)  # seconds
    WARNING_THRESHOLD: int = parse_int(os.getenv('WARNING_THRESHOLD'), 3)
    WARNING_ACTION: str = os.getenv('WARNING_ACTION', 'timeout')  # timeout, kick, ban
    WARNING_DURATION: int = parse_int(os.getenv('WARNING_DURATION'), 3600)  # seconds
    WARNING_EXPIRE_DAYS: int = parse_int(os.getenv('WARNING_EXPIRE_DAYS'), 30)  # days until warnings expire
    EXEMPT_ROLES: List[int] = [parse_int(id_str) for id_str in parse_list(os.getenv('EXEMPT_ROLES')) if id_str]
    
    # AutoMod settings
    AUTOMOD_ENABLED: bool = parse_bool(os.getenv('AUTOMOD_ENABLED'), True)
    AUTOMOD_SPAM_THRESHOLD: int = parse_int(os.getenv('AUTOMOD_SPAM_THRESHOLD'), 5)
    AUTOMOD_SPAM_INTERVAL: int = parse_int(os.getenv('AUTOMOD_SPAM_INTERVAL'), 5)
    AUTOMOD_RAID_THRESHOLD: int = parse_int(os.getenv('AUTOMOD_RAID_THRESHOLD'), 10)
    AUTOMOD_RAID_INTERVAL: int = parse_int(os.getenv('AUTOMOD_RAID_INTERVAL'), 30)
    AUTOMOD_ACTION: str = os.getenv('AUTOMOD_ACTION', 'warn')  # warn, mute, kick, ban
    AUTOMOD_IGNORED_CHANNELS: List[int] = [parse_int(id_str) for id_str in parse_list(os.getenv('AUTOMOD_IGNORED_CHANNELS')) if id_str]
    AUTOMOD_IGNORED_ROLES: List[int] = [parse_int(id_str) for id_str in parse_list(os.getenv('AUTOMOD_IGNORED_ROLES')) if id_str]
    
    # Leveling settings
    LEVELING_ENABLED: bool = parse_bool(os.getenv('LEVELING_ENABLED'), True)
    XP_PER_MESSAGE: int = parse_int(os.getenv('XP_PER_MESSAGE'), 15)
    XP_COOLDOWN: int = parse_int(os.getenv('XP_COOLDOWN'), 60)
    LEVEL_UP_CHANNEL_ID: Optional[int] = parse_int(os.getenv('LEVEL_UP_CHANNEL_ID'))
    LEVEL_UP_MESSAGE: str = os.getenv('LEVEL_UP_MESSAGE', 'Congratulations {user}! You reached level {level}!')
    ROLE_REWARDS: Dict[str, int] = parse_json(os.getenv('ROLE_REWARDS'), {})  # {level: role_id} pairs
    CHANNEL_MULTIPLIERS: Dict[str, float] = parse_json(os.getenv('CHANNEL_MULTIPLIERS'), {})  # {channel_id: multiplier}
    ROLE_MULTIPLIERS: Dict[str, float] = parse_json(os.getenv('ROLE_MULTIPLIERS'), {})  # {role_id: multiplier}
    
    # Visa settings
    VISA_IMAGE_URL: str = os.getenv('VISA_IMAGE_URL', 'https://i.imgur.com/your_image_id.png')
    
    # Ticket settings
    TICKET_STAFF_ROLE_ID: int = parse_int(os.getenv('TICKET_STAFF_ROLE_ID'), 0)  # Role that can see tickets
    TICKET_CATEGORY_ID: int = parse_int(os.getenv('TICKET_CATEGORY_ID'), 0)  # Category to create tickets in
    TICKET_LOG_CHANNEL_ID: int = parse_int(os.getenv('TICKET_LOG_CHANNEL_ID'), 0)  # Channel to log ticket actions
    TICKET_ARCHIVE_DAYS: int = parse_int(os.getenv('TICKET_ARCHIVE_DAYS'), 30)  # Days to keep closed tickets
    TICKET_CLOSE_DELAY: int = parse_int(os.getenv('TICKET_CLOSE_DELAY'), 5)  # Seconds to wait before deleting closed ticket
    TICKET_RATE_LIMIT: int = parse_int(os.getenv('TICKET_RATE_LIMIT'), 1)  # Maximum open tickets per user
    TICKET_AUTO_CLOSE_HOURS: int = parse_int(os.getenv('TICKET_AUTO_CLOSE_HOURS'), 72)  # Hours until inactive tickets auto-close
    
    # Department Role IDs
    PLAYER_REPORT_ROLE_ID: int = parse_int(os.getenv('PLAYER_REPORT_ROLE_ID'), 0)  # Staff for player reports
    HEALTH_DEPT_ROLE_ID: int = parse_int(os.getenv('HEALTH_DEPT_ROLE_ID'), 0)  # Health department staff
    INTERIOR_DEPT_ROLE_ID: int = parse_int(os.getenv('INTERIOR_DEPT_ROLE_ID'), 0)  # Interior department staff
    FEEDBACK_ROLE_ID: int = parse_int(os.getenv('FEEDBACK_ROLE_ID'), 0)  # Staff for feedback/suggestions
    
    # Logging settings
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE_PATH: str = os.getenv('LOG_FILE_PATH', 'logs/bot.log')
    LOG_FORMAT: str = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    LOG_MAX_BYTES: int = parse_int(os.getenv('LOG_MAX_BYTES'), 10485760)  # 10MB
    LOG_BACKUP_COUNT: int = parse_int(os.getenv('LOG_BACKUP_COUNT'), 5)
    LOG_TO_CONSOLE: bool = parse_bool(os.getenv('LOG_TO_CONSOLE'), True)
    LOG_TO_FILE: bool = parse_bool(os.getenv('LOG_TO_FILE'), True)
    
    @classmethod
    def validate_config(cls):
        """Validate required configuration values"""
        # Validate token first
        if not cls.TOKEN:
            raise ValueError("Discord bot token not set in .env file")
        
        # Basic token format validation (should be ~70 chars with 2 dots)
        if not cls.TOKEN.count('.') == 2 or len(cls.TOKEN) < 50:
            raise ValueError("Invalid Discord bot token format. Token should contain exactly two dots and be at least 50 characters long.")

        # Check other required fields
        required_fields = [
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
            
        # Validate role IDs
        if not cls.ROLE_IDS_ALLOWED or cls.ROLE_IDS_ALLOWED == ['']:
            raise ValueError("At least one allowed role ID must be configured")

        # Validate FFmpeg path
        if not cls.FFMPEG_PATH:
            # Default paths based on OS
            if os.name == 'nt':  # Windows
                default_paths = [
                    r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
                    r'C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe',
                    r'ffmpeg.exe'  # If in PATH
                ]
            else:  # Unix/Linux
                default_paths = [
                    '/usr/bin/ffmpeg',
                    '/usr/local/bin/ffmpeg',
                    'ffmpeg'  # If in PATH
                ]
                
            # Try to find ffmpeg in default locations
            for path in default_paths:
                if os.path.isfile(path) or shutil.which(path):
                    cls.FFMPEG_PATH = path
                    break
            else:
                if os.name == 'nt':
                    raise ValueError("FFmpeg not found. Please install FFmpeg and add it to PATH or set FFMPEG_PATH in .env")
                else:
                    raise ValueError("FFmpeg not found. Please install FFmpeg with: sudo apt install -y ffmpeg")
        else:
            # Validate custom path
            if not os.path.isfile(cls.FFMPEG_PATH) and not shutil.which(cls.FFMPEG_PATH):
                raise ValueError(f"FFmpeg not found at path: {cls.FFMPEG_PATH}")

        # Validate ticket settings if staff role is set
        if cls.TICKET_STAFF_ROLE_ID != 0:
            if cls.TICKET_CATEGORY_ID == 0:
                raise ValueError("Ticket category ID must be set if using ticket system")
            if cls.TICKET_LOG_CHANNEL_ID == 0:
                raise ValueError("Ticket log channel ID must be set if using ticket system")
            
        # Create logs directory if logging to file
        if cls.LOG_TO_FILE:
            log_dir = os.path.dirname(cls.LOG_FILE_PATH)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
