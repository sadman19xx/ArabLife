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
        self.is_connecting = False
        # Connect to welcome channel on startup
        bot.loop.create_task(self._connect())
        bot.loop.create_task(self._heartbeat())

    async def _heartbeat(self):
        """Keep connection alive"""
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                channel = self.bot.get_channel(self.welcome_channel_id)
                if channel and channel.guild.voice_client:
                    # Use guild's voice client
                    self.voice_client = channel.guild.voice_client
                    if not self.voice_client.is_connected():
                        logger.info("Voice client disconnected in heartbeat")
                        self.voice_client = None
                        if not self.is_connecting:
                            await self._connect()
                elif not self.is_connecting:
                    await self._connect()
            except Exception as e:
                logger.error(f"Heartbeat error: {str(e)}")
            await asyncio.sleep(30)

    async def _connect(self):
        """Connect to the welcome channel"""
        if self.is_connecting:
            return
            
        self.is_connecting = True
        try:
            await self.bot.wait_until_ready()
            channel = self.bot.get_channel(self.welcome_channel_id)
            if not channel:
                logger.error("Could not find welcome channel")
                return

            # Clean up existing connection
            if channel.guild.voice_client:
                await channel.guild.voice_client.disconnect(force=True)
                await asyncio.sleep(2)

            # Connect to channel
            self.voice_client = await channel.connect(self_deaf=False)
            logger.info(f"Connected to channel: {channel.name}")
            
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            self.voice_client = None
        finally:
            self.is_connecting = False

    @Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Play welcome sound when someone joins"""
        if member.bot:
            return

        if after.channel and after.channel.id == self.welcome_channel_id and before.channel != after.channel:
            try:
                channel = self.bot.get_channel(self.welcome_channel_id)
                if channel and channel.guild.voice_client:
                    self.voice_client = channel.guild.voice_client
                    if self.voice_client.is_connected():
                        audio = discord.FFmpegPCMAudio('/root/ArabLife/welcome.mp3')
                        if not self.voice_client.is_playing():
                            self.voice_client.play(audio)
                            logger.info(f"Playing welcome sound for {member.name}")
                    else:
                        logger.info("Voice client not connected, reconnecting...")
                        await self._connect()
                else:
                    logger.info("No voice client, connecting...")
                    await self._connect()
            except Exception as e:
                logger.error(f"Playback error: {str(e)}")

    @Cog.listener()
    async def on_voice_client_disconnect(self):
        """Handle disconnect"""
        logger.info("Voice client disconnected")
        self.voice_client = None
        if not self.is_connecting:
            await self._connect()

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(VoiceCommands(bot))
