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

    @app_commands.command(name="help")
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
            await interaction.response.send_message("❌ لا يمكن إرسال الرسالة. يرجى التأكد من إعدادات الخصوصية الخاصة بك.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error sending help message: {str(e)}")
            await interaction.response.send_message("❌ حدث خطأ أثناء إرسال قائمة الأوامر.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(HelpCommands(bot))
