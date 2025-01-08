import logging
import discord

class RoleLogFilter(logging.Filter):
    """Filter for role-related logs"""
    def filter(self, record):
        return "Role" in record.getMessage()

class GeneralLogFilter(logging.Filter):
    """Filter for general logs"""
    def filter(self, record):
        return "Role" not in record.getMessage()

class DiscordLogHandler(logging.Handler):
    """Custom handler to send logs to Discord channels"""
    def __init__(self, bot, channel_id):
        super().__init__()
        self.bot = bot
        self.channel_id = channel_id

    async def send_log(self, message):
        channel = self.bot.get_channel(self.channel_id)
        if channel:
            await channel.send(message)

    def emit(self, record):
        log_entry = self.format(record)
        self.bot.loop.create_task(self.send_log(log_entry))

def setup_logging(bot, role_channel_id, audit_channel_id):
    """Setup logging configuration"""
    logger = logging.getLogger('discord')
    logger.setLevel(logging.INFO)

    # Create handlers
    role_audit_handler = DiscordLogHandler(bot, role_channel_id)
    audit_log_handler = DiscordLogHandler(bot, audit_channel_id)

    # Apply filters
    role_audit_handler.addFilter(RoleLogFilter())
    audit_log_handler.addFilter(GeneralLogFilter())

    # Set formatter
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    role_audit_handler.setFormatter(formatter)
    audit_log_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(role_audit_handler)
    logger.addHandler(audit_log_handler)

    return logger
