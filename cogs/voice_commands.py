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
        bot.loop.create_task(self._connect())

    async def _cleanup(self):
        """Clean up voice client"""
        try:
            if self.voice_client:
                await self.voice_client.disconnect(force=True)
                self.voice_client = None
        except:
            pass

    async def _connect(self):
        """Connect to the welcome channel"""
        await self.bot.wait_until_ready()
        await asyncio.sleep(5)  # Wait for bot to fully initialize
        
        try:
            channel = self.bot.get_channel(self.welcome_channel_id)
            if not channel:
                logger.error("Could not find welcome channel")
                return
                
            # Clean up any existing connections
            await self._cleanup()
            
            # Connect to channel
            self.voice_client = await channel.connect(self_deaf=False)
            logger.info(f"Connected to channel: {channel.name}")
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            await self._cleanup()  # Clean up on error
            # Simple retry after error
            await asyncio.sleep(5)
            self.bot.loop.create_task(self._connect())

    @Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Play welcome sound when someone joins"""
        if member.bot:
            return

        if after.channel and after.channel.id == self.welcome_channel_id and before.channel != after.channel:
            try:
                if self.voice_client and self.voice_client.is_connected():
                    audio = discord.FFmpegPCMAudio('/root/ArabLife/welcome.mp3')
                    if not self.voice_client.is_playing():
                        self.voice_client.play(audio)
                        logger.info(f"Playing welcome sound for {member.name}")
            except Exception as e:
                logger.error(f"Playback error: {str(e)}")

    @Cog.listener()
    async def on_voice_client_disconnect(self):
        """Reconnect on disconnect"""
        logger.info("Voice client disconnected, reconnecting...")
        await self._cleanup()  # Clean up first
        await asyncio.sleep(5)
        await self._connect()

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(VoiceCommands(bot))
