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
        # Connect to welcome channel on startup and start connection check
        bot.loop.create_task(self._connect_to_channel())
        bot.loop.create_task(self._check_connection())

    async def _check_connection(self):
        """Periodically check and ensure we stay connected"""
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            if not self.voice_client or not self.voice_client.is_connected():
                logger.info("Voice client disconnected, reconnecting...")
                await self._connect_to_channel()
            await asyncio.sleep(30)  # Check every 30 seconds

    async def _connect_to_channel(self):
        """Connect to the welcome channel and stay there"""
        await self.bot.wait_until_ready()
        await asyncio.sleep(5)  # Wait a bit after bot is ready
        
        try:
            # Clean up existing connection if any
            if self.voice_client:
                try:
                    await self.voice_client.disconnect(force=True)
                except:
                    pass
                self.voice_client = None
                await asyncio.sleep(2)  # Wait after disconnect
            
            channel = self.bot.get_channel(self.welcome_channel_id)
            if channel:
                if channel.guild.voice_client:
                    await channel.guild.voice_client.disconnect(force=True)
                    await asyncio.sleep(2)
                
                self.voice_client = await channel.connect(self_deaf=False, timeout=30.0)
                logger.info(f"Connected to welcome channel {channel.name}")
            else:
                logger.error("Could not find welcome channel")
                await asyncio.sleep(5)
                await self._connect_to_channel()
        except Exception as e:
            logger.error(f"Failed to connect to welcome channel: {e}")
            # Clean up on error
            if self.voice_client:
                try:
                    await self.voice_client.disconnect(force=True)
                except:
                    pass
                self.voice_client = None
            # Try to reconnect
            await asyncio.sleep(5)
            await self._connect_to_channel()

    @Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Play welcome sound when someone joins the channel"""
        # Ignore bot's own updates
        if member.bot:
            return

        # Check if member joined the welcome channel
        if after.channel and after.channel.id == self.welcome_channel_id and before.channel != after.channel:
            # Check if we need to reconnect
            if not self.voice_client or not self.voice_client.is_connected():
                await self._connect_to_channel()
                await asyncio.sleep(1)  # Wait for connection

            if self.voice_client and self.voice_client.is_connected():
                try:
                    # Play welcome sound
                    audio_source = discord.FFmpegPCMAudio(
                        '/root/ArabLife/welcome.mp3',
                        options='-loglevel warning'
                    )
                    if not self.voice_client.is_playing():
                        self.voice_client.play(audio_source)
                        logger.info(f"Playing welcome sound for {member.name}")
                except Exception as e:
                    logger.error(f"Error playing welcome sound: {e}")

    @Cog.listener()
    async def on_voice_client_disconnect(self):
        """Reconnect if we get disconnected"""
        logger.info("Voice client disconnected, reconnecting...")
        await self._connect_to_channel()

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(VoiceCommands(bot))
