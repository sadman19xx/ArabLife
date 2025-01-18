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

    async def _verify_connection(self, voice_client) -> bool:
        """Verify voice connection is healthy"""
        if not voice_client:
            return False
            
        if not voice_client.is_connected():
            return False
            
        if hasattr(voice_client, 'ws') and voice_client.ws and voice_client.ws.closed:
            return False
            
        return True

    async def _initial_connect(self):
        """Initial voice connection"""
        await self.bot.wait_until_ready()
        await asyncio.sleep(5)  # Wait for bot to initialize
        self.ready.set()

        while True:  # Keep trying to connect
            try:
                # Check if we already have a connection
                if self.voice and await self._verify_connection(self.voice):
                    await asyncio.sleep(5)
                    continue

                channel = self.bot.get_channel(self.channel_id)
                if not channel:
                    await asyncio.sleep(5)
                    continue

                # Configure FFmpeg
                discord.FFmpegPCMAudio.DEFAULT_EXECUTABLE = Config.FFMPEG_PATH
                
                # Clean up any existing connection
                if channel.guild.voice_client:
                    try:
                        await channel.guild.voice_client.disconnect(force=True)
                        await asyncio.sleep(1)
                    except:
                        pass

                # Initial connection
                voice_client = await channel.connect(
                    timeout=Config.VOICE_TIMEOUT,
                    self_deaf=False,
                    self_mute=False
                )

                # Verify connection
                if await self._verify_connection(voice_client):
                    self.bot.shared_voice_client = voice_client
                    await self._log("Made initial voice connection")
                    
                    # Start keep-alive if needed
                    if (hasattr(voice_client, 'ws') and 
                        voice_client.ws and 
                        hasattr(voice_client.ws, '_keep_alive')):
                        voice_client.ws._keep_alive.start()
                else:
                    await self._log("Initial connection verification failed")
                    try:
                        await voice_client.disconnect(force=True)
                    except:
                        pass

                await asyncio.sleep(5)  # Wait before next check

            except Exception as e:
                logger.error(f"Initial connection error: {e}")
                await asyncio.sleep(5)  # Wait before retry

    async def _ensure_connection(self):
        """Ensure we have a valid voice connection"""
        if not self.voice or not await self._verify_connection(self.voice):
            channel = self.bot.get_channel(self.channel_id)
            if not channel:
                return False

            try:
                # Clean up any existing connection
                if channel.guild.voice_client:
                    try:
                        await channel.guild.voice_client.disconnect(force=True)
                        await asyncio.sleep(1)
                    except:
                        pass

                # New connection
                voice_client = await channel.connect(
                    timeout=Config.VOICE_TIMEOUT,
                    self_deaf=False,
                    self_mute=False
                )

                if await self._verify_connection(voice_client):
                    self.bot.shared_voice_client = voice_client
                    return True
            except:
                pass

            return False
        return True

    async def _play_welcome(self, member_name: str):
        """Play welcome sound"""
        if not await self._ensure_connection():
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
                    if await self._ensure_connection():
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
            self.bot.shared_voice_client = None
            await asyncio.sleep(1)  # Wait for cleanup

            # New connection
            voice_client = await channel.connect(
                timeout=Config.VOICE_TIMEOUT,
                self_deaf=False,
                self_mute=False
            )
            
            # Verify connection
            if await self._verify_connection(voice_client):
                self.bot.shared_voice_client = voice_client
                # Start keep-alive
                if hasattr(voice_client, 'ws') and voice_client.ws and hasattr(voice_client.ws, '_keep_alive'):
                    voice_client.ws._keep_alive.start()
                await ctx.send("✅ Successfully reconnected!")
            else:
                await ctx.send("❌ Connection verification failed")
                try:
                    await voice_client.disconnect(force=True)
                except:
                    pass
                
        except Exception as e:
            await ctx.send(f"❌ Error during reconnection: {str(e)}")
            logger.error(f"Rejoin error: {e}")

async def setup(bot):
    await bot.add_cog(VoiceCommands(bot))
