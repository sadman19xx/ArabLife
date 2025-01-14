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
        self.welcome_sound_path = os.path.join(os.path.dirname(__file__), '..', 'welcome.mp3')
        self.voice_client = None

    async def play_welcome_sound(self, voice_channel: discord.VoiceChannel):
        """Play welcome sound in voice channel"""
        try:
            # Check if sound file exists
            if not os.path.exists(self.welcome_sound_path):
                self.logger.error(f"Welcome sound file not found at {self.welcome_sound_path}")
                return

            # Connect to voice channel if not already connected
            if not self.voice_client or not self.voice_client.is_connected():
                self.voice_client = await voice_channel.connect()
            elif self.voice_client.channel != voice_channel:
                await self.voice_client.move_to(voice_channel)

            # Play the welcome sound
            if not self.voice_client.is_playing():
                audio_source = discord.FFmpegPCMAudio(
                    self.welcome_sound_path,
                    executable=Config.FFMPEG_PATH
                )
                self.voice_client.play(
                    audio_source,
                    after=lambda e: self.bot.loop.create_task(self.cleanup_voice())
                )

        except Exception as e:
            self.logger.error(f"Error playing welcome sound: {str(e)}")

    async def cleanup_voice(self):
        """Cleanup voice client after playing sound"""
        try:
            await asyncio.sleep(1)  # Wait a bit to ensure audio is finished
            if self.voice_client and self.voice_client.is_connected():
                await self.voice_client.disconnect()
                self.voice_client = None
        except Exception as e:
            self.logger.error(f"Error cleaning up voice client: {str(e)}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Play welcome sound when a member joins"""
        if member.bot:
            return

        try:
            # Play welcome sound if voice channel is configured
            voice_channel = self.bot.get_channel(Config.WELCOME_VOICE_CHANNEL_ID)
            if voice_channel and isinstance(voice_channel, discord.VoiceChannel):
                await self.play_welcome_sound(voice_channel)
        except Exception as e:
            self.logger.error(f"Error handling member join: {str(e)}")

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(WelcomeCommands(bot))
