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
                    "🎫 `/help tickets` - نظام التذاكر\n"
                    "🛡️ `/help security` - نظام الحماية\n"
                    "🤖 `/help automod` - نظام المراقبة الآلي\n"
                    "👋 `/help welcome` - نظام الترحيب\n"
                    "👥 `/help roles` - إدارة الرتب\n"
                    "🎙️ `/help voice` - إعدادات الصوت\n"
                    "🎮 `/help status` - حالة البوت\n"
                    "⚙️ `/help admin` - أوامر الإدارة\n\n"
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
            "tickets": self.get_tickets_help(),
            "security": self.get_security_help(),
            "automod": self.get_automod_help(),
            "welcome": self.get_welcome_help(),
            "roles": self.get_roles_help(),
            "voice": self.get_voice_help(),
            "status": self.get_status_help(),
            "admin": self.get_admin_help()
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

    def get_tickets_help(self) -> discord.Embed:
        """Get help embed for ticket commands"""
        embed = discord.Embed(
            title="🎫 نظام التذاكر",
            description="أوامر نظام التذاكر المتاحة:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="إعداد النظام (للإدارة)",
            value=(
                "• `/setup-tickets` - إعداد نظام التذاكر في القناة الحالية\n"
                "• `/ticket-stats` - عرض إحصائيات التذاكر\n"
                "• `/ticket-search` - البحث في التذاكر"
            ),
            inline=False
        )
        
        embed.add_field(
            name="أزرار التذاكر",
            value=(
                "• `استلام` - استلام التذكرة\n"
                "• `اغلاق` - إغلاق التذكرة\n"
                "• `اعادة فتح` - إعادة فتح تذكرة مغلقة\n"
                "• `حذف` - حذف التذكرة نهائياً"
            ),
            inline=False
        )
        
        return embed

    def get_security_help(self) -> discord.Embed:
        """Get help embed for security commands"""
        embed = discord.Embed(
            title="🛡️ نظام الحماية",
            description="أوامر الحماية المتاحة:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="إدارة التحذيرات",
            value=(
                "• `/warnings [member]` - عرض تحذيرات العضو\n"
                "• `/clearwarnings [member]` - مسح تحذيرات العضو"
            ),
            inline=False
        )
        
        embed.add_field(
            name="الحماية من الهجمات",
            value=(
                "• `/raidmode [on/off]` - تفعيل/تعطيل وضع الحماية من الهجمات\n"
                "يتم تفعيله تلقائياً عند اكتشاف هجوم"
            ),
            inline=False
        )
        
        return embed

    def get_automod_help(self) -> discord.Embed:
        """Get help embed for automod commands"""
        embed = discord.Embed(
            title="🤖 نظام المراقبة الآلي",
            description="أوامر المراقبة الآلية المتاحة:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="إعدادات الحماية",
            value=(
                "• `/automod spam [on/off]` - حماية من الرسائل المكررة\n"
                "• `/automod links [on/off]` - حماية من الروابط\n"
                "• `/automod invites [on/off]` - حماية من دعوات الديسكورد\n"
                "• `/automod mentions [limit]` - تحديد عدد الإشارات المسموح"
            ),
            inline=False
        )
        
        return embed

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

    def get_roles_help(self) -> discord.Embed:
        """Get help embed for role commands"""
        embed = discord.Embed(
            title="👥 إدارة الرتب",
            description="أوامر إدارة الرتب المتاحة:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="الأوامر الأساسية",
            value=(
                "• `/مقبول [member]` - إعطاء رتبة للعضو\n"
                "• `/مرفوض [member]` - إزالة رتبة من العضو"
            ),
            inline=False
        )
        
        return embed

    def get_voice_help(self) -> discord.Embed:
        """Get help embed for voice commands"""
        embed = discord.Embed(
            title="🎙️ إعدادات الصوت",
            description="أوامر إعدادات الصوت المتاحة:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="الأوامر المتاحة",
            value=(
                "• `/testsound` - اختبار صوت الترحيب\n"
                "• `/volume [0.0-1.0]` - تعديل مستوى الصوت"
            ),
            inline=False
        )
        
        return embed

    def get_status_help(self) -> discord.Embed:
        """Get help embed for status commands"""
        embed = discord.Embed(
            title="🎮 حالة البوت",
            description="أوامر تغيير حالة البوت المتاحة:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="تغيير الحالة",
            value=(
                "• `/setstatus [type] [message]` - تغيير حالة البوت\n"
                "الأنواع المتاحة: playing, streaming, listening, watching, competing"
            ),
            inline=False
        )
        
        return embed

    def get_admin_help(self) -> discord.Embed:
        """Get help embed for admin commands"""
        embed = discord.Embed(
            title="⚙️ أوامر الإدارة",
            description="الأوامر الإدارية المتاحة:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="إعدادات عامة",
            value=(
                "• `/settings view` - عرض الإعدادات الحالية\n"
                "• `/settings prefix [prefix]` - تغيير بادئة الأوامر\n"
                "• `/settings language [lang]` - تغيير لغة البوت"
            ),
            inline=False
        )
        
        embed.add_field(
            name="إدارة القنوات",
            value=(
                "• `/setlogchannel [channel]` - تحديد قناة السجلات\n"
                "• `/setauditchannel [channel]` - تحديد قناة المراقبة"
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
