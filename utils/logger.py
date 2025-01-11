import logging
import os
import sys
import asyncio
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from collections import deque
import discord
from config import Config

class DiscordHandler(logging.Handler):
    """Custom logging handler that sends logs to Discord channels
    
    Attributes:
        bot: Discord bot instance
        channel_id: Discord channel ID for logging
        queue: Queue of log records to send when ready
        ready: Whether handler is ready to send messages
        rate_limit: Number of messages that can be sent per minute
        _last_sent: Timestamp of last message sent
    """
    
    def __init__(self, bot: discord.Client, channel_id: int, rate_limit: int = 60):
        super().__init__()
        self.bot = bot
        self.channel_id = channel_id
        self.queue: deque = deque(maxlen=1000)  # Limit queue size
        self.ready: bool = False
        self.rate_limit: int = rate_limit
        self._last_sent: Dict[int, float] = {}  # Channel ID -> Last send time
        self._lock = asyncio.Lock()

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record to Discord channel
        
        Args:
            record: Log record to emit
            
        Note:
            If handler is not ready, record is queued.
            Rate limiting is applied per channel.
        """
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
            self.bot.loop.create_task(self._send_log(channel, embed, record))
            
        except Exception as e:
            self.handleError(record)
            logger.error(f"Failed to emit Discord log: {e}")

    async def _send_log(self, channel: discord.TextChannel, embed: discord.Embed, record: logging.LogRecord) -> None:
        """Send log message with rate limiting
        
        Args:
            channel: Discord channel to send to
            embed: Formatted embed to send
            record: Original log record
        """
        async with self._lock:
            now = datetime.utcnow().timestamp()
            if self.channel_id in self._last_sent:
                time_diff = now - self._last_sent[self.channel_id]
                if time_diff < 1:  # Less than a second since last message
                    await asyncio.sleep(1 - time_diff)
            
            try:
                await channel.send(embed=embed)
                self._last_sent[self.channel_id] = datetime.utcnow().timestamp()
            except discord.HTTPException as e:
                logger.error(f"Failed to send Discord log: {e}")
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

def setup_logging(
    bot: discord.Client,
    role_log_channel_id: Optional[int] = None,
    audit_log_channel_id: Optional[int] = None
) -> logging.Logger:
    """Set up logging configuration
    
    Args:
        bot: Discord bot instance
        role_log_channel_id: Channel ID for role-related logs
        audit_log_channel_id: Channel ID for audit logs
        
    Returns:
        Configured logger instance
        
    Note:
        Uses settings from Config class for log configuration
    """
    # Create logs directory if logging to file
    if Config.LOG_TO_FILE:
        log_dir = os.path.dirname(Config.LOG_FILE_PATH)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger('discord')
    logger.setLevel(Config.LOG_LEVEL)
    
    # Remove existing handlers
    logger.handlers = []
    
    # Console handler with colors (if enabled)
    if Config.LOG_TO_CONSOLE:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(
            CustomFormatter(
                Config.LOG_FORMAT,
                datefmt='%Y-%m-%d %H:%M:%S',
                use_colors=sys.platform != 'win32' or 'ANSICON' in os.environ
            )
        )
        logger.addHandler(console_handler)
    
    # File handler with rotation (if enabled)
    if Config.LOG_TO_FILE:
        file_handler = RotatingFileHandler(
            Config.LOG_FILE_PATH,
            maxBytes=Config.LOG_MAX_BYTES,
            backupCount=Config.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(Config.LOG_FORMAT, datefmt='%Y-%m-%d %H:%M:%S'))
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
    """Mixin to add logging capabilities to a class
    
    Provides a 'log' property that returns a logger instance
    specific to the class.
    """
    
    @property
    def log(self) -> logging.Logger:
        """Get logger for the class
        
        Returns:
            Logger instance with class name
        """
        if not hasattr(self, '_log'):
            self._log = logging.getLogger(f'discord.{self.__class__.__name__}')
        return self._log
