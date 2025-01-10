import discord
from discord.ext import commands
from discord import app_commands
from discord.ext.commands import Cog
import logging
from config import Config

logger = logging.getLogger('discord')

class StatusCommands(Cog):
    """Cog for bot status commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.activity_types = {
            "playing": discord.ActivityType.playing,
            "streaming": discord.ActivityType.streaming,
            "listening": discord.ActivityType.listening,
            "watching": discord.ActivityType.watching,
            "competing": discord.ActivityType.competing,
        }

    def _validate_status(self, activity_type: str, message: str) -> bool:
        """Validate status parameters"""
        # Check activity type
        if activity_type.lower() not in self.activity_types:
            return False
            
        # Check message length
        if len(message) > Config.MAX_STATUS_LENGTH:
            return False
            
        # Check for blacklisted words
        if any(word.lower() in message.lower() for word in Config.BLACKLISTED_WORDS if word):
            return False
            
        return True

    @app_commands.command(
        name="setstatus",
        description="Change the bot's status"
    )
    @app_commands.describe(
        activity_type="Type of activity (playing, streaming, listening, watching, competing)",
        message="Status message to display"
    )
    @app_commands.choices(activity_type=[
        app_commands.Choice(name="Playing", value="playing"),
        app_commands.Choice(name="Streaming", value="streaming"),
        app_commands.Choice(name="Listening", value="listening"),
        app_commands.Choice(name="Watching", value="watching"),
        app_commands.Choice(name="Competing", value="competing")
    ])
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(1, Config.STATUS_COMMAND_COOLDOWN)
    async def set_status(self, interaction: discord.Interaction, activity_type: str, message: str):
        """Change the bot's status dynamically"""
        # Validate input
        if not self._validate_status(activity_type, message):
            await interaction.response.send_message(
                "❌ *نوع النشاط غير صالح أو الرسالة تحتوي على كلمات محظورة.*",
                ephemeral=True
            )
            return

        try:
            activity = discord.Activity(
                type=self.activity_types[activity_type.lower()], 
                name=message
            )
            await self.bot.change_presence(activity=activity)
            await interaction.response.send_message(
                f"✅ *تم تغيير الحالة الى: {activity_type.capitalize()} {message}*"
            )
            logger.info(f"Status changed to: {activity_type.capitalize()} {message} by {interaction.user.name}#{interaction.user.discriminator}")
            
        except discord.InvalidArgument:
            await interaction.response.send_message(
                "❌ *معطيات غير صالحة.*",
                ephemeral=True
            )
            logger.error(f"Invalid status parameters: type={activity_type}, message={message}")
            
        except Exception as e:
            await interaction.response.send_message(
                "❌ *حدث خطأ أثناء تغيير الحالة.*",
                ephemeral=True
            )
            logger.error(f"Error changing status: {str(e)}")

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Error handler for application commands"""
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"*الرجاء الانتظار {error.retry_after:.1f} ثواني.*",
                ephemeral=True
            )
        elif isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "*لا تملك الصلاحية لأستخدام هذه الامر.*",
                ephemeral=True
            )
        else:
            logger.error(f"Status command error: {str(error)}")
            await interaction.response.send_message(
                "*حدث خطأ غير متوقع.*",
                ephemeral=True
            )

async def setup(bot):
    """Setup function for loading the cog"""
    # Create cog instance
    cog = StatusCommands(bot)
    
    # Add cog to bot
    await bot.add_cog(cog)
    
    try:
        # Register app commands to guild
        guild = discord.Object(id=Config.GUILD_ID)
        bot.tree.add_command(cog.set_status, guild=guild)
        print("Registered status commands to guild")
    except Exception as e:
        print(f"Failed to register status commands: {e}")
