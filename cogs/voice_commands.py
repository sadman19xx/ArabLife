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

    async def _log(self, msg: str, level: str = 'info'):
        """Log message to both console and channel"""
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(msg)
        
        try:
            # Get audit log channel from config
            audit_channel = self.bot.get_channel(Config.AUDIT_LOG_CHANNEL_ID)
            if audit_channel:
                # Format message based on level
                if level.lower() == 'error':
                    content = f"❌ **Voice Error:** {msg}"
                elif level.lower() == 'warning':
                    content = f"⚠️ **Voice Warning:** {msg}"
                else:
                    content = f"ℹ️ **Voice Info:** {msg}"
                    
                await audit_channel.send(content)
        except Exception as e:
            logger.error(f"Failed to send log message: {e}")

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

                        # Connect to voice with self_deaf=False to ensure bot can play audio
                        self.voice = await channel.connect(
                            timeout=Config.VOICE_TIMEOUT,
                            reconnect=True,
                            self_deaf=False,
                            self_mute=False
                        )
                        
                        # Verify connection is healthy
                        if not self.voice.is_connected():
                            raise discord.ClientException("Voice client reports disconnected state after connect")
                            
                        # Ensure websocket is connected
                        if not hasattr(self.voice, 'ws') or not self.voice.ws or self.voice.ws.closed:
                            raise discord.ClientException("Voice websocket not established")
                            
                        # Start keep-alive
                        if hasattr(self.voice.ws, '_keep_alive'):
                            self.voice.ws._keep_alive.start()
                            
                        # Update bot's shared voice client
                        self.bot.shared_voice_client = self.voice
                        
                        # Configure FFmpeg path
                        discord.FFmpegPCMAudio.DEFAULT_EXECUTABLE = Config.FFMPEG_PATH
                        
                        # Reset reconnect attempts on successful connection
                        self.reconnect_attempts = 0
                        await self._log("Connected to voice channel")
                        
                        # Verify voice state
                        await asyncio.sleep(1)  # Short wait to verify connection
                        if not self.voice.is_connected() or (hasattr(self.voice, 'ws') and self.voice.ws.closed):
                            raise discord.ClientException("Connection unstable after connect")

            except discord.ClientException as e:
                await self._log(f"Voice client error: {str(e)}", 'error')
                # Clean up the failed connection
                try:
                    if self.voice:
                        await self.voice.disconnect(force=True)
                except:
                    pass
                self.voice = None
                self.bot.shared_voice_client = None
                
            except Exception as e:
                await self._log(f"Connection error: {str(e)}", 'error')
                # Clean up any existing connection
                try:
                    if self.voice:
                        await self.voice.disconnect(force=True)
                except:
                    pass
                self.voice = None
                self.bot.shared_voice_client = None
                
                # Implement exponential backoff for reconnection
                self.reconnect_attempts += 1
                if self.reconnect_attempts > Config.MAX_RECONNECT_ATTEMPTS:
                    await self._log("Max reconnection attempts reached. Waiting for manual intervention.", 'warning')
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
                    await self._log(f"Failed to create audio source: {str(e)}", 'error')
                    return
                await self._log(f"Playing welcome for {member_name}")

            except Exception as e:
                await self._log(f"Playback error: {str(e)}", 'error')

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Handle voice states"""
        await self.ready.wait()  # Wait for bot to be ready

        # Handle bot's own voice state
        if member.id == self.bot.user.id:
            if after.channel:
                # Bot joined a channel
                if after.deaf or after.self_deaf:
                    try:
                        # Ensure bot is not deafened
                        await member.guild.change_voice_state(
                            channel=after.channel,
                            self_deaf=False,
                            self_mute=False
                        )
                        await self._log("Undeafened bot in voice channel")
                    except Exception as e:
                        await self._log(f"Failed to undeafen bot: {str(e)}", 'error')
                
                # Verify connection state
                if self.voice and not self.voice.is_connected():
                    await self._log("Voice connection state mismatch detected", 'warning')
                    self.voice = None
                    self.bot.shared_voice_client = None
            else:
                # Bot left channel
                if self.voice and self.voice.is_connected():
                    await self._log("Unexpected voice disconnection", 'warning')
                    try:
                        await self.voice.disconnect(force=True)
                    except:
                        pass
                    self.voice = None
                    self.bot.shared_voice_client = None
            return

        # Handle user joins
        if not member.bot and after.channel and after.channel.id == self.channel_id:
            if before.channel != after.channel:
                # Verify bot's voice state before playing
                if self.voice and self.voice.is_connected():
                    if not self.voice.is_playing():
                        await self._play_welcome(member.name)
                    else:
                        await self._log(f"Skipped welcome sound for {member.name} - Already playing", 'warning')
                else:
                    await self._log(f"Couldn't play welcome sound for {member.name} - Not connected", 'warning')

    @commands.command()
    async def rejoin(self, ctx):
        """Force reconnection to voice channel"""
        try:
            # Clean up existing connection first
            if self.voice:
                try:
                    await self.voice.disconnect(force=True)
                except:
                    pass
            
            self.voice = None
            self.bot.shared_voice_client = None
            self.reconnect_attempts = 0  # Reset attempts
            
            await ctx.send("🔄 Reconnecting to voice channel...")
            
            # Wait for new connection
            for _ in range(10):  # Wait up to 10 seconds
                await asyncio.sleep(1)
                if self.voice and self.voice.is_connected():
                    if hasattr(self.voice, 'ws') and self.voice.ws and not self.voice.ws.closed:
                        await ctx.send("✅ Successfully reconnected!")
                        return
            
            await ctx.send("❌ Failed to establish stable connection. Please try again or check logs.")
        except Exception as e:
            await ctx.send(f"❌ Error during reconnection: {str(e)}")
            await self._log(f"Rejoin command error: {str(e)}", 'error')

async def setup(bot):
    await bot.add_cog(VoiceCommands(bot))
