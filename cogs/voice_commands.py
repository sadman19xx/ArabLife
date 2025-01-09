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
        # Get FFmpeg path from config or use default paths
        self.ffmpeg_path = Config.FFMPEG_PATH or self._get_ffmpeg_path()
        self.voice_client = None

    def _get_ffmpeg_path(self):
        """Try to find FFmpeg in common locations"""
        common_paths = [
            r"C:\ffmpeg\bin\ffmpeg.exe",  # Windows custom install
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",  # Windows program files
            r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",  # Windows program files (x86)
            "ffmpeg"  # System PATH
        ]
        
        for path in common_paths:
            if os.path.isfile(path):
                return path
            elif os.path.isfile(path + ".exe"):  # Check with .exe extension
                return path + ".exe"
        
        return "ffmpeg"  # Default to system PATH as last resort

    async def cog_check(self, ctx):
        """Check if user has required permissions for any command in this cog"""
        if not ctx.guild:
            raise commands.NoPrivateMessage()
        return True

    @Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Triggered when a member joins/leaves/moves between voice channels"""
        # Ignore bot's own voice state updates
        if member.bot:
            return

        # Get the configured welcome channel
        welcome_channel = self.bot.get_channel(Config.WELCOME_VOICE_CHANNEL_ID)
        if not welcome_channel:
            logger.error("Welcome voice channel not found")
            return

        # Check if member joined the welcome channel
        if after.channel == welcome_channel and before.channel != welcome_channel:
            try:
                # Only connect to voice and play sound if configured
                if Config.WELCOME_SOUND_PATH and os.path.exists(Config.WELCOME_SOUND_PATH):
                    # Connect to voice channel if not already connected
                    if not welcome_channel.guild.voice_client:
                        self.voice_client = await welcome_channel.connect()
                    else:
                        self.voice_client = welcome_channel.guild.voice_client
                        if self.voice_client.channel != welcome_channel:
                            await self.voice_client.move_to(welcome_channel)

                    # Play the welcome sound
                    audio_source = discord.FFmpegPCMAudio(
                        Config.WELCOME_SOUND_PATH,
                        executable=self.ffmpeg_path
                    )
                    transformed_source = discord.PCMVolumeTransformer(audio_source, volume=Config.DEFAULT_VOLUME)
                    
                    if not self.voice_client.is_playing():
                        self.voice_client.play(transformed_source)
                        logger.info(f"Playing welcome sound for {member.name}#{member.discriminator} in {welcome_channel.name}")
                else:
                    logger.warning(f"Welcome sound file not found at {Config.WELCOME_SOUND_PATH}")
            except Exception as e:
                logger.error(f"Error playing welcome sound: {str(e)}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    @cooldown(1, Config.SOUND_COMMAND_COOLDOWN, BucketType.guild)
    async def testsound(self, ctx):
        """Test the welcome sound"""
        try:
            # Log FFmpeg path being used
            logger.info(f"Using FFmpeg path: {self.ffmpeg_path}")
            
            # Verify FFmpeg exists
            if not os.path.isfile(self.ffmpeg_path) and self.ffmpeg_path != "ffmpeg":
                await ctx.send("*خطأ: لم يتم العثور على FFmpeg. يرجى التحقق من التثبيت.*")
                return

            # Get the welcome channel
            welcome_channel = self.bot.get_channel(Config.WELCOME_VOICE_CHANNEL_ID)
            if not welcome_channel:
                await ctx.send("*لم يتم العثور على قناة الترحيب.*")
                return

            await ctx.send("*جاري تشغيل صوت الترحيب...*")

            # Only connect to voice and play sound if configured
            if Config.WELCOME_SOUND_PATH and os.path.exists(Config.WELCOME_SOUND_PATH):
                # Connect to voice channel
                if not welcome_channel.guild.voice_client:
                    self.voice_client = await welcome_channel.connect()
                else:
                    self.voice_client = welcome_channel.guild.voice_client
                    if self.voice_client.channel != welcome_channel:
                        await self.voice_client.move_to(welcome_channel)

                # Play the welcome sound
                audio_source = discord.FFmpegPCMAudio(
                    Config.WELCOME_SOUND_PATH,
                    executable=self.ffmpeg_path
                )
                transformed_source = discord.PCMVolumeTransformer(audio_source, volume=Config.DEFAULT_VOLUME)
                
                if not self.voice_client.is_playing():
                    self.voice_client.play(transformed_source)
                    logger.info(f"Testing welcome sound in {welcome_channel.name}")
            else:
                await ctx.send("*لم يتم تكوين ملف الصوت.*")

        except Exception as e:
            logger.error(f"Error testing welcome sound: {str(e)}")
            await ctx.send(f"*حدث خطأ أثناء تشغيل الصوت: {str(e)}*")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def volume(self, ctx, vol: float):
        """Change the volume (0.0 to 1.0)"""
        if not self.voice_client:
            await ctx.send("*البوت غير متصل بالصوت.*")
            return

        try:
            # Ensure volume is between 0 and 1
            vol = min(1.0, max(0.0, vol))
            
            if self.voice_client.source:
                self.voice_client.source.volume = vol
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
