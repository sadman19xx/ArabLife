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
        self.voice_ready = asyncio.Event()
        self.session_id = None
        self.ws = None
        bot.loop.create_task(self._connection_loop())

    @property
    def voice(self):
        """Get voice client from bot's shared client"""
        return self.bot.shared_voice_client

    async def _log(self, msg: str, level: str = 'info'):
        """Log message to both console and channel"""
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(msg)

    async def _verify_connection(self, voice_client) -> bool:
        """Verify voice connection is healthy"""
        if not voice_client:
            return False
            
        if not voice_client.is_connected():
            return False
            
        if not hasattr(voice_client, '_connected'):
            return False
            
        try:
            # Wait for voice client to be fully ready
            await asyncio.wait_for(voice_client._connected.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            return False
            
        return True

    async def _cleanup_voice(self):
        """Clean up voice resources"""
        try:
            if self.voice:
                if self.voice.is_playing():
                    self.voice.stop()
                await self.voice.disconnect(force=True)
            self.bot.shared_voice_client = None
            self.voice_ready.clear()
            self.session_id = None
            self.ws = None
            await asyncio.sleep(1)  # Wait for cleanup
        except Exception as e:
            logger.error(f"Error cleaning up voice: {e}")

    async def _connection_loop(self):
        """Maintain voice connection"""
        await self.bot.wait_until_ready()
        await asyncio.sleep(5)  # Wait for bot to initialize
        self.ready.set()

        while not self.bot.is_closed():
            try:
                # Check if we already have a connection
                if self.voice and await self._verify_connection(self.voice):
                    self.voice_ready.set()
                    await asyncio.sleep(5)
                    continue

                await self._cleanup_voice()
                
                channel = self.bot.get_channel(self.channel_id)
                if not channel:
                    await asyncio.sleep(5)
                    continue

                # Configure FFmpeg
                discord.FFmpegPCMAudio.DEFAULT_EXECUTABLE = Config.FFMPEG_PATH

                # Connect with longer timeout
                voice_client = await channel.connect(
                    timeout=30.0,  # Increased timeout
                    self_deaf=False,
                    self_mute=False
                )

                # Wait for connection to stabilize
                await asyncio.sleep(2)

                # Verify connection
                if await self._verify_connection(voice_client):
                    self.bot.shared_voice_client = voice_client
                    self.voice_ready.set()
                    logger.info("Voice connection established and verified")
                else:
                    logger.warning("Voice connection verification failed")
                    await self._cleanup_voice()

            except Exception as e:
                logger.error(f"Connection error: {e}")
                await self._cleanup_voice()
                await asyncio.sleep(5)

    async def _play_welcome(self, member_name: str):
        """Play welcome sound"""
        try:
            # Wait for voice to be ready
            await asyncio.wait_for(self.voice_ready.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for voice connection for {member_name}")
            return

        if not self.voice or not await self._verify_connection(self.voice):
            logger.warning(f"Cannot play welcome for {member_name} - No voice connection")
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
            
            def after_play(error):
                if error:
                    logger.error(f"Playback error: {error}")
            
            self.voice.play(transformer, after=after_play)
            logger.info(f"Playing welcome for {member_name}")

        except Exception as e:
            logger.error(f"Playback error: {e}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Handle voice states"""
        await self.ready.wait()

        # Handle bot's own voice state
        if member.id == self.bot.user.id:
            if after.channel:
                if after.deaf or after.self_deaf:
                    try:
                        await member.guild.change_voice_state(
                            channel=after.channel,
                            self_deaf=False,
                            self_mute=False
                        )
                        logger.info("Undeafened bot in voice channel")
                    except Exception as e:
                        logger.error(f"Failed to undeafen bot: {e}")
                
                # Store session ID
                self.session_id = after.session_id
            else:
                await self._cleanup_voice()
            return

        # Handle user joins
        if not member.bot and after.channel and after.channel.id == self.channel_id:
            if before.channel != after.channel:
                async with self.lock:
                    await self._play_welcome(member.name)

    @commands.command()
    async def rejoin(self, ctx):
        """Force reconnection"""
        try:
            await ctx.send("🔄 Reconnecting to voice channel...")
            
            # Clean up existing connection
            await self._cleanup_voice()
            
            channel = self.bot.get_channel(self.channel_id)
            if not channel:
                await ctx.send("❌ Voice channel not found")
                return

            # New connection with longer timeout
            voice_client = await channel.connect(
                timeout=30.0,
                self_deaf=False,
                self_mute=False
            )
            
            # Wait for connection to stabilize
            await asyncio.sleep(2)
            
            # Verify connection
            if await self._verify_connection(voice_client):
                self.bot.shared_voice_client = voice_client
                self.voice_ready.set()
                await ctx.send("✅ Successfully reconnected!")
            else:
                await ctx.send("❌ Connection verification failed")
                await self._cleanup_voice()
                
        except Exception as e:
            await ctx.send(f"❌ Error during reconnection: {str(e)}")
            logger.error(f"Rejoin error: {e}")
            await self._cleanup_voice()

async def setup(bot):
    await bot.add_cog(VoiceCommands(bot))
