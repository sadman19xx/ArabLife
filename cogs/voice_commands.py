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
        while not self.bot.is_closed():
            try:
                current_time = asyncio.get_event_loop().time()
                
                # Check if we need to force reconnection due to stale connection
                if self.last_heartbeat and current_time - self.last_heartbeat > 60:
                    await self._log_to_channel("⚠️ Connection appears stale, forcing reconnection...")
                    if self.voice_client:
                        await self.voice_client.disconnect(force=True)
                    self.voice_client = None
                
                # Check connection status
                if not self.voice_client or not self.voice_client.is_connected():
                    await self._log_to_channel("🔄 Voice connection lost, attempting to reconnect...")
                    async with self.reconnect_lock:
                        await self._connect()
                        if self.voice_client and self.voice_client.is_connected():
                            self.connection_retries = 0
                            await self._log_to_channel("✅ Successfully reconnected to voice channel")
                        else:
                            self.connection_retries += 1
                            await self._log_to_channel(f"❌ Reconnection attempt failed (attempt {self.connection_retries})")
                else:
                    # Ensure we're in the correct channel and not deafened
                    channel = self.bot.get_channel(self.welcome_channel_id)
                    if channel:
                        if self.voice_client.channel != channel:
                            await self._log_to_channel("🔄 Bot in wrong channel, moving to correct channel...")
                            await self._connect()
                        
                        # Check and fix deafened state
                        voice_state = self.voice_client.guild.me.voice
                        if voice_state and (voice_state.deaf or voice_state.self_deaf):
                            await self._log_to_channel("🔊 Bot is deafened, undeafening...")
                            await self.voice_client.guild.change_voice_state(
                                channel=channel,
                                self_deaf=False,
                                self_mute=False
                            )
                            # Double-check the change was applied
                            await asyncio.sleep(1)
                            if self.voice_client.guild.me.voice.deaf:
                                await self._log_to_channel("⚠️ Failed to undeafen, forcing reconnection...")
                                await self._connect()
                
                self.last_heartbeat = current_time
                
            except Exception as e:
                error_msg = f"❌ Heartbeat error: {str(e)}"
                logger.error(error_msg)
                await self._log_to_channel(error_msg)
            
            await asyncio.sleep(5)  # Check more frequently

    async def _initial_connect(self):
        """Initial connection attempt"""
        await self.bot.wait_until_ready()
        await asyncio.sleep(10)  # Wait longer for bot to fully initialize
        
        # Initial connection attempt
        await self._connect()
        
        # If initial connection failed, retry with increasing delays
        if not self.voice_client or not self.voice_client.is_connected():
            delays = [15, 30, 60]  # Increasing delays in seconds
            for delay in delays:
                logger.info(f"Initial connection failed, retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                await self._connect()
                if self.voice_client and self.voice_client.is_connected():
                    break

    async def _connect(self):
        """Connect to the welcome channel"""
        MAX_RETRIES = 3
        RETRY_DELAY = 5
        
        for attempt in range(MAX_RETRIES):
            try:
                # Get channel
                channel = self.bot.get_channel(self.welcome_channel_id)
                if not channel:
                    logger.error("Could not find welcome channel")
                    return

                # Disconnect if already connected but in a bad state
                if channel.guild.voice_client:
                    if not channel.guild.voice_client.is_connected():
                        await channel.guild.voice_client.disconnect(force=True)
                    elif channel.guild.voice_client.channel != channel:
                        await channel.guild.voice_client.disconnect(force=True)

                # Connect to channel with longer timeout
                self.voice_client = await channel.connect(
                    timeout=120.0,  # Increased timeout
                    reconnect=True,
                    self_deaf=False
                )
                
                # Wait for connection to stabilize
                await asyncio.sleep(2)
                
                if not self.voice_client.is_connected():
                    raise Exception("Voice client disconnected immediately after connection")
                
                # Ensure bot is not deafened after connection
                await asyncio.sleep(1)  # Wait before changing voice state
                await channel.guild.change_voice_state(
                    channel=channel,
                    self_deaf=False,
                    self_mute=False
                )
                
                logger.info(f"Successfully connected to channel: {channel.name} (attempt {attempt + 1})")
                return  # Successful connection
                
            except Exception as e:
                logger.error(f"Connection error (attempt {attempt + 1}): {str(e)}")
                if self.voice_client:
                    try:
                        await self.voice_client.disconnect(force=True)
                    except:
                        pass
                self.voice_client = None
                
                if attempt < MAX_RETRIES - 1:
                    logger.info(f"Retrying connection in {RETRY_DELAY} seconds...")
                    await asyncio.sleep(RETRY_DELAY)
                else:
                    logger.error("Max connection attempts reached")

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
            # If bot was moved to a different channel, move back
            if after.channel and after.channel.id != self.welcome_channel_id:
                try:
                    channel = self.bot.get_channel(self.welcome_channel_id)
                    await member.move_to(channel)
                    await self._log_to_channel("🔄 Bot was moved, returning to welcome channel")
                except Exception as e:
                    await self._log_to_channel(f"❌ Failed to return to welcome channel: {str(e)}")
                return
                
            # If bot was deafened, undeafen it
            if after.deaf or after.self_deaf:
                try:
                    await member.guild.change_voice_state(
                        channel=after.channel,
                        self_deaf=False,
                        self_mute=False
                    )
                    await self._log_to_channel("🔊 Undeafened bot")
                except Exception as e:
                    await self._log_to_channel(f"❌ Failed to undeafen: {str(e)}")
                return
                
            # If bot was disconnected, reconnect immediately
            if before.channel and not after.channel:
                await self._log_to_channel("⚠️ Bot was disconnected, reconnecting...")
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
        
        # Don't force disconnect, just clear our reference
        self.voice_client = None
        
        # Get channel and check if we can reconnect
        channel = self.bot.get_channel(self.welcome_channel_id)
        if not channel:
            await self._log_to_channel("❌ Could not find welcome channel for reconnection")
            return
            
        # Wait before attempting reconnection
        await asyncio.sleep(2)
        
        try:
            # Only clean up if we're in a different channel
            if channel.guild.voice_client and channel.guild.voice_client.channel != channel:
                await channel.guild.voice_client.disconnect(force=True)
                await asyncio.sleep(1)
                
            # Attempt to reconnect
            self.voice_client = await channel.connect(
                timeout=120.0,
                reconnect=True,
                self_deaf=False
            )
            
            # Wait for connection to stabilize
            await asyncio.sleep(1)
            
            # Ensure we're not deafened
            await channel.guild.change_voice_state(
                channel=channel,
                self_deaf=False,
                self_mute=False
            )
            
            await self._log_to_channel("✅ Successfully recovered voice connection")
            
        except Exception as e:
            error_msg = f"❌ Failed to recover connection: {str(e)}"
            logger.error(error_msg)
            await self._log_to_channel(error_msg)
            self.voice_client = None

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(VoiceCommands(bot))
