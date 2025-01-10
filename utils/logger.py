import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional
import discord

class DiscordHandler(logging.Handler):
    """Custom logging handler that sends logs to Discord channels"""
    
    def __init__(self, bot, channel_id: int):
        super().__init__()
        self.bot = bot
        self.channel_id = channel_id
        self.queue = []
        self.ready = False

    def emit(self, record):
        """Emit a log record"""
        if not self.ready:
            self.queue.append(record)
            return

        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            return

        try:
            # Format the record
            msg = self.format(record)
            
            # Create embed for better formatting
            embed = discord.Embed(
                description=f"```{msg}```",
                color=self._get_color(record.levelno),
                timestamp=datetime.utcnow()
            )
            embed.set_author(name=f"Log: {record.levelname}")
            
            # Add error traceback if exists
            if record.exc_info:
                tb = self.formatter.formatException(record.exc_info)
                if len(tb) > 1024:  # Discord embed field value limit
                    tb = tb[:1021] + "..."
                embed.add_field(name="Traceback", value=f"```py\n{tb}```", inline=False)

            # Send asynchronously using bot's loop
            self.bot.loop.create_task(channel.send(embed=embed))
            
        except Exception:
            self.handleError(record)

    def _get_color(self, level: int) -> discord.Color:
        """Get color based on log level"""
        if level >= logging.ERROR:
            return discord.Color.red()
        elif level >= logging.WARNING:
            return discord.Color.gold()
        elif level >= logging.INFO:
            return discord.Color.blue()
        return discord.Color.green()

class CustomFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    COLORS = {
        'DEBUG': '\033[37m',  # White
        'INFO': '\033[36m',   # Cyan
        'WARNING': '\033[33m', # Yellow
        'ERROR': '\033[31m',  # Red
        'CRITICAL': '\033[1;31m'  # Bold Red
    }
    RESET = '\033[0m'
    
    def __init__(self, *args, use_colors: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_colors = use_colors

    def format(self, record):
        """Format log record with optional colors"""
        # Save original values
        orig_msg = record.msg
        orig_levelname = record.levelname
        
        if self.use_colors:
            color = self.COLORS.get(record.levelname, self.RESET)
            record.msg = f"{color}{record.msg}{self.RESET}"
            record.levelname = f"{color}{record.levelname}{self.RESET}"
        
        # Format with modified values
        result = super().format(record)
        
        # Restore original values
        record.msg = orig_msg
        record.levelname = orig_levelname
        
        return result

def setup_logging(bot, role_log_channel_id: Optional[int] = None, audit_log_channel_id: Optional[int] = None) -> logging.Logger:
    """Set up logging configuration"""
    # Create logs directory
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger('discord')
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    logger.handlers = []
    
    # Log format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Console handler with colors (if supported)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        CustomFormatter(
            log_format,
            date_format,
            use_colors=sys.platform != 'win32' or 'ANSICON' in os.environ
        )
    )
    logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'bot.log'),
        maxBytes=10_000_000,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    logger.addHandler(file_handler)
    
    # Discord channel handlers
    if role_log_channel_id:
        role_handler = DiscordHandler(bot, role_log_channel_id)
        role_handler.setFormatter(logging.Formatter('%(message)s'))
        role_handler.setLevel(logging.INFO)
        logger.addHandler(role_handler)
        
    if audit_log_channel_id:
        audit_handler = DiscordHandler(bot, audit_log_channel_id)
        audit_handler.setFormatter(logging.Formatter('%(message)s'))
        audit_handler.setLevel(logging.WARNING)
        logger.addHandler(audit_handler)
    
    # Mark Discord handlers as ready
    for handler in logger.handlers:
        if isinstance(handler, DiscordHandler):
            handler.ready = True
            
            # Send queued messages
            while handler.queue:
                record = handler.queue.pop(0)
                handler.emit(record)
    
    return logger

class LoggerMixin:
    """Mixin to add logging capabilities to a class"""
    
    @property
    def log(self) -> logging.Logger:
        """Get logger for the class"""
        if not hasattr(self, '_log'):
            self._log = logging.getLogger(f'discord.{self.__class__.__name__}')
        return self._log
