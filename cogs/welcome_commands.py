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
                
            # Check if FFMPEG path is set and valid
            if not Config.FFMPEG_PATH or not os.path.exists(Config.FFMPEG_PATH):
                self.logger.error(f"FFMPEG not found at {Config.FFMPEG_PATH}")
                return

            self.logger.info(f"Attempting to join voice channel {voice_channel.name}")

            # Connect to voice channel if not already connected
            try:
                if not self.voice_client or not self.voice_client.is_connected():
                    self.voice_client = await voice_channel.connect(timeout=20.0)
                    self.logger.info("Successfully connected to voice channel")
                elif self.voice_client.channel != voice_channel:
                    await self.voice_client.move_to(voice_channel)
                    self.logger.info("Successfully moved to new voice channel")
            except asyncio.TimeoutError:
                self.logger.error("Timeout while connecting to voice channel")
                return
            except discord.ClientException as e:
                self.logger.error(f"Failed to connect to voice channel: {str(e)}")
                return

            # Play the welcome sound
            if not self.voice_client.is_playing():
                try:
                    audio_source = discord.FFmpegPCMAudio(
                        self.welcome_sound_path,
                        executable=Config.FFMPEG_PATH
                    )
                    self.voice_client.play(
                        audio_source,
                        after=lambda e: self.bot.loop.create_task(self.cleanup_voice(e))
                    )
                    self.logger.info("Started playing welcome sound")
                except Exception as e:
                    self.logger.error(f"Failed to play audio: {str(e)}")
                    await self.cleanup_voice(None)
                    return

        except Exception as e:
            self.logger.error(f"Error playing welcome sound: {str(e)}")
            if self.voice_client and self.voice_client.is_connected():
                await self.cleanup_voice(None)

    async def cleanup_voice(self, error):
        """Cleanup voice client after playing sound"""
        try:
            if error:
                self.logger.error(f"Error during playback: {str(error)}")
                
            await asyncio.sleep(1)  # Wait a bit to ensure audio is finished
            
            if self.voice_client:
                if self.voice_client.is_playing():
                    self.voice_client.stop()
                    self.logger.info("Stopped audio playback")
                    
                if self.voice_client.is_connected():
                    await self.voice_client.disconnect()
                    self.logger.info("Disconnected from voice channel")
                    
                self.voice_client = None
                
        except Exception as e:
            self.logger.error(f"Error cleaning up voice client: {str(e)}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Play welcome sound when a member joins"""
        if member.bot:
            return

        try:
            # Check if welcome voice channel is configured
            if not Config.WELCOME_VOICE_CHANNEL_ID:
                self.logger.error("Welcome voice channel ID not configured")
                return
                
            # Get the voice channel
            voice_channel = self.bot.get_channel(Config.WELCOME_VOICE_CHANNEL_ID)
            if not voice_channel:
                self.logger.error(f"Could not find voice channel with ID {Config.WELCOME_VOICE_CHANNEL_ID}")
                return
                
            if not isinstance(voice_channel, discord.VoiceChannel):
                self.logger.error(f"Channel with ID {Config.WELCOME_VOICE_CHANNEL_ID} is not a voice channel")
                return
                
            self.logger.info(f"Member {member.name} joined, attempting to play welcome sound")
            await self.play_welcome_sound(voice_channel)
            
        except Exception as e:
            self.logger.error(f"Error handling member join: {str(e)}")

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(WelcomeCommands(bot))
