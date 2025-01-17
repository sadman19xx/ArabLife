import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional
import discord
from config import Config

class LoggerMixin:
    """Mixin class to provide logging functionality to cogs"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def log_info(self, message: str):
        """Log an info message"""
        self.logger.info(message)
        
    def log_warning(self, message: str):
        """Log a warning message"""
        self.logger.warning(message)
        
    def log_error(self, message: str):
        """Log an error message"""
        self.logger.error(message)
        
    def log_debug(self, message: str):
        """Log a debug message"""
        self.logger.debug(message)
        
    async def log_to_channel(self, channel: discord.TextChannel, message: str):
        """Log a message to a Discord channel"""
        try:
            await channel.send(message)
        except Exception as e:
            self.log_error(f"Failed to log to channel {channel.id}: {e}")

class DiscordHandler(logging.Handler):
    """Custom logging handler that sends logs to a Discord channel"""
    
    def __init__(self, bot: discord.Client, channel_id: int):
        super().__init__()
        self.bot = bot
        self.channel_id = channel_id
        self.queue = []
        self.ready = False
        
    def emit(self, record: logging.LogRecord):
        """Emit a log record to Discord"""
        try:
            msg = self.format(record)
            
            # Always print to stderr for errors
            if record.levelno >= logging.ERROR:
                print(f"ERROR: {msg}", file=sys.stderr)
            
            # Only try Discord logging if bot exists and is ready
            if hasattr(self, 'bot') and self.bot and hasattr(self.bot, 'is_ready') and self.bot.is_ready():
                channel = self.bot.get_channel(self.channel_id)
                if channel:
                    # Split long messages
                    while len(msg) > 1900:  # Leave room for code block
                        split_msg = msg[:1900]
                        last_newline = split_msg.rfind('\n')
                        if last_newline != -1:
                            split_msg = msg[:last_newline]
                            msg = msg[last_newline+1:]
                        else:
                            msg = msg[1900:]
                        
                        self.bot.loop.create_task(
                            channel.send(f"```\n{split_msg}\n```")
                        )
                    
                    if msg:  # Send remaining message
                        self.bot.loop.create_task(
                            channel.send(f"```\n{msg}\n```")
                        )
            else:
                # Queue message for later if bot isn't ready
                self.queue.append(msg)
                
        except Exception as e:
            print(f"Failed to log to Discord: {e}", file=sys.stderr)

    def flush_queue(self):
        """Send queued messages once bot is ready"""
        try:
            # Only try Discord logging if bot exists and is ready
            if hasattr(self, 'bot') and self.bot and hasattr(self.bot, 'is_ready') and self.bot.is_ready():
                channel = self.bot.get_channel(self.channel_id)
                if channel:
                    while self.queue:
                        msg = self.queue.pop(0)
                        self.bot.loop.create_task(channel.send(f"```\n{msg}\n```"))
        except Exception as e:
            print(f"Failed to flush queue: {e}", file=sys.stderr)

class ErrorHandler(logging.Handler):
    """Custom logging handler for error messages"""
    
    def __init__(self, bot: discord.Client, channel_id: int):
        super().__init__()
        self.bot = bot
        self.channel_id = channel_id
        
    def emit(self, record: logging.LogRecord):
        """Emit an error log record to Discord"""
        try:
            # Always print to stderr for critical errors
            if record.levelno >= logging.ERROR:
                print(f"ERROR: {self.format(record)}", file=sys.stderr)
            
            # Only try Discord logging if bot is ready and connected
            if hasattr(self, 'bot') and self.bot and getattr(self.bot, 'is_ready', lambda: False)():
                channel = self.bot.get_channel(self.channel_id)
                if channel:
                    embed = discord.Embed(
                        title="⚠️ Error",
                        description=f"```\n{self.format(record)}\n```",
                        color=discord.Color.red(),
                        timestamp=discord.utils.utcnow()
                    )
                    self.bot.loop.create_task(channel.send(embed=embed))
        except Exception as e:
            print(f"Failed to log error: {e}", file=sys.stderr)

class AuditHandler(logging.Handler):
    """Custom logging handler for audit logs"""
    
    def __init__(self, bot: discord.Client, channel_id: int):
        super().__init__()
        self.bot = bot
        self.channel_id = channel_id
        self.important_events = {
            'ban', 'unban', 'kick'  # Only log critical moderation events
        }
        
    def emit(self, record: logging.LogRecord):
        """Emit an audit log record to Discord"""
        # Only log important events
        event_type = getattr(record, 'event_type', None)
        if not event_type or event_type not in self.important_events:
            return
            
        try:
            # Only try Discord logging if bot exists and is ready
            if hasattr(self, 'bot') and self.bot and hasattr(self.bot, 'is_ready') and self.bot.is_ready():
                channel = self.bot.get_channel(self.channel_id)
                if channel:
                    embed = discord.Embed(
                        title="📝 Audit Log",
                        description=self.format(record),
                        color=discord.Color.blue(),
                        timestamp=discord.utils.utcnow()
                    )
                    self.bot.loop.create_task(channel.send(embed=embed))
        except Exception as e:
            print(f"Failed to log audit event: {e}", file=sys.stderr)

def setup_logging(
    bot: discord.Client,
    error_log_channel: Optional[int] = None,
    audit_log_channel: Optional[int] = None
) -> logging.Logger:
    """Set up logging configuration"""
    
    # Create logger
    logger = logging.getLogger('discord')
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(Config.LOG_FORMAT))
    logger.addHandler(console_handler)
    
    # File handlers
    if Config.LOG_TO_FILE:
        os.makedirs(Config.LOG_DIR, exist_ok=True)
        
        # Main log file for all levels
        main_handler = RotatingFileHandler(
            filename=os.path.join(Config.LOG_DIR, 'arablife-bot.log'),
            maxBytes=5_000_000,  # 5 MB
            backupCount=5,
            encoding='utf-8'
        )
        main_handler.setFormatter(logging.Formatter(Config.LOG_FORMAT))
        logger.addHandler(main_handler)
        
        # Error log file for ERROR and above
        error_handler = RotatingFileHandler(
            filename=os.path.join(Config.LOG_DIR, 'arablife-bot.error.log'),
            maxBytes=5_000_000,  # 5 MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(Config.LOG_FORMAT))
        logger.addHandler(error_handler)
        
        # Debug log file for DEBUG level
        debug_handler = RotatingFileHandler(
            filename=os.path.join(Config.LOG_DIR, 'arablife-bot.debug.log'),
            maxBytes=5_000_000,  # 5 MB
            backupCount=5,
            encoding='utf-8'
        )
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(logging.Formatter(Config.LOG_FORMAT))
        logger.addHandler(debug_handler)
    
    # Discord channel handlers
    if error_log_channel:
        error_handler = ErrorHandler(bot, error_log_channel)
        error_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(message)s'))
        error_handler.setLevel(logging.ERROR)
        logger.addHandler(error_handler)
    
    if audit_log_channel:
        audit_handler = AuditHandler(bot, audit_log_channel)
        audit_handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(audit_handler)
    
    return logger
