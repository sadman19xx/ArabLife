import discord
from discord.ext import commands
import logging
import os
import asyncio
from config import Config
from utils.logger import setup_logging

# Set up intents
intents = discord.Intents.default()
intents.members = True  # Required for role management
intents.message_content = True  # Required for commands
intents.voice_states = True  # Required for voice functionality

class ArabLifeBot(commands.Bot):
    """Custom bot class with additional functionality"""
    
    def __init__(self):
        super().__init__(command_prefix='/', intents=intents)
        self.initial_extensions = [
            'cogs.role_commands',
            'cogs.voice_commands',
            'cogs.status_commands'
        ]
        
    async def setup_hook(self):
        """A coroutine to be called to setup the bot, by default this is blank."""
        # Load extensions
        for extension in self.initial_extensions:
            try:
                await self.load_extension(extension)
                print(f'Loaded extension: {extension}')
            except Exception as e:
                print(f'Failed to load extension {extension}: {str(e)}')

    async def on_ready(self):
        """Event triggered when the bot is ready"""
        print(f'Logged in as {self.user.name}')

        # Setup logging
        logger = setup_logging(self, Config.ROLE_ACTIVITY_LOG_CHANNEL_ID, Config.AUDIT_LOG_CHANNEL_ID)

        # Set default status
        activity = discord.Activity(type=discord.ActivityType.watching, name="you my love")
        await self.change_presence(activity=activity)

        # Sync commands for the specific guild
        try:
            guild = discord.Object(id=Config.GUILD_ID)
            await self.tree.sync(guild=guild)
            
            guild_object = self.get_guild(Config.GUILD_ID)
            if guild_object:
                print(f"Successfully synced commands to guild: {guild_object.name}")
            else:
                print("Failed to fetch the guild object.")
        except Exception as e:
            print(f"Failed to sync commands: {str(e)}")

    async def on_command_error(self, ctx, error):
        """Global error handler for command errors"""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send('*لا تملك الصلاحية لأستخدام هذه الامر.*')
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('*يرجى تقديم جميع المعطيات المطلوبة.*')
        elif isinstance(error, commands.BadArgument):
            await ctx.send('*معطيات غير صالحة.*')
        elif isinstance(error, commands.CommandNotFound):
            # Ignore command not found errors
            pass
        else:
            # Log unexpected errors
            logging.error(f"An unexpected error occurred: {error}", exc_info=True)
            await ctx.send('*حدث خطأ غير متوقع. ارجو التواصل مع إدارة الديسكورد وتقديم تفاصيل الأمر.*')

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
    asyncio.run(main())
