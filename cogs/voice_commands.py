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
        self.voice = None
        self.lock = asyncio.Lock()
        self.ready = asyncio.Event()
        self.reconnect_attempts = 0
        bot.loop.create_task(self._connection_loop())

    async def _log(self, msg: str):
        """Log message to both console and channel"""
        logger.info(msg)
        try:
            channel = self.bot.get_channel(self.channel_id)
            if channel:
                await channel.send(f"```\n{msg}\n```")
        except:
            pass

    async def _connection_loop(self):
        """Maintain voice connection"""
        await self.bot.wait_until_ready()
        await asyncio.sleep(5)  # Wait for bot to initialize
        self.ready.set()

        while not self.bot.is_closed():
            try:
                channel = self.bot.get_channel(self.channel_id)
                if not channel:
                    await asyncio.sleep(5)
                    continue

                async with self.lock:
                    # Check if we need to connect
                    if not self.voice or not self.voice.is_connected():
                        # Clean up any existing connection
                        if channel.guild.voice_client:
                            await channel.guild.voice_client.disconnect()
                            await asyncio.sleep(2)

                        # Connect to voice with configured timeout
                        self.voice = await channel.connect(
                            timeout=Config.VOICE_TIMEOUT,
                            reconnect=True
                        )
                        
                        # Update bot's shared voice client
                        self.bot.shared_voice_client = self.voice
                        
                        # Configure FFmpeg path
                        discord.FFmpegPCMAudio.DEFAULT_EXECUTABLE = Config.FFMPEG_PATH
                        
                        # Reset reconnect attempts on successful connection
                        self.reconnect_attempts = 0
                        await self._log("Connected to voice channel")

            except Exception as e:
                await self._log(f"Connection error: {str(e)}")
                self.voice = None
                self.bot.shared_voice_client = None
                
                # Implement exponential backoff for reconnection
                self.reconnect_attempts += 1
                if self.reconnect_attempts > Config.MAX_RECONNECT_ATTEMPTS:
                    await self._log("Max reconnection attempts reached. Waiting for manual intervention.")
                    await asyncio.sleep(Config.MAX_RECONNECT_DELAY)
                    self.reconnect_attempts = 0
                else:
                    delay = min(Config.RECONNECT_DELAY * (2 ** (self.reconnect_attempts - 1)), Config.MAX_RECONNECT_DELAY)
                    await asyncio.sleep(delay)

            await asyncio.sleep(5)

    async def _play_welcome(self, member_name: str):
        """Play welcome sound"""
        await self.ready.wait()  # Wait for bot to be ready
        
        async with self.lock:
            if not self.voice or not self.voice.is_connected():
                return

            try:
                if self.voice.is_playing():
                    self.voice.stop()

                # Configure FFmpeg options
                ffmpeg_options = {
                    'options': f'-loglevel warning -filter:a volume={Config.WELCOME_SOUND_VOLUME}',
                    'executable': Config.FFMPEG_PATH
                }
                
                # Create audio source with error handling
                try:
                    audio = discord.FFmpegPCMAudio(Config.WELCOME_SOUND_PATH, **ffmpeg_options)
                    transformer = discord.PCMVolumeTransformer(audio, volume=Config.WELCOME_SOUND_VOLUME)
                    
                    def after_play(error):
                        if error:
                            self.bot.loop.create_task(self._log(f"Playback error: {error}"))
                    
                    self.voice.play(transformer, after=after_play)
                except Exception as e:
                    await self._log(f"Failed to create audio source: {str(e)}")
                    return
                await self._log(f"Playing welcome for {member_name}")

            except Exception as e:
                await self._log(f"Playback error: {str(e)}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Handle voice states"""
        await self.ready.wait()  # Wait for bot to be ready

        # Only handle user joins
        if not member.bot and after.channel and after.channel.id == self.channel_id:
            if before.channel != after.channel:
                await self._play_welcome(member.name)

    @commands.command()
    async def rejoin(self, ctx):
        """Force reconnection to voice channel"""
        try:
            self.voice = None  # This will trigger reconnect in connection loop
            await ctx.send("🔄 Reconnecting to voice channel...")
            await asyncio.sleep(2)  # Wait for reconnection
            if self.voice and self.voice.is_connected():
                await ctx.send("✅ Successfully reconnected!")
            else:
                await ctx.send("❌ Failed to reconnect. Please try again or check logs.")
        except Exception as e:
            await ctx.send(f"❌ Error during reconnection: {str(e)}")

async def setup(bot):
    await bot.add_cog(VoiceCommands(bot))
