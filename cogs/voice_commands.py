import discord
from discord.ext import commands
from discord import app_commands
from discord.ext.commands import Cog
import logging
import os
import asyncio
from collections import deque
from config import Config

logger = logging.getLogger('discord')

class VoiceCommands(Cog):
    """Cog for voice-related commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.welcome_channel_id = 1309595750878937240
        self.log_channel_id = 1327648816874262549  # Dedicated logs channel
        self.voice_client = None
        self.audio_queue = deque()  # Queue for handling multiple join events
        self.is_playing = False
        self.reconnect_lock = asyncio.Lock()
        self.heartbeat_task = None
        self.last_heartbeat = None
        self.connection_retries = 0
        # Connect to welcome channel on startup
        bot.loop.create_task(self._initial_connect())
        # Start connection heartbeat
        bot.loop.create_task(self._connection_heartbeat())

    async def _log_to_channel(self, message):
        """Send log message to Discord channel"""
        try:
            channel = self.bot.get_channel(self.log_channel_id)
            if channel:
                await channel.send(f"```\n{message}\n```")
        except Exception as e:
            logger.error(f"Failed to send log to channel: {str(e)}")

    async def _connection_heartbeat(self):
        """Monitor and maintain voice connection"""
        await self.bot.wait_until_ready()
        await asyncio.sleep(30)  # Initial delay to let bot fully initialize
        
        while not self.bot.is_closed():
            try:
                current_time = asyncio.get_event_loop().time()
                
                # Only check connection if we haven't checked recently
                if not self.last_heartbeat or current_time - self.last_heartbeat > 30:
                    channel = self.bot.get_channel(self.welcome_channel_id)
                    if not channel:
                        await self._log_to_channel("⚠️ Could not find welcome channel")
                        await asyncio.sleep(30)
                        continue

                    # Check if we need to establish initial connection
                    if not self.voice_client:
                        await self._log_to_channel("🔄 No voice connection, establishing connection...")
                        async with self.reconnect_lock:
                            await self._connect()
                    # Check if connection is in correct channel and not deafened
                    elif self.voice_client.is_connected():
                        voice_state = self.voice_client.guild.me.voice
                        if voice_state:
                            if voice_state.channel.id != self.welcome_channel_id:
                                await self._log_to_channel("🔄 Bot in wrong channel, moving back...")
                                await self._connect()
                            elif voice_state.deaf or voice_state.self_deaf:
                                await self._log_to_channel("🔊 Bot is deafened, undeafening...")
                                try:
                                    await self.voice_client.guild.change_voice_state(
                                        channel=channel,
                                        self_deaf=False,
                                        self_mute=False
                                    )
                                except Exception as e:
                                    await self._log_to_channel(f"❌ Failed to undeafen: {str(e)}")
                    else:
                        # Connection exists but disconnected
                        await self._log_to_channel("⚠️ Voice connection lost, reconnecting...")
                        async with self.reconnect_lock:
                            await self._connect()
                    
                    self.last_heartbeat = current_time
                
            except Exception as e:
                error_msg = f"❌ Heartbeat error: {str(e)}"
                logger.error(error_msg)
                await self._log_to_channel(error_msg)
            
            await asyncio.sleep(30)  # Reduced check frequency to prevent spam

    async def _initial_connect(self):
        """Initial connection attempt"""
        await self.bot.wait_until_ready()
        await asyncio.sleep(30)  # Wait longer for bot to fully initialize
        
        try:
            # Get channel
            channel = self.bot.get_channel(self.welcome_channel_id)
            if not channel:
                logger.error("Could not find welcome channel")
                return

            # Clean up any existing connections
            try:
                if channel.guild.voice_client:
                    await channel.guild.voice_client.disconnect(force=True)
                    await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Error cleaning up existing connection: {str(e)}")

            # Set initial voice state
            try:
                await channel.guild.change_voice_state(
                    channel=None,  # Disconnect first
                    self_deaf=False,
                    self_mute=False
                )
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Error setting initial voice state: {str(e)}")

            # Now try to connect
            self.voice_client = await channel.connect(
                timeout=120.0,
                reconnect=True
            )

            if self.voice_client and self.voice_client.is_connected():
                await self._log_to_channel("✅ Initial connection successful")
                logger.info("Initial connection successful")
            else:
                await self._log_to_channel("❌ Initial connection failed, will retry through heartbeat")
                logger.error("Initial connection failed")
                self.voice_client = None

        except Exception as e:
            error_msg = f"Initial connection error: {str(e)}"
            logger.error(error_msg)
            await self._log_to_channel(f"❌ {error_msg}")
            self.voice_client = None

    async def _connect(self):
        """Connect to the welcome channel"""
        MAX_RETRIES = 3
        RETRY_DELAY = 15  # Increased delay between attempts
        
        for attempt in range(MAX_RETRIES):
            try:
                # Get channel
                channel = self.bot.get_channel(self.welcome_channel_id)
                if not channel:
                    logger.error("Could not find welcome channel")
                    return

                # Clean up any existing voice clients without forcing
                if self.voice_client:
                    try:
                        self.voice_client = None
                    except Exception as e:
                        logger.error(f"Error cleaning up voice client: {str(e)}")

                # Wait for any existing voice clients to fully clean up
                await asyncio.sleep(5)
                
                # Ensure we're starting fresh
                try:
                    if channel.guild.voice_client:
                        await channel.guild.voice_client.cleanup()
                except Exception:
                    pass

                await asyncio.sleep(2)

                # Connect to channel first
                self.voice_client = await channel.connect(
                    timeout=60.0,
                    reconnect=True  # Let discord.py handle reconnection
                )

                # Wait for connection to establish
                await asyncio.sleep(2)

                # Now set voice state
                if self.voice_client and self.voice_client.is_connected():
                    try:
                        await channel.guild.change_voice_state(
                            channel=channel,
                            self_deaf=False,
                            self_mute=False
                        )
                    except Exception as e:
                        logger.error(f"Error setting voice state: {str(e)}")
                        # Don't raise here, try to continue
                
                # Verify connection
                if not self.voice_client or not self.voice_client.is_connected():
                    raise Exception("Failed to establish voice connection")

                # Wait for connection to fully establish
                await asyncio.sleep(5)
                
                # Final connection check
                if self.voice_client and self.voice_client.is_connected():
                    logger.info(f"Successfully connected to channel: {channel.name} (attempt {attempt + 1})")
                    await self._log_to_channel(f"✅ Connected to voice channel (attempt {attempt + 1})")
                    return
                
            except Exception as e:
                error_msg = f"Connection error (attempt {attempt + 1}): {str(e)}"
                logger.error(error_msg)
                await self._log_to_channel(f"❌ {error_msg}")
                
                # Clean up failed connection
                if self.voice_client:
                    try:
                        await self.voice_client.disconnect(force=True)
                    except:
                        pass
                self.voice_client = None
                
                # Wait before retry
                if attempt < MAX_RETRIES - 1:
                    retry_msg = f"Retrying connection in {RETRY_DELAY} seconds..."
                    logger.info(retry_msg)
                    await self._log_to_channel(f"⏳ {retry_msg}")
                    await asyncio.sleep(RETRY_DELAY)
                else:
                    error_msg = "Max connection attempts reached"
                    logger.error(error_msg)
                    await self._log_to_channel(f"❌ {error_msg}")

    async def _play_next(self):
        """Play next audio in queue if any"""
        if self.audio_queue and not self.is_playing:
            member_name = self.audio_queue.popleft()
            try:
                if self.voice_client and self.voice_client.is_connected():
                    try:
                        # Use relative path from project root
                        audio = discord.FFmpegPCMAudio('welcome.mp3')
                        
                        def after_playing(error):
                            if error:
                                logger.error(f"Playback error: {error}")
                            # Schedule _play_next in the event loop
                            asyncio.run_coroutine_threadsafe(self._after_playing(), self.bot.loop)
                        
                        self.is_playing = True
                        self.voice_client.play(audio, after=after_playing)
                        logger.info(f"Playing welcome sound for {member_name}")
                    except Exception as e:
                        logger.error(f"FFmpeg error: {str(e)}")
                        self.is_playing = False
                        # Try to play next in queue if this one failed
                        await self._play_next()
            except Exception as e:
                logger.error(f"Error playing welcome sound: {str(e)}")
                self.is_playing = False
                # Try to play next in queue if this one failed
                await self._play_next()

    async def _after_playing(self):
        """Callback for after audio finishes playing"""
        self.is_playing = False
        await self._play_next()  # Play next in queue if any

    async def _play_welcome(self, member_name):
        """Add member to audio queue"""
        self.audio_queue.append(member_name)
        logger.info(f"Added {member_name} to welcome audio queue")
        await self._play_next()

    @Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Handle voice state updates"""
        # Handle bot's voice state changes
        if member.id == self.bot.user.id:
            async with self.reconnect_lock:  # Prevent concurrent voice state changes
                # Log state change
                state_msg = f"Voice state update: {before.channel} -> {after.channel}"
                if after.deaf != before.deaf:
                    state_msg += f" (deaf: {before.deaf} -> {after.deaf})"
                await self._log_to_channel(f"ℹ️ {state_msg}")

                # Handle different scenarios
                if after.channel and after.channel.id != self.welcome_channel_id:
                    # Wrong channel - move back
                    try:
                        channel = self.bot.get_channel(self.welcome_channel_id)
                        if channel:
                            await asyncio.sleep(1)  # Wait for state to settle
                            await member.guild.change_voice_state(
                                channel=channel,
                                self_deaf=False,
                                self_mute=False
                            )
                            await self._log_to_channel("🔄 Moved back to welcome channel")
                    except Exception as e:
                        await self._log_to_channel(f"❌ Failed to move: {str(e)}")
                    return

                elif after.deaf or after.self_deaf:
                    # Deafened - undeafen
                    try:
                        await asyncio.sleep(1)  # Wait for state to settle
                        await member.guild.change_voice_state(
                            channel=after.channel,
                            self_deaf=False,
                            self_mute=False
                        )
                        await self._log_to_channel("🔊 Undeafened")
                    except Exception as e:
                        await self._log_to_channel(f"❌ Failed to undeafen: {str(e)}")
                    return

                elif not after.channel and before.channel:
                    # Disconnected - reconnect
                    await self._log_to_channel("⚠️ Disconnected, reconnecting...")
                    await asyncio.sleep(2)  # Wait before reconnecting
                    await self._connect()
                    return

        # Handle other users
        if not member.bot and after.channel and after.channel.id == self.welcome_channel_id:
            # Only trigger for users joining (not leaving or moving within the channel)
            if before.channel != after.channel:
                await self._log_to_channel(f"👋 User {member.name} joined, playing welcome sound")
                # Ensure we're connected
                if not self.voice_client or not self.voice_client.is_connected():
                    await self._connect()
                    await asyncio.sleep(1)

                # Play welcome sound
                await self._play_welcome(member.name)

    @Cog.listener()
    async def on_voice_client_disconnect(self):
        """Handle disconnection"""
        await self._log_to_channel("⚠️ Voice client disconnected, initiating recovery...")
        
        # Clear voice client reference
        old_client = self.voice_client
        self.voice_client = None
        
        try:
            # Clean up old client properly
            if old_client:
                try:
                    await old_client.cleanup()
                except:
                    pass
            
            # Wait for cleanup
            await asyncio.sleep(5)
            
            # Get channel
            channel = self.bot.get_channel(self.welcome_channel_id)
            if not channel:
                await self._log_to_channel("❌ Could not find welcome channel")
                return
                
            # Clean up any existing guild voice clients
            if channel.guild.voice_client:
                try:
                    await channel.guild.voice_client.cleanup()
                except:
                    pass
                await asyncio.sleep(2)
            
            # Connect with fresh state
            self.voice_client = await channel.connect(
                timeout=60.0,
                reconnect=True
            )
            
            if not self.voice_client or not self.voice_client.is_connected():
                raise Exception("Failed to establish connection")
            
            # Wait for connection to stabilize
            await asyncio.sleep(2)
            
            # Set voice state
            await channel.guild.change_voice_state(
                channel=channel,
                self_deaf=False,
                self_mute=False
            )
            
            # Final verification
            if self.voice_client and self.voice_client.is_connected():
                await self._log_to_channel("✅ Successfully recovered voice connection")
            else:
                raise Exception("Connection verification failed")
            
        except Exception as e:
            error_msg = f"❌ Recovery failed: {str(e)}"
            logger.error(error_msg)
            await self._log_to_channel(error_msg)
            
            # Schedule reconnection through heartbeat
            self.voice_client = None
            self.last_heartbeat = None  # Force heartbeat check

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(VoiceCommands(bot))
