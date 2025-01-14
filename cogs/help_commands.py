import discord
from discord.ext import commands
from discord.ext.commands import Cog
from discord import app_commands
import logging
from config import Config
from utils.logger import LoggerMixin

class HelpCommands(Cog, LoggerMixin):
    """Cog for help commands"""
    
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="help",
        description="Shows all available commands"
    )
    async def help_command(
        self,
        interaction: discord.Interaction,
        category: str = None
    ):
        """Shows all available commands"""
        try:
            if category:
                await self.show_category_help(interaction, category)
                return

            # Main help embed
            help_embed = discord.Embed(
                title="نظام المساعدة",
                description=(
                    "اختر فئة للحصول على معلومات مفصلة عن الأوامر المتاحة:\n\n"
                    "👋 `/help welcome` - نظام الترحيب\n"
                    "📝 `/help application` - نظام التقديم\n\n"
                    "*استخدم الأمر مع اسم الفئة للحصول على تفاصيل أكثر*"
                ),
                color=discord.Color.blue()
            )
            
            help_embed.set_footer(
                text=f"{interaction.guild.name}",
                icon_url=interaction.guild.icon.url if interaction.guild.icon else None
            )
            
            await interaction.response.send_message(embed=help_embed, ephemeral=True)
            
        except Exception as e:
            self.log.error(f"Error sending help message: {e}")
            await interaction.response.send_message(
                "❌ حدث خطأ أثناء إرسال قائمة الأوامر.",
                ephemeral=True
            )

    async def show_category_help(self, interaction: discord.Interaction, category: str):
        """Show help for specific category"""
        embeds = {
            "welcome": self.get_welcome_help(),
            "application": self.get_application_help()
        }
        
        embed = embeds.get(category.lower())
        if not embed:
            await interaction.response.send_message(
                "❌ فئة غير صالحة. استخدم `/help` لعرض الفئات المتاحة.",
                ephemeral=True
            )
            return
            
        embed.set_footer(
            text=f"{interaction.guild.name}",
            icon_url=interaction.guild.icon.url if interaction.guild.icon else None
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    def get_welcome_help(self) -> discord.Embed:
        """Get help embed for welcome commands"""
        embed = discord.Embed(
            title="👋 نظام الترحيب",
            description="أوامر نظام الترحيب المتاحة:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="إعدادات الترحيب",
            value=(
                "• `/setwelcomechannel [channel]` - تحديد قناة الترحيب\n"
                "• `/setwelcomebackground [url]` - تحديد خلفية الترحيب\n"
                "• `/testwelcome` - اختبار رسالة الترحيب"
            ),
            inline=False
        )
        
        return embed

    def get_application_help(self) -> discord.Embed:
        """Get help embed for application commands"""
        embed = discord.Embed(
            title="📝 نظام التقديم",
            description="أوامر نظام التقديم المتاحة:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="أوامر التقديم",
            value=(
                "• `/apply` - بدء عملية التقديم\n"
                "• `/accept [member]` - قبول عضو\n"
                "• `/reject [member]` - رفض عضو"
            ),
            inline=False
        )
        
        return embed

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
            self.log.error(f"Help command error: {error}")
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
