import discord
from discord.ext import commands
from discord import app_commands
from discord.ext.commands import Cog
import logging
import os
import asyncio
from config import Config

logger = logging.getLogger('discord')

class VoiceCommands(Cog):
    """Cog for voice-related commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.welcome_channel_id = 1309595750878937240
        self.voice_client = None
        # Connect to welcome channel on startup
        bot.loop.create_task(self._initial_connect())

    async def _initial_connect(self):
        """Initial connection attempt"""
        await self.bot.wait_until_ready()
        await asyncio.sleep(5)  # Wait for bot to fully initialize
        await self._connect()

    async def _connect(self):
        """Connect to the welcome channel"""
        try:
            # Get channel
            channel = self.bot.get_channel(self.welcome_channel_id)
            if not channel:
                logger.error("Could not find welcome channel")
                return

            # Check if already connected
            if channel.guild.voice_client and channel.guild.voice_client.is_connected():
                self.voice_client = channel.guild.voice_client
                logger.info("Using existing voice connection")
                return

            # Connect to channel
            self.voice_client = await channel.connect(
                timeout=60.0,
                reconnect=True,
                self_deaf=False
            )
            logger.info(f"Connected to channel: {channel.name}")

        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            self.voice_client = None

    async def _play_welcome(self, member_name):
        """Play welcome sound"""
        try:
            if self.voice_client and self.voice_client.is_connected():
                if not self.voice_client.is_playing():
                    audio = discord.FFmpegPCMAudio('/root/ArabLife/welcome.mp3')
                    self.voice_client.play(
                        audio,
                        after=lambda e: logger.error(f"Playback error: {e}") if e else None
                    )
                    logger.info(f"Playing welcome sound for {member_name}")
        except Exception as e:
            logger.error(f"Error playing welcome sound: {str(e)}")

    @Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Handle voice state updates"""
        if member.bot:
            return

        if after.channel and after.channel.id == self.welcome_channel_id and before.channel != after.channel:
            # Ensure we're connected
            if not self.voice_client or not self.voice_client.is_connected():
                await self._connect()
                await asyncio.sleep(1)  # Wait for connection to stabilize

            # Play welcome sound
            await self._play_welcome(member.name)

    @Cog.listener()
    async def on_voice_client_disconnect(self):
        """Handle disconnection"""
        logger.info("Voice client disconnected")
        self.voice_client = None
        await asyncio.sleep(5)  # Wait before reconnecting
        await self._connect()

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(VoiceCommands(bot))
