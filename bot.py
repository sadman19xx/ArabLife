import discord
from discord.ext import commands
import logging
import os
from config import Config
from utils.logger import setup_logging

# Set up intents with required privileges
intents = discord.Intents.default()
intents.members = True
intents.voice_states = True  # Required for voice functionality

class ArabLifeBot(commands.Bot):
    """Custom bot class for welcome voice functionality"""
    
    def __init__(self) -> None:
        super().__init__(
            command_prefix="!",  # Simple static prefix since we don't need command handling
            intents=intents,
            case_insensitive=True
        )
        
        # List of cogs to load
        self.initial_extensions = [
            'cogs.welcome_commands',
            'cogs.application_commands',
            'cogs.help_commands'
        ]

    async def setup_hook(self) -> None:
        """Initialize bot setup"""
        # Load extensions
        try:
            await self.load_extension('cogs.welcome_commands')
            print('Loaded welcome commands')
            await self.load_extension('cogs.application_commands')
            print('Loaded application commands')
            await self.load_extension('cogs.help_commands')
            print('Loaded help commands')
        except Exception as e:
            print(f'Failed to load extensions: {str(e)}')

    async def on_ready(self) -> None:
        """Event triggered when the bot is ready"""
        print(f'Logged in as {self.user.name}')
        print(f'Bot ID: {self.user.id}')
        
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
