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
            
            # If bot is ready, send immediately
            if self.bot.is_ready():
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
        if not self.bot.is_ready():
            return
            
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            return
            
        while self.queue:
            msg = self.queue.pop(0)
            self.bot.loop.create_task(channel.send(f"```\n{msg}\n```"))

class RoleActivityHandler(logging.Handler):
    """Custom logging handler for role-related activity"""
    
    def __init__(self, bot: discord.Client, channel_id: int):
        super().__init__()
        self.bot = bot
        self.channel_id = channel_id
        
    def emit(self, record: logging.LogRecord):
        """Emit a role activity log record to Discord"""
        if not self.bot.is_ready():
            return
            
        try:
            channel = self.bot.get_channel(self.channel_id)
            if channel:
                embed = discord.Embed(
                    title="Role Update",
                    description=self.format(record),
                    color=discord.Color.blue()
                )
                self.bot.loop.create_task(channel.send(embed=embed))
        except Exception as e:
            print(f"Failed to log role activity: {e}", file=sys.stderr)

def setup_logging(
    bot: discord.Client,
    role_log_channel: Optional[int] = None,
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
    
    # File handler
    if Config.LOG_TO_FILE:
        os.makedirs(Config.LOG_DIR, exist_ok=True)
        file_handler = RotatingFileHandler(
            filename=os.path.join(Config.LOG_DIR, 'bot.log'),
            maxBytes=5_000_000,  # 5 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(Config.LOG_FORMAT))
        logger.addHandler(file_handler)
    
    # Discord channel handlers
    if audit_log_channel:
        discord_handler = DiscordHandler(bot, audit_log_channel)
        discord_handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(discord_handler)
    
    if role_log_channel:
        role_handler = RoleActivityHandler(bot, role_log_channel)
        role_handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(role_handler)
    
    return logger
