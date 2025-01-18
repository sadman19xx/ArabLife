import discord
from discord.ext import commands
import logging
import asyncio
from config import Config

logger = logging.getLogger('discord')

class VoiceCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = str(Config.WELCOME_VOICE_CHANNEL_ID)  # Convert to string
        self.lock = asyncio.Lock()
        self.ready = asyncio.Event()
        self.voice_ready = asyncio.Event()
        self.session_id = None
        self.ws = None
        self._connection_task = None
        self._reconnecting = False
        bot.loop.create_task(self._initial_connect())

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
        try:
            if not voice_client:
                logger.debug("No voice client to verify")
                return False
                
            if not voice_client.is_connected():
                logger.debug("Voice client reports as not connected")
                return False
                
            if not voice_client.channel:
                logger.debug("Voice client has no channel")
                return False
                
            if not voice_client.guild:
                logger.debug("Voice client has no guild")
                return False
                
            # Check if the voice client is in the correct channel
            if str(voice_client.channel.id) != self.channel_id:
                logger.debug(f"Voice client in wrong channel: {voice_client.channel.id} != {self.channel_id}")
                return False
                
            # Check if we can actually see the channel
            channel = self.bot.get_channel(int(self.channel_id))
            if not channel:
                logger.debug("Cannot see target voice channel")
                return False
                
            # Verify voice websocket
            if hasattr(voice_client, 'ws'):
                if not voice_client.ws or voice_client.ws.closed:
                    logger.debug("Voice websocket is closed or missing")
                    return False
                    
            try:
                # Test basic voice operations
                voice_client.is_playing()  # This should not raise an exception if client is healthy
            except Exception as e:
                logger.debug(f"Voice client operation test failed: {e}")
                return False
                
            logger.debug("Voice connection verified as healthy")
            return True
            
        except Exception as e:
            logger.error(f"Error during connection verification: {e}")
            return False

    async def _cleanup_voice(self):
        """Clean up voice resources"""
        try:
            # Cancel any existing connection task
            if self._connection_task and not self._connection_task.done():
                self._connection_task.cancel()
                try:
                    await self._connection_task
                except asyncio.CancelledError:
                    pass
                self._connection_task = None

            # Clean up voice client
            if self.voice:
                try:
                    if self.voice.is_playing():
                        self.voice.stop()
                    await self.voice.disconnect(force=True)
                except:
                    pass

            # Reset state
            self.bot.shared_voice_client = None
            self.voice_ready.clear()
            self.session_id = None
            self.ws = None
            self._reconnecting = False
            
            # Wait for cleanup
            await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"Error cleaning up voice: {e}")

    async def _connect_to_voice(self, channel):
        """Connect to voice channel"""
        try:
            # Force cleanup of any existing connections first
            await self._cleanup_voice()
            
            # Check if channel is valid
            if not isinstance(channel, discord.VoiceChannel):
                logger.error(f"Invalid channel type: {type(channel)}")
                return False

            # Check if channel is valid
            if not isinstance(channel, discord.VoiceChannel):
                logger.error(f"Invalid channel type: {type(channel)}")
                return False

            # Clean up any existing voice clients in the guild
            if channel.guild.voice_client:
                try:
                    await channel.guild.voice_client.disconnect(force=True)
                    await asyncio.sleep(1)
                except:
                    pass

            # Connect to voice channel with explicit options
            try:
                voice_client = await channel.connect(
                    timeout=Config.VOICE_TIMEOUT,
                    self_deaf=False,  # Explicitly set not deafened
                    self_mute=False   # Explicitly set not muted
                )
            except Exception as e:
                logger.error(f"Failed to connect to voice channel: {e}")
                return False

            # Wait for connection to stabilize
            await asyncio.sleep(Config.VOICE_STABILIZATION_DELAY)
            try:
                await channel.guild.change_voice_state(
                    channel=channel,
                    self_deaf=False,
                    self_mute=False
                )
                await asyncio.sleep(1)  # Wait for state change
            except Exception as e:
                logger.error(f"Failed to update voice state: {e}")
                # Continue anyway as this is not critical

            # Double-check voice state and force undeafen if needed
            try:
                await channel.guild.change_voice_state(
                    channel=channel,
                    self_deaf=False,
                    self_mute=False
                )
            except Exception as e:
                logger.error(f"Failed to update initial voice state: {e}")
                # Continue anyway as we'll verify the connection next

            # Verify connection with retries
            for _ in range(3):  # Try up to 3 times
                if await self._verify_connection(voice_client):
                    self.bot.shared_voice_client = voice_client
                    self.voice_ready.set()
                    self._reconnecting = False
                    logger.info(f"Voice connection established in guild {channel.guild.id}")
                    return True
                else:
                    logger.warning("Connection verification failed, retrying...")
                    await asyncio.sleep(1)
                    try:
                        await channel.guild.change_voice_state(
                            channel=channel,
                            self_deaf=False,
                            self_mute=False
                        )
                    except Exception as e:
                        logger.error(f"Failed to update voice state during retry: {e}")

            logger.warning(f"Voice connection verification failed after retries for guild {channel.guild.id}")
            await self._cleanup_voice()
            return False

        except Exception as e:
            logger.error(f"Connection error in guild {getattr(channel.guild, 'id', 'unknown')}: {e}")
            await self._cleanup_voice()
            return False

    async def _initial_connect(self):
        """Initial connection setup"""
        await self.bot.wait_until_ready()
        await asyncio.sleep(5)  # Wait for bot to initialize
        self.ready.set()
        
        # Start connection loop
        self._connection_task = self.bot.loop.create_task(self._connection_loop())

    async def _connection_loop(self):
        """Maintain voice connection"""
        retry_count = 0
        max_retries = Config.MAX_RECONNECT_ATTEMPTS
        base_delay = Config.RECONNECT_DELAY
        max_delay = Config.MAX_RECONNECT_DELAY

        while not self.bot.is_closed():
            try:
                # Check if we're already connected
                if self.voice and await self._verify_connection(self.voice):
                    retry_count = 0  # Reset retry count on successful connection
                    self.voice_ready.set()
                    await asyncio.sleep(5)
                    continue

                # Skip if we're in the process of reconnecting
                if self._reconnecting:
                    await asyncio.sleep(1)
                    continue

                self._reconnecting = True
                await self._cleanup_voice()
                
                # Get channel
                channel = self.bot.get_channel(int(self.channel_id))
                if not channel:
                    logger.warning(f"Could not find voice channel {self.channel_id}")
                    await asyncio.sleep(5)
                    continue

                # Configure FFmpeg
                discord.FFmpegPCMAudio.DEFAULT_EXECUTABLE = Config.FFMPEG_PATH

                # Connect to voice
                if await self._connect_to_voice(channel):
                    retry_count = 0  # Reset retry count on successful connection
                else:
                    # Connection failed, implement exponential backoff
                    retry_count += 1
                    if retry_count >= max_retries:
                        logger.error(f"Failed to connect after {max_retries} attempts")
                        await asyncio.sleep(max_delay)
                        retry_count = 0  # Reset count and try again
                    else:
                        delay = min(base_delay * (2 ** retry_count), max_delay)
                        logger.info(f"Connection attempt {retry_count} failed, waiting {delay}s before retry")
                        await asyncio.sleep(delay)

            except Exception as e:
                logger.error(f"Connection loop error: {e}")
                await self._cleanup_voice()
                # Use exponential backoff for errors too
                retry_count += 1
                delay = min(base_delay * (2 ** retry_count), max_delay)
                await asyncio.sleep(delay)

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

        try:
            # Log voice state change
            logger.debug(
                f"Voice state update: member={member.name} "
                f"before={before.channel.name if before.channel else 'None'} "
                f"after={after.channel.name if after.channel else 'None'} "
                f"deaf={after.deaf} self_deaf={after.self_deaf}"
            )

            # Handle bot's own voice state
            if member.id == self.bot.user.id:
                if after.channel:
                    logger.info(f"Bot voice state changed in channel {after.channel.name}")
                    
                    # Handle deafened state
                    if after.deaf or after.self_deaf:
                        try:
                            logger.info("Attempting to undeafen bot")
                            await member.guild.change_voice_state(
                                channel=after.channel,
                                self_deaf=False,
                                self_mute=False
                            )
                            logger.info("Successfully undeafened bot")
                        except Exception as e:
                            logger.error(f"Failed to undeafen bot: {e}")
                            # Try to reconnect if we can't undeafen
                            await self._cleanup_voice()
                            channel = self.bot.get_channel(int(self.channel_id))
                            if channel:
                                await self._connect_to_voice(channel)
                    
                    # Update session ID
                    if self.session_id != after.session_id:
                        old_session = self.session_id
                        self.session_id = after.session_id
                        logger.info(f"Updated session ID: {old_session} -> {self.session_id}")
                        
                    # Verify connection health
                    if not await self._verify_connection(self.voice):
                        logger.warning("Voice connection unhealthy after state change")
                        await self._cleanup_voice()
                        channel = self.bot.get_channel(int(self.channel_id))
                        if channel:
                            await self._connect_to_voice(channel)
                else:
                    logger.info("Bot left voice channel")
                    await self._cleanup_voice()
                return

            # Handle user joins
            if not member.bot and after.channel and str(after.channel.id) == self.channel_id:
                if before.channel != after.channel:
                    logger.info(f"User {member.name} joined welcome channel")
                    async with self.lock:
                        # Verify connection before playing
                        if not self.voice or not await self._verify_connection(self.voice):
                            logger.warning("Voice connection unhealthy before welcome sound")
                            channel = self.bot.get_channel(int(self.channel_id))
                            if channel:
                                await self._connect_to_voice(channel)
                        
                        await self._play_welcome(member.name)

        except Exception as e:
            logger.error(f"Error in voice state update: {e}")
            # Try to recover voice state
            try:
                await self._cleanup_voice()
                channel = self.bot.get_channel(int(self.channel_id))
                if channel:
                    await self._connect_to_voice(channel)
            except Exception as recovery_error:
                logger.error(f"Failed to recover from voice state error: {recovery_error}")

    @commands.command()
    async def rejoin(self, ctx):
        """Force reconnection"""
        try:
            await ctx.send("🔄 Reconnecting to voice channel...")
            
            # Clean up existing connection
            await self._cleanup_voice()
            
            channel = self.bot.get_channel(int(self.channel_id))
            if not channel:
                await ctx.send("❌ Voice channel not found")
                return

            # Connect to voice
            if await self._connect_to_voice(channel):
                await ctx.send("✅ Successfully reconnected!")
            else:
                await ctx.send("❌ Connection verification failed")
                
        except Exception as e:
            await ctx.send(f"❌ Error during reconnection: {str(e)}")
            logger.error(f"Rejoin error: {e}")
            await self._cleanup_voice()

    def cog_unload(self):
        """Clean up when cog is unloaded"""
        if self._connection_task:
            self._connection_task.cancel()

async def setup(bot):
    await bot.add_cog(VoiceCommands(bot))
