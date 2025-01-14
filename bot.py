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
from typing import Optional, Dict, List, Union, Callable, Any
from collections import defaultdict
from config import Config
from utils.logger import setup_logging
from utils.database import db
from utils.health import HealthCheck

# Ensure directories exist
os.makedirs(os.path.dirname(db.db_path), exist_ok=True)
os.makedirs('logs', exist_ok=True)

# Set up intents with all privileges
intents = discord.Intents.all()
intents.message_content = True
intents.members = True
intents.presences = True

class ArabLifeBot(commands.Bot):
    """Custom bot class with additional functionality"""
    
    def __init__(self) -> None:
        # Initialize attributes with type hints
        self.uptime: Optional[datetime] = None
        self.prefixes: Dict[int, str] = {}
        self.cog_load_order: List[str] = []
        self.command_stats: Dict[str, int] = defaultdict(int)  # Track command usage
        self.error_count: int = 0  # Track error count
        self.db = db  # Make database accessible to cogs
        
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
        self.health_server = HealthCheck(
            self,
            host=Config.HEALTH_CHECK_HOST,
            port=Config.HEALTH_CHECK_PORT,
            metrics_cooldown=Config.HEALTH_CHECK_METRICS_COOLDOWN
        )  # Health check server
        
        # List of cogs to load
        self.initial_extensions = [
            'cogs.role_commands',
            'cogs.voice_commands',
            'cogs.status_commands',
            'cogs.help_commands',
            'cogs.ticket_commands',
            'cogs.welcome_commands',
            'cogs.security_commands',
            'cogs.automod_commands',
            'cogs.custom_commands',
            'cogs.fivem_commands'  # Add FiveM integration
        ]
        
        # Set up error handlers
        self.tree.on_error = self.on_app_command_error
        
    async def get_prefix(self, message: discord.Message) -> Union[str, List[str]]:
        """Get the prefix for the guild"""
        # DMs use default prefix
        if not message.guild:
            return "!"
            
        # Return cached prefix if available
        if message.guild.id in self.prefixes:
            return self.prefixes[message.guild.id]
            
        try:
            # Get prefix from database
            async with self.db.transaction() as cursor:
                await cursor.execute("""
                    SELECT prefix FROM bot_settings WHERE guild_id = ?
                """, (str(message.guild.id),))
                result = await cursor.fetchone()
                
            # Cache and return the prefix
            prefix = result[0] if result else "!"
            self.prefixes[message.guild.id] = prefix
            return prefix
        except Exception as e:
            logging.error(f"Error fetching prefix for guild {message.guild.id}: {e}")
            return "!"  # Fallback to default prefix on error

    async def setup_hook(self) -> None:
        """Initialize bot setup"""
        # Initialize database
        await self.db.init()
        
        # Start health check server
        await self.health_server.start()
        
        # Load extensions
        for extension in self.initial_extensions:
            try:
                await self.load_extension(extension)
                self.cog_load_order.append(extension)
                print(f'Loaded extension: {extension}')
            except Exception as e:
                print(f'Failed to load extension {extension}: {str(e)}')
                traceback.print_exc()

        # Register persistent views for tickets
        from cogs.ticket_commands import TicketView, StaffView
        self.add_view(TicketView())
        self.add_view(StaffView())
        
        # Sync commands with guild
        if Config.GUILD_ID:
            try:
                guild = discord.Object(id=Config.GUILD_ID)
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                print("Successfully synced commands to guild!")
            except discord.HTTPException as e:
                print(f"Failed to sync commands: {e}")
            except Exception as e:
                print(f"Unexpected error syncing commands: {e}")

    async def on_ready(self) -> None:
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
            try:
                async with self.db.transaction() as cursor:
                    # Insert guild if not exists
                    await cursor.execute("""
                        INSERT OR IGNORE INTO guilds (id, name, owner_id, member_count)
                        VALUES (?, ?, ?, ?)
                    """, (str(guild.id), guild.name, str(guild.owner_id), guild.member_count))
                    
                    # Insert default bot settings if not exists
                    await cursor.execute("""
                        INSERT OR IGNORE INTO bot_settings (guild_id, prefix)
                        VALUES (?, ?)
                    """, (str(guild.id), "!"))
            except Exception as e:
                logging.error(f"Failed to initialize database for guild {guild.id}: {e}")

        # Sync commands again after bot is ready
        if Config.GUILD_ID:
            try:
                guild = discord.Object(id=Config.GUILD_ID)
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                print("Successfully synced commands to guild after ready!")
            except Exception as e:
                print(f"Failed to sync commands after ready: {e}")

    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Event triggered when the bot joins a new guild"""
        try:
            # Initialize database for new guild
            async with self.db.transaction() as cursor:
                await cursor.execute("""
                    INSERT OR IGNORE INTO guilds (id, name, owner_id, member_count)
                    VALUES (?, ?, ?, ?)
                """, (str(guild.id), guild.name, str(guild.owner_id), guild.member_count))
                
                await cursor.execute("""
                    INSERT OR IGNORE INTO bot_settings (guild_id, prefix)
                    VALUES (?, ?)
                """, (str(guild.id), "!"))
        except Exception as e:
            logging.error(f"Failed to initialize database for new guild {guild.id}: {e}")
            return

        # Sync commands to the new guild
        if Config.GUILD_ID and guild.id == Config.GUILD_ID:
            guild_obj = discord.Object(id=guild.id)
            self.tree.copy_global_to(guild=guild_obj)
            await self.tree.sync(guild=guild_obj)
            print(f"Synced commands to new guild: {guild.name}")

    async def on_error(self, event_method: str, *args: Any, **kwargs: Any) -> None:
        """Global error handler for events"""
        self.error_count += 1
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

    async def on_command(self, ctx: commands.Context) -> None:
        """Track command usage"""
        self.command_stats[ctx.command.qualified_name] += 1
        await super().on_command(ctx)

    async def on_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """Global error handler for command errors"""
        self.error_count += 1
        
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
                async with self.db.transaction() as cursor:
                    await cursor.execute("""
                        SELECT response FROM custom_commands 
                        WHERE guild_id = ? AND name = ?
                    """, (str(ctx.guild.id), ctx.invoked_with.lower()))
                    result = await cursor.fetchone()
                    if result:
                        await ctx.send(result[0])
                        return
        else:
            logging.error(f"An unexpected error occurred: {error}", exc_info=True)
            await ctx.send('*حدث خطأ غير متوقع. ارجو التواصل مع إدارة الديسكورد وتقديم تفاصيل الأمر.*')

    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        """Global error handler for application commands"""
        self.error_count += 1
        
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

    async def close(self) -> None:
        """Cleanup when bot is shutting down"""
        print("Bot is shutting down...")
        
        # Close database connections
        await self.db.close()
        
        # Stop health check server
        await self.health_server.stop()
        
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
