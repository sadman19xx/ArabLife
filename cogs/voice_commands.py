import discord
from discord.ext import commands
from discord.ext.commands import Cog, cooldown, BucketType
import logging
import os
from config import Config

logger = logging.getLogger('discord')

class VoiceCommands(Cog):
    """Cog for voice-related commands"""
    
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """Check if user has required permissions for any command in this cog"""
        if not ctx.guild:
            raise commands.NoPrivateMessage()
        return True

    @Cog.listener()
    async def on_member_join(self, member):
        """Play welcome sound when a member joins"""
        # Get the first voice channel in the guild
        voice_channel = next((channel for channel in member.guild.voice_channels), None)
        if not voice_channel:
            logger.error("No voice channels found in the guild")
            return

        try:
            # Connect to voice channel if not already connected
            if not member.guild.voice_client:
                voice_client = await voice_channel.connect()
            else:
                voice_client = member.guild.voice_client
                if voice_client.channel != voice_channel:
                    await voice_client.move_to(voice_channel)

            # Play the welcome sound
            if os.path.exists(Config.WELCOME_SOUND_PATH):
                audio_source = discord.FFmpegPCMAudio(Config.WELCOME_SOUND_PATH)
                transformed_source = discord.PCMVolumeTransformer(audio_source, volume=Config.DEFAULT_VOLUME)
                
                if not voice_client.is_playing():
                    voice_client.play(transformed_source)
                    logger.info(f"Playing welcome sound for {member.name}#{member.discriminator}")
            else:
                logger.error(f"Welcome sound file not found at {Config.WELCOME_SOUND_PATH}")

        except Exception as e:
            logger.error(f"Error playing welcome sound: {str(e)}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    @cooldown(1, Config.SOUND_COMMAND_COOLDOWN, BucketType.guild)
    async def testsound(self, ctx):
        """Test the welcome sound"""
        await ctx.send("*جاري تشغيل صوت الترحيب...*")
        try:
            await self.on_member_join(ctx.author)
        except Exception as e:
            logger.error(f"Error testing welcome sound: {str(e)}")
            await ctx.send("*حدث خطأ أثناء تشغيل الصوت.*")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def volume(self, ctx, vol: float):
        """Change the volume (0.0 to 1.0)"""
        if not ctx.voice_client:
            await ctx.send("*البوت غير متصل بالصوت.*")
            return

        try:
            # Ensure volume is between 0 and 1
            vol = min(1.0, max(0.0, vol))
            
            if ctx.voice_client.source:
                ctx.voice_client.source.volume = vol
                await ctx.send(f"*تم تغيير مستوى الصوت الى {vol}*")
                logger.info(f"Volume changed to {vol} by {ctx.author.name}#{ctx.author.discriminator}")
            else:
                await ctx.send("*لا يوجد صوت قيد التشغيل.*")
        except Exception as e:
            logger.error(f"Error changing volume: {str(e)}")
            await ctx.send("*حدث خطأ أثناء تغيير مستوى الصوت.*")

    @testsound.error
    @volume.error
    async def voice_command_error(self, ctx, error):
        """Error handler for voice commands"""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send('*لا تملك الصلاحية لأستخدام هذه الامر.*')
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f'*الرجاء الانتظار {error.retry_after:.1f} ثواني.*')
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send('*لا يمكن استخدام هذا الأمر في الرسائل الخاصة.*')
        elif isinstance(error, commands.BadArgument):
            await ctx.send('*يرجى إدخال رقم صحيح بين 0.0 و 1.0*')
        else:
            logger.error(f"Unexpected error in voice command: {str(error)}")
            await ctx.send('*حدث خطأ غير متوقع.*')

async def setup(bot):
    await bot.add_cog(VoiceCommands(bot))
