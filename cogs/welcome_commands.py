import discord
import os
import asyncio
from discord.ext import commands
from config import Config
import logging

class WelcomeCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        self.voice_client = None
        self.reconnect_task = None

    async def ensure_voice_connection(self):
        """Ensure bot is connected to welcome channel"""
        try:
            channel = self.bot.get_channel(Config.WELCOME_VOICE_CHANNEL_ID)
            if not channel:
                self.logger.error(f"Could not find welcome channel with ID {Config.WELCOME_VOICE_CHANNEL_ID}")
                return False

            if not isinstance(channel, discord.VoiceChannel):
                self.logger.error(f"Channel with ID {Config.WELCOME_VOICE_CHANNEL_ID} is not a voice channel")
                return False

            # If we're already connected to the right channel, verify connection
            if self.voice_client and self.voice_client.is_connected():
                if self.voice_client.channel.id == Config.WELCOME_VOICE_CHANNEL_ID:
                    # Check if connection is healthy
                    if hasattr(self.voice_client, 'ws') and self.voice_client.ws and not self.voice_client.ws.closed:
                        return True
                    else:
                        self.logger.warning("Unhealthy voice connection, reconnecting...")
                        await self.voice_client.disconnect(force=True)
                else:
                    # Connected to wrong channel
                    await self.voice_client.disconnect(force=True)

            # Connect to welcome channel
            self.voice_client = await channel.connect(
                timeout=Config.VOICE_TIMEOUT,
                reconnect=True,
                self_deaf=False,
                self_mute=False
            )
            
            # Ensure we're not deafened
            await asyncio.sleep(1)
            await channel.guild.change_voice_state(
                channel=channel,
                self_deaf=False,
                self_mute=False
            )
            
            self.logger.info(f"Connected to welcome channel: {channel.name}")
            return True

        except Exception as e:
            self.logger.error(f"Error ensuring voice connection: {str(e)}")
            return False

    async def play_welcome_sound(self, member_name: str):
        """Play welcome sound for member"""
        try:
            if not await self.ensure_voice_connection():
                return

            if self.voice_client.is_playing():
                self.voice_client.stop()

            # Create FFmpeg audio source
            audio_source = discord.FFmpegPCMAudio(
                Config.WELCOME_SOUND_PATH,
                executable=Config.FFMPEG_PATH
            )
            
            # Add volume transformation
            audio_source = discord.PCMVolumeTransformer(
                audio_source,
                volume=Config.WELCOME_SOUND_VOLUME
            )

            self.voice_client.play(
                audio_source,
                after=lambda e: self.logger.error(f"Error playing welcome sound: {str(e)}") if e else None
            )
            
            self.logger.info(f"Playing welcome sound for {member_name}")

        except Exception as e:
            self.logger.error(f"Error playing welcome sound: {str(e)}")

    async def maintain_voice_connection(self):
        """Task to maintain voice connection"""
        while True:
            try:
                await self.ensure_voice_connection()
                await asyncio.sleep(30)  # Check connection every 30 seconds
            except Exception as e:
                self.logger.error(f"Error in maintain_voice_connection task: {str(e)}")
                await asyncio.sleep(5)  # Wait before retrying on error

    @commands.Cog.listener()
    async def on_ready(self):
        """Initialize welcome channel connection when bot starts"""
        try:
            # Start connection maintenance task
            if self.reconnect_task is None or self.reconnect_task.done():
                self.reconnect_task = asyncio.create_task(self.maintain_voice_connection())
                
            await self.ensure_voice_connection()
            self.logger.info("Welcome system initialized")
                
        except Exception as e:
            self.logger.error(f"Error initializing welcome system: {str(e)}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Handle member joining voice channel"""
        if member.bot:
            return

        try:
            # Check if member joined the welcome channel
            if (before.channel != after.channel and 
                after.channel and 
                after.channel.id == Config.WELCOME_VOICE_CHANNEL_ID):
                self.logger.info(f"Member {member.name} joined welcome channel")
                await self.play_welcome_sound(member.name)
        except Exception as e:
            self.logger.error(f"Error handling voice state update: {str(e)}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Play welcome sound when a member joins the server"""
        if member.bot:
            return

        try:
            # Wait a moment for voice connection to stabilize
            await asyncio.sleep(1)
            
            self.logger.info(f"Member {member.name} joined server, playing welcome sound")
            await self.play_welcome_sound(member.name)
        except Exception as e:
            self.logger.error(f"Error handling member join: {str(e)}")

    def cog_unload(self):
        """Cleanup when cog is unloaded"""
        if self.reconnect_task:
            self.reconnect_task.cancel()
        if self.voice_client:
            asyncio.create_task(self.voice_client.disconnect(force=True))
        
async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(WelcomeCommands(bot))
