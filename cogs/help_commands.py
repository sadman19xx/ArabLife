import discord
from discord.ext import commands
from discord.ext.commands import Cog
from discord import app_commands
import logging
from config import Config

logger = logging.getLogger('discord')

class HelpCommands(Cog):
    """Cog for help commands"""
    
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="help",
        description="Shows all available commands"
    )
    async def help_command(self, interaction: discord.Interaction):
        """Shows all available commands"""
        help_embed = discord.Embed(
            title="Available Commands",
            color=discord.Color.blue()
        )
        
        # Role Commands
        help_embed.add_field(
            name="Role Management",
            value=(
                "• `/مقبول [member]` - Give role to member\n"
                "• `/مرفوض [member]` - Remove role from member"
            ),
            inline=False
        )
        
        # Welcome Commands
        help_embed.add_field(
            name="Welcome Settings (Admin Only)",
            value=(
                "• `/setwelcomechannel [channel]` - Set welcome channel\n"
                "• `/setwelcomebackground [url]` - Set welcome background\n"
                "• `/testwelcome` - Test welcome message"
            ),
            inline=False
        )
        
        # Voice Commands
        help_embed.add_field(
            name="Voice Commands (Admin Only)",
            value=(
                "• `/testsound` - Test welcome sound\n"
                "• `/volume [0.0-1.0]` - Adjust sound volume"
            ),
            inline=False
        )
        
        # Status Commands
        help_embed.add_field(
            name="Status Commands (Admin Only)",
            value=(
                "• `/setstatus [type] [message]` - Change bot status\n"
                "  Types: playing, streaming, listening, watching, competing"
            ),
            inline=False
        )
        
        # Testing Commands
        help_embed.add_field(
            name="Testing Commands (Admin Only)",
            value="• `/test_visa_dm` - Test visa DM messages",
            inline=False
        )
        
        try:
            await interaction.response.send_message(embed=help_embed, ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ لا يمكن إرسال الرسالة. يرجى التأكد من إعدادات الخصوصية الخاصة بك.",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error sending help message: {str(e)}")
            await interaction.response.send_message(
                "❌ حدث خطأ أثناء إرسال قائمة الأوامر.",
                ephemeral=True
            )

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
            logger.error(f"Help command error: {str(error)}")
            await interaction.response.send_message(
                "*حدث خطأ غير متوقع.*",
                ephemeral=True
            )

async def setup(bot):
    """Setup function for loading the cog"""
    # Create cog instance
    cog = HelpCommands(bot)
    
    # Add cog to bot
    await bot.add_cog(cog)
    
    try:
        # Register app commands to guild
        guild = discord.Object(id=Config.GUILD_ID)
        bot.tree.add_command(cog.help_command, guild=guild)
        print("Registered help command to guild")
    except Exception as e:
        print(f"Failed to register help command: {e}")
