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
        self.log_channel_id = 1327648816874262549
        self.voice_client = None
        # Connect to welcome channel on startup
        bot.loop.create_task(self._connect())

    async def _log_to_discord(self, message):
        """Log message to Discord channel"""
        try:
            if self.bot.is_ready():
                channel = self.bot.get_channel(self.log_channel_id)
                if channel:
                    await channel.send(f"```\n{message}\n```")
        except Exception as e:
            logger.error(f"Failed to send log to Discord: {e}")

    def log(self, message, error=False):
        """Log to both console and Discord"""
        if error:
            logger.error(message)
        else:
            logger.info(message)
        asyncio.create_task(self._log_to_discord(message))

    async def _connect(self):
        """Connect to the welcome channel"""
        await self.bot.wait_until_ready()
        await asyncio.sleep(5)  # Wait for bot to fully initialize
        
        try:
            channel = self.bot.get_channel(self.welcome_channel_id)
            if not channel:
                self.log("Could not find welcome channel", error=True)
                return

            # Connect to channel
            self.voice_client = await channel.connect(self_deaf=False)
            
            # Wait a bit before checking connection
            await asyncio.sleep(1)
            
            if self.voice_client and self.voice_client.is_connected():
                self.log(f"Successfully connected to {channel.name}")
            else:
                self.log("Failed to establish stable connection", error=True)
                self.voice_client = None
                # Try to reconnect
                await asyncio.sleep(5)
                self.bot.loop.create_task(self._connect())
                
        except Exception as e:
            self.log(f"Connection error: {str(e)}", error=True)
            self.voice_client = None
            # Try to reconnect
            await asyncio.sleep(5)
            self.bot.loop.create_task(self._connect())

    @Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Play welcome sound when someone joins"""
        if member.bot:
            return

        if after.channel and after.channel.id == self.welcome_channel_id and before.channel != after.channel:
            try:
                if not self.voice_client or not self.voice_client.is_connected():
                    self.log("Voice client disconnected, reconnecting...", error=True)
                    await self._connect()
                    await asyncio.sleep(1)

                if self.voice_client and self.voice_client.is_connected():
                    audio = discord.FFmpegPCMAudio('/root/ArabLife/welcome.mp3')
                    if not self.voice_client.is_playing():
                        self.voice_client.play(audio)
                        self.log(f"Playing welcome sound for {member.name}")
            except Exception as e:
                self.log(f"Playback error: {str(e)}", error=True)

    @Cog.listener()
    async def on_voice_client_disconnect(self):
        """Reconnect on disconnect"""
        self.log("Voice client disconnected, reconnecting...", error=True)
        self.voice_client = None
        await asyncio.sleep(5)
        await self._connect()

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(VoiceCommands(bot))
