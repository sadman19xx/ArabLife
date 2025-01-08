import discord
from discord.ext import commands
from discord.ext.commands import Cog, cooldown, BucketType
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

    async def cog_check(self, ctx):
        """Check if user has required permissions for any command in this cog"""
        if not ctx.guild:
            raise commands.NoPrivateMessage()
        return True

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

    @commands.command()
    @commands.has_permissions(administrator=True)
    @cooldown(1, Config.STATUS_COMMAND_COOLDOWN, BucketType.guild)
    async def setstatus(self, ctx, activity_type: str, *, message: str):
        """Change the bot's status dynamically.
        Usage: /setstatus <type> <message>
        Types: playing, streaming, listening, watching, competing
        """
        # Validate input
        if not self._validate_status(activity_type, message):
            await ctx.send("❌ *نوع النشاط غير صالح أو الرسالة تحتوي على كلمات محظورة.*")
            return

        try:
            activity = discord.Activity(
                type=self.activity_types[activity_type.lower()], 
                name=message
            )
            await self.bot.change_presence(activity=activity)
            await ctx.send(f"✅ *تم تغيير الحالة الى: {activity_type.capitalize()} {message}*")
            logger.info(f"Status changed to: {activity_type.capitalize()} {message} by {ctx.author.name}#{ctx.author.discriminator}")
            
        except discord.InvalidArgument:
            await ctx.send("❌ *معطيات غير صالحة.*")
            logger.error(f"Invalid status parameters: type={activity_type}, message={message}")
            
        except Exception as e:
            await ctx.send("❌ *حدث خطأ أثناء تغيير الحالة.*")
            logger.error(f"Error changing status: {str(e)}")

    @setstatus.error
    async def status_command_error(self, ctx, error):
        """Error handler for status commands"""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send('*لا تملك الصلاحية لأستخدام هذه الامر.*')
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f'*الرجاء الانتظار {error.retry_after:.1f} ثواني.*')
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('*يرجى تقديم نوع النشاط والرسالة.*')
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send('*لا يمكن استخدام هذا الأمر في الرسائل الخاصة.*')
        else:
            logger.error(f"Unexpected error in status command: {str(error)}")
            await ctx.send('*حدث خطأ غير متوقع.*')

async def setup(bot):
    await bot.add_cog(StatusCommands(bot))
