import discord
from discord.ext import commands
import logging
import os
from config import Config
from utils.logger import setup_logging

# Disable unnecessary discord.py logging
for logger_name in ['discord', 'discord.client', 'discord.gateway', 'discord.http', 'discord.shard']:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.CRITICAL)  # Only show critical errors

# Set up intents with required privileges
intents = discord.Intents.default()
intents.members = True  # Required for on_member_join event
intents.voice_states = True  # Required for voice channel events and functionality
intents.message_content = True  # Required for legacy commands like !testwelcome

class ArabLifeBot(commands.Bot):
    """Custom bot class for ArabLife Discord server functionality"""
    
    def __init__(self) -> None:
        super().__init__(
            command_prefix="!",  # Prefix for legacy commands like !testwelcome
            intents=intents,
            case_insensitive=True  # Make commands case-insensitive
        )
        
        # List of cogs to load
        self.initial_extensions = [
            'cogs.welcome_commands',
            'cogs.application_commands',
            'cogs.help_commands',
            'cogs.voice_commands'
        ]
        
        # Don't clear existing commands
        self._clear_commands = False

    async def setup_hook(self) -> None:
        """Initialize bot setup"""
        # Clear existing commands if requested
        if self._clear_commands:
            self.tree.clear_commands(guild=None)
            print('Cleared all existing commands')
            
        # Load extensions
        try:
            for extension in self.initial_extensions:
                await self.load_extension(extension)
                print(f'Loaded {extension}')
        except Exception as e:
            print(f'Failed to load extensions: {str(e)}')

    async def on_ready(self) -> None:
        """Event triggered when the bot is ready"""
        print('='*50)
        print('             ARABLIFE BOT IS UP')
        print('='*50)
        print(f'Logged in as: {self.user.name}')
        print(f'Bot ID: {self.user.id}')
        print(f'Start Time: {discord.utils.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}')
        
        # Sync commands with Discord
        try:
            guild = discord.Object(id=Config.GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print('Successfully synced application commands')
        except Exception as e:
            print(f'Failed to sync commands: {str(e)}')
            
        print('------')
        
        # Set up logging with Discord channels
        setup_logging(
            self,
            error_log_channel=1327648816874262549,
            audit_log_channel=1286684861234417704
        )

async def main():
    """Main function to run the bot"""
    # Validate configuration
    try:
        Config.validate_config()
    except ValueError as e:
        print(f"Configuration error: {str(e)}")
        return

    # Create and run bot
    try:
        async with ArabLifeBot() as bot:
            await bot.start(Config.TOKEN)
    except Exception as e:
        print(f"Failed to start bot: {str(e)}")

# Run the bot
if __name__ == "__main__":
    try:
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print(f"Fatal error: {str(e)}")
