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

    async def _trigger_welcome_sound(self, member_name: str):
        """Trigger welcome sound through voice commands"""
        try:
            voice_commands = self.bot.get_cog('VoiceCommands')
            if voice_commands:
                await voice_commands._play_welcome(member_name)
            else:
                self.logger.error("VoiceCommands cog not found")
        except Exception as e:
            self.logger.error(f"Error triggering welcome sound: {str(e)}")

    @commands.Cog.listener()
    async def on_ready(self):
        """Initialize welcome channel settings when bot starts"""
        try:
            voice_channel = self.bot.get_channel(Config.WELCOME_VOICE_CHANNEL_ID)
            if not voice_channel:
                self.logger.error(f"Could not find voice channel with ID {Config.WELCOME_VOICE_CHANNEL_ID}")
                return
                
            if not isinstance(voice_channel, discord.VoiceChannel):
                self.logger.error(f"Channel with ID {Config.WELCOME_VOICE_CHANNEL_ID} is not a voice channel")
                return

            self.logger.info(f"Welcome channel configured: {voice_channel.name}")
                
        except Exception as e:
            self.logger.error(f"Error initializing welcome channel: {str(e)}")

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
                await self._trigger_welcome_sound(member.name)
        except Exception as e:
            self.logger.error(f"Error handling voice state update: {str(e)}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Play welcome sound when a member joins the server"""
        if member.bot:
            return

        try:
            self.logger.info(f"Member {member.name} joined server")
            await self._trigger_welcome_sound(member.name)
        except Exception as e:
            self.logger.error(f"Error handling member join: {str(e)}")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Handle member leave event"""
        if not member.bot:
            self.logger.info(f"Member {member.name} left server")
        
async def setup(bot):
    """Setup function for loading the cog"""
    cog = WelcomeCommands(bot)
    await bot.add_cog(cog)
