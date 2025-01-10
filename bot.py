import discord
from discord.ext import commands
from discord import app_commands
import logging
import os
import asyncio
import aiosqlite
import sys
import traceback
from datetime import datetime
from typing import Optional, Dict, List
from config import Config
from utils.logger import setup_logging
from utils.database import db

# Ensure database directory exists
os.makedirs(os.path.dirname(db.db_path), exist_ok=True)

# Set up intents with all privileges
intents = discord.Intents.all()

class ArabLifeBot(commands.Bot):
    """Custom bot class with additional functionality"""
    
    def __init__(self):
        super().__init__(
            command_prefix=self.get_prefix,
            intents=intents,
            case_insensitive=True,
            strip_after_prefix=True,
            allowed_mentions=discord.AllowedMentions(
                users=True,
                roles=False,
                everyone=False,
                replied_user=True
            )
        )
        
        # Initialize bot state
        self.uptime = None
        self.prefixes = {}
        self.cog_load_order = []
        self.cog_dependencies = {
            'cogs.leveling_commands': ['utils.database'],
            'cogs.automod_commands': ['utils.database'],
            'cogs.ticket_commands': ['utils.database'],
            'cogs.custom_commands': ['utils.database']
        }
        
        # List of cogs to load
        self.initial_extensions = [
            'cogs.role_commands',
            'cogs.voice_commands',
            'cogs.status_commands',
            'cogs.help_commands',
            'cogs.ticket_commands',
            'cogs.welcome_commands',
            'cogs.security_commands',
            'cogs.leveling_commands',
            'cogs.automod_commands',
            'cogs.custom_commands'
        ]
        
        # Set up error handlers
        self.tree.on_error = self.on_app_command_error
        
    async def get_prefix(self, message: discord.Message) -> str:
        """Get the prefix for the guild"""
        # DMs use default prefix
        if not message.guild:
            return "!"
            
        # Return cached prefix if available
        if message.guild.id in self.prefixes:
            return self.prefixes[message.guild.id]
            
        # Get prefix from database
        async with aiosqlite.connect(db.db_path) as conn:
            async with conn.execute(
                "SELECT prefix FROM bot_settings WHERE guild_id = ?",
                (str(message.guild.id),)
            ) as cursor:
                result = await cursor.fetchone()
                
        # Cache and return the prefix
        prefix = result[0] if result else "!"
        self.prefixes[message.guild.id] = prefix
        return prefix

    async def load_extension_with_dependencies(self, extension: str) -> None:
        """Load an extension after its dependencies"""
        if extension in self.cog_load_order:
            return
            
        # Load dependencies first
        if extension in self.cog_dependencies:
            for dependency in self.cog_dependencies[extension]:
                await self.load_extension_with_dependencies(dependency)
                
        try:
            await self.load_extension(extension)
            self.cog_load_order.append(extension)
            print(f'Loaded extension: {extension}')
        except Exception as e:
            print(f'Failed to load extension {extension}: {str(e)}')
            traceback.print_exc()

    async def setup_hook(self):
        """Initialize bot setup"""
        # Initialize database
        await db.init()
        
        # Load extensions in dependency order
        for extension in self.initial_extensions:
            await self.load_extension_with_dependencies(extension)

        # Register persistent views for tickets
        from cogs.ticket_commands import TicketView, StaffView
        self.add_view(TicketView())
        self.add_view(StaffView())
        
        # Sync commands with guild
        if Config.GUILD_ID:
            guild = discord.Object(id=Config.GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print("Successfully synced commands to guild!")

    async def on_ready(self):
        """Event triggered when the bot is ready"""
        if not self.uptime:
            self.uptime = datetime.utcnow()
            
        print(f'Logged in as {self.user.name}')
        print(f'Bot ID: {self.user.id}')
        print(f'Discord.py Version: {discord.__version__}')
        print(f'Uptime: {self.uptime}')
        print('------')

        # Setup logging
        logger = setup_logging(self, Config.ROLE_ACTIVITY_LOG_CHANNEL_ID, Config.AUDIT_LOG_CHANNEL_ID)

        # Set default status
        activity = discord.Activity(type=discord.ActivityType.watching, name="you my love")
        await self.change_presence(activity=activity)

        # Initialize database for each guild
        for guild in self.guilds:
            async with aiosqlite.connect(db.db_path) as conn:
                # Insert guild if not exists
                await conn.execute("""
                    INSERT OR IGNORE INTO guilds (id, name, owner_id, member_count)
                    VALUES (?, ?, ?, ?)
                """, (str(guild.id), guild.name, str(guild.owner_id), guild.member_count))
                
                # Insert default bot settings if not exists
                await conn.execute("""
                    INSERT OR IGNORE INTO bot_settings (guild_id, prefix)
                    VALUES (?, ?)
                """, (str(guild.id), "!"))
                
                await conn.commit()

    async def on_guild_join(self, guild: discord.Guild):
        """Event triggered when the bot joins a new guild"""
        # Initialize database for new guild
        async with aiosqlite.connect(db.db_path) as conn:
            await conn.execute("""
                INSERT OR IGNORE INTO guilds (id, name, owner_id, member_count)
                VALUES (?, ?, ?, ?)
            """, (str(guild.id), guild.name, str(guild.owner_id), guild.member_count))
            
            await conn.execute("""
                INSERT OR IGNORE INTO bot_settings (guild_id, prefix)
                VALUES (?, ?)
            """, (str(guild.id), "!"))
            
            await conn.commit()

        # Sync commands to the new guild
        if Config.GUILD_ID and guild.id == Config.GUILD_ID:
            guild_obj = discord.Object(id=guild.id)
            self.tree.copy_global_to(guild=guild_obj)
            await self.tree.sync(guild=guild_obj)
            print(f"Synced commands to new guild: {guild.name}")

    async def on_error(self, event_method: str, *args, **kwargs):
        """Global error handler for events"""
        exc_info = sys.exc_info()
        traceback.print_exception(*exc_info)
        
        # Log to error channel if configured
        if hasattr(Config, 'ERROR_LOG_CHANNEL_ID'):
            channel = self.get_channel(Config.ERROR_LOG_CHANNEL_ID)
            if channel:
                error_msg = f"```py\nEvent: {event_method}\n"
                error_msg += "".join(traceback.format_exception(*exc_info))
                error_msg += "```"
                
                try:
                    await channel.send(error_msg[:2000])  # Discord message limit
                except:
                    pass

    async def on_command_error(self, ctx, error):
        """Global error handler for command errors"""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send('*لا تملك الصلاحية لأستخدام هذه الامر.*')
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('*يرجى تقديم جميع المعطيات المطلوبة.*')
        elif isinstance(error, commands.BadArgument):
            await ctx.send('*معطيات غير صالحة.*')
        elif isinstance(error, app_commands.CommandInvokeError):
            await ctx.send('*حدث خطأ أثناء تنفيذ الأمر. يرجى المحاولة مرة أخرى.*')
            logging.error(f"App command error: {error}", exc_info=True)
        elif isinstance(error, commands.CommandNotFound):
            # Check for custom command
            if ctx.guild:
                async with aiosqlite.connect(db.db_path) as conn:
                    async with conn.execute(
                        "SELECT response FROM custom_commands WHERE guild_id = ? AND name = ?",
                        (str(ctx.guild.id), ctx.invoked_with.lower())
                    ) as cursor:
                        result = await cursor.fetchone()
                        if result:
                            await ctx.send(result[0])
                            return
        else:
            logging.error(f"An unexpected error occurred: {error}", exc_info=True)
            await ctx.send('*حدث خطأ غير متوقع. ارجو التواصل مع إدارة الديسكورد وتقديم تفاصيل الأمر.*')

    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Global error handler for application commands"""
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"*يرجى الانتظار {error.retry_after:.2f} ثانية قبل استخدام هذا الأمر مرة أخرى.*",
                ephemeral=True
            )
        elif isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "*لا تملك الصلاحية لأستخدام هذه الامر.*",
                ephemeral=True
            )
        else:
            logging.error(f"App command error: {error}", exc_info=True)
            await interaction.response.send_message(
                "*حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى.*",
                ephemeral=True
            )

    async def close(self):
        """Cleanup when bot is shutting down"""
        print("Bot is shutting down...")
        
        # Close database connections
        await db.close()
        
        # Call parent close
        await super().close()

async def main():
    """Main function to run the bot"""
    # Validate configuration
    try:
        Config.validate_config()
    except ValueError as e:
        if "Welcome sound file not found" in str(e) or "welcome.mp3" in str(e):
            # Ignore welcome sound file errors
            pass
        else:
            print(f"Configuration error: {str(e)}")
            return

    # Create and run bot
    try:
        async with ArabLifeBot() as bot:
            await bot.start(Config.TOKEN)
    except Exception as e:
        print(f"Failed to start bot: {str(e)}")
        traceback.print_exc()

# Run the bot
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        traceback.print_exc()
