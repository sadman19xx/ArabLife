import logging
from typing import Optional
import discord
from utils.logger import setup_logging

# Initialize logger at module level
_logger = setup_logging(
    None,  # We'll update this with the bot instance later
    error_log_channel=1327648816874262549,
    audit_log_channel=1286684861234417704
)

def get_logger():
    """Get the current logger instance"""
    return _logger

def update_logger(bot: Optional[discord.Client] = None):
    """Update the logger with a bot instance"""
    global _logger
    _logger = setup_logging(
        bot,
        error_log_channel=1327648816874262549,
        audit_log_channel=1286684861234417704
    )
