import discord
from discord.ext import commands
import logging
import asyncio
from config import Config

logger = logging.getLogger('discord')

class VoiceCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = Config.WELCOME_VOICE_CHANNEL_ID
        self.lock = asyncio.Lock()
        self.ready = asyncio.Event()
        bot.loop.create_task(self._initial_connect())

    @property
    def voice(self):
        """Get voice client from bot's shared client"""
        return self.bot.shared_voice_client

    async def _log(self, msg: str):
        """Log message"""
        logger.info(msg)

    async def _initial_connect(self):
        """Initial voice connection"""
        await self.bot.wait_until_ready()
        await asyncio.sleep(5)  # Wait for bot to initialize
        self.ready.set()

        try:
            channel = self.bot.get_channel(self.channel_id)
            if channel:
                # Configure FFmpeg
                discord.FFmpegPCMAudio.DEFAULT_EXECUTABLE = Config.FFMPEG_PATH
                
                # Initial connection
                await channel.connect(
                    timeout=Config.VOICE_TIMEOUT,
                    self_deaf=False,
                    self_mute=False
                )
                await self._log("Made initial voice connection")
        except Exception as e:
            logger.error(f"Initial connection error: {e}")

    async def _play_welcome(self, member_name: str):
        """Play welcome sound"""
        if not self.voice:
            return

        try:
            if self.voice.is_playing():
                self.voice.stop()

            # Configure FFmpeg options
            ffmpeg_options = {
                'options': f'-loglevel warning -filter:a volume={Config.WELCOME_SOUND_VOLUME}',
                'executable': Config.FFMPEG_PATH
            }
            
            # Create and play audio
            audio = discord.FFmpegPCMAudio(Config.WELCOME_SOUND_PATH, **ffmpeg_options)
            transformer = discord.PCMVolumeTransformer(audio, volume=Config.WELCOME_SOUND_VOLUME)
            self.voice.play(transformer)
            await self._log(f"Playing welcome for {member_name}")

        except Exception as e:
            logger.error(f"Playback error: {e}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Handle user joins"""
        await self.ready.wait()

        if not member.bot and after.channel and after.channel.id == self.channel_id:
            if before.channel != after.channel:
                async with self.lock:
                    if self.voice and self.voice.is_connected():
                        await self._play_welcome(member.name)

    @commands.command()
    async def rejoin(self, ctx):
        """Force reconnection"""
        try:
            channel = self.bot.get_channel(self.channel_id)
            if not channel:
                await ctx.send("❌ Voice channel not found")
                return

            await ctx.send("🔄 Reconnecting to voice channel...")
            
            # Clean up existing connection
            if self.voice:
                try:
                    await self.voice.disconnect(force=True)
                except:
                    pass

            # New connection
            await channel.connect(
                timeout=Config.VOICE_TIMEOUT,
                self_deaf=False,
                self_mute=False
            )
            await ctx.send("✅ Successfully reconnected!")
            
        except Exception as e:
            await ctx.send(f"❌ Error during reconnection: {str(e)}")
            logger.error(f"Rejoin error: {e}")

async def setup(bot):
    await bot.add_cog(VoiceCommands(bot))
