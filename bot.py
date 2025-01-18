import discord
from discord.ext import commands
import logging
import os
import asyncio
from config import Config
from utils.logger import setup_logging

# Set up logging before anything else
global logger
logger = setup_logging(
    None,  # We'll update this with the bot instance later
    error_log_channel=1327648816874262549,
    audit_log_channel=1286684861234417704
)

# Set up intents with required privileges
intents = discord.Intents.default()
intents.members = True  # Required for on_member_join event
intents.voice_states = True  # Required for voice channel events and functionality

class ArabLifeBot(commands.Bot):
    """Custom bot class for ArabLife Discord server functionality"""
    
    def __init__(self) -> None:
        super().__init__(
            command_prefix='!',  # Add command prefix for traditional commands
            intents=intents,
            case_insensitive=True  # Make commands case-insensitive
        )
        
        # List of cogs to load (only existing cogs)
        self.initial_extensions = [
            'cogs.welcome_commands',
            'cogs.application_commands',
            'cogs.help_commands',
            'cogs.announcement_commands',
            'cogs.role_commands',
            'cogs.status_commands'
        ]
        
        # Clear existing commands to remove stale ones
        self._clear_commands = True

    async def setup_hook(self) -> None:
        """Initialize bot setup"""
        # Clear existing commands if requested
        if self._clear_commands:
            self.tree.clear_commands(guild=None)
            logger.info('Cleared all existing commands')
            
        # Configure voice settings
        discord.VoiceClient.warn_nacl = False
        discord.VoiceClient.default_timeout = Config.VOICE_TIMEOUT
        discord.VoiceClient.default_reconnect = True
        
        # Load extensions
        try:
            for extension in self.initial_extensions:
                await self.load_extension(extension)
                logger.info(f'Loaded {extension}')
        except Exception as e:
            logger.error(f'Failed to load extensions: {str(e)}')

    async def on_error(self, event_method: str, *args, **kwargs) -> None:
        """Global error handler for all events"""
        logger.error(f'Error in {event_method}: {args} {kwargs}')
        await super().on_error(event_method, *args, **kwargs)

    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
        """Error handler for application commands"""
        try:
            if isinstance(error, discord.app_commands.CommandInvokeError):
                error = error.original

            if isinstance(error, discord.NotFound) and error.code == 10062:
                # Interaction has expired - ignore this error
                return
            
            error_message = f"An error occurred: {str(error)}"
            
            try:
                if interaction.response.is_done():
                    await interaction.followup.send(error_message, ephemeral=True)
                else:
                    await interaction.response.send_message(error_message, ephemeral=True)
            except discord.NotFound:
                # If we can't respond to the interaction, log it
                logger.error(f"Failed to respond to interaction: {error_message}")
                
        except Exception as e:
            logger.error(f"Error in error handler: {str(e)}")

    async def on_ready(self) -> None:
        """Event triggered when the bot is ready"""
        logger.info('='*50)
        logger.info('             ARABLIFE BOT IS UP')
        logger.info('='*50)
        logger.info(f'Logged in as: {self.user.name}')
        logger.info(f'Bot ID: {self.user.id}')
        logger.info(f'Start Time: {discord.utils.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}')
        
        # Set the default status when the bot starts
        activity = discord.Activity(type=discord.ActivityType.watching, name="ArabLife")
        await self.change_presence(activity=activity)
        
        # Sync commands with Discord
        try:
            guild = discord.Object(id=Config.GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logger.info('Successfully synced application commands')
        except Exception as e:
            logger.error(f'Failed to sync commands: {str(e)}')
            
        logger.info('------')
        
        # Update logger with bot instance
        logger = setup_logging(
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
        logger.error(f"Configuration error: {str(e)}")
        return

    # Create and run bot
    try:
        async with ArabLifeBot() as bot:
            await bot.start(Config.TOKEN)
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}")

# Run the bot
if __name__ == "__main__":
    try:
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}")
