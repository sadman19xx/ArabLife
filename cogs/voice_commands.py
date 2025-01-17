import discord
from discord.ext import commands
import logging

logger = logging.getLogger('discord')

class VoiceCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = 1309595750878937240

    async def _ensure_voice(self, channel):
        """Ensure bot is in voice channel"""
        try:
            # If already connected to this channel, return current client
            if channel.guild.voice_client and channel.guild.voice_client.channel == channel:
                return channel.guild.voice_client

            # Disconnect if connected to wrong channel
            if channel.guild.voice_client:
                await channel.guild.voice_client.disconnect()

            # Connect to channel
            voice = await channel.connect(
                reconnect=True,
                timeout=None,
                self_deaf=False
            )

            # Set voice state
            await channel.guild.change_voice_state(
                channel=channel,
                self_deaf=False,
                self_mute=False
            )

            return voice

        except Exception as e:
            logger.error(f"Voice connection error: {e}")
            return None

    @commands.Cog.listener()
    async def on_ready(self):
        """Connect when bot is ready"""
        channel = self.bot.get_channel(self.channel_id)
        if channel:
            await self._ensure_voice(channel)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Handle voice states"""
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            return

        # Handle bot state changes
        if member.id == self.bot.user.id:
            if not after.channel or after.channel.id != self.channel_id or after.deaf:
                voice = await self._ensure_voice(channel)
                if not voice:
                    logger.error("Failed to reconnect bot")
            return

        # Handle user joins
        if not member.bot and after.channel and after.channel.id == self.channel_id:
            if before.channel != after.channel:
                try:
                    voice = await self._ensure_voice(channel)
                    if voice and voice.is_connected() and not voice.is_playing():
                        voice.play(discord.FFmpegPCMAudio('welcome.mp3'))
                        logger.info(f"Playing welcome for {member.name}")
                except Exception as e:
                    logger.error(f"Error playing welcome: {e}")

async def setup(bot):
    await bot.add_cog(VoiceCommands(bot))
