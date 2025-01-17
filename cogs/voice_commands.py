import discord
from discord.ext import commands
from discord import app_commands
from discord.ext.commands import Cog
import logging
import os
from config import Config

logger = logging.getLogger('discord')

# Create a separate logger for voice that only logs to file/console
voice_logger = logging.getLogger('discord.voice')
voice_logger.propagate = False  # Prevent logs from being sent to parent logger
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
voice_logger.addHandler(handler)

class VoiceCommands(Cog):
    """Cog for voice-related commands"""
    
    def __init__(self, bot):
        self.bot = bot
        # Get FFmpeg path from config or use default paths
        self.ffmpeg_path = Config.FFMPEG_PATH or self._get_ffmpeg_path()
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10  # Increased max attempts
        self.reconnect_delay = 1  # Start with 1 second delay
        self.max_reconnect_delay = 30  # Maximum delay between attempts
        self.should_stay_connected = True

    @property
    def voice_client(self):
        """Get the current voice client from bot's shared client"""
        return self.bot.shared_voice_client

    @voice_client.setter
    def voice_client(self, client):
        """Set the bot's shared voice client"""
        self.bot.shared_voice_client = client

    def _get_ffmpeg_path(self):
        """Try to find FFmpeg in common locations"""
        common_paths = [
            "/usr/bin/ffmpeg",  # Linux default
            "/usr/local/bin/ffmpeg",  # Linux alternative
            "/opt/homebrew/bin/ffmpeg",  # macOS Homebrew
            r"C:\ffmpeg\bin\ffmpeg.exe",  # Windows custom install
            "ffmpeg"  # System PATH
        ]
        
        for path in common_paths:
            if os.path.isfile(path):
                return path
        
        return "/usr/bin/ffmpeg"  # Default to Linux standard location

    @Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Triggered when a member joins/leaves/moves between voice channels"""
        # Ignore bot's own voice state updates
        if member.bot:
            return

        # Check if member joined the specific channel
        if after.channel and after.channel.id == 1309595750878937240 and before.channel != after.channel:
            welcome_channel = after.channel
            try:
                # Play welcome sound
                if os.path.exists('welcome.mp3'):
                    # Connect to voice channel if not already connected
                    try:
                        if not welcome_channel.guild.voice_client:
                            self.voice_client = await welcome_channel.connect(self_deaf=True)
                            # Set up initial connection
                            if not hasattr(self.voice_client, '_event_listeners'):
                                self.voice_client._event_listeners = {}
                            self.voice_client.on_disconnect = self._handle_disconnect
                        else:
                            self.voice_client = welcome_channel.guild.voice_client
                            if self.voice_client.channel != welcome_channel:
                                await self.voice_client.move_to(welcome_channel)
                        
                        # Reset reconnect attempts on successful connection
                        self.reconnect_attempts = 0
                        self.should_stay_connected = True
                    except discord.ClientException as e:
                        voice_logger.error(f"Failed to connect to voice: {str(e)}")
                        if "already connected" in str(e):
                            # Clean up existing connection
                            try:
                                await welcome_channel.guild.voice_client.disconnect()
                            except:
                                pass
                            # Try connecting again
                            self.voice_client = await welcome_channel.connect()

                    # Play the welcome sound
                    audio_source = discord.FFmpegPCMAudio(
                        'welcome.mp3',
                        executable=self.ffmpeg_path
                    )
                    transformed_source = discord.PCMVolumeTransformer(audio_source, volume=Config.DEFAULT_VOLUME)
                    
                    if not self.voice_client.is_playing():
                        self.voice_client.play(transformed_source)
                        voice_logger.info(f"Playing welcome sound for {member.name}#{member.discriminator} in {welcome_channel.name}")
                else:
                    voice_logger.warning(f"Welcome sound file not found at {Config.WELCOME_SOUND_PATH}")
            except Exception as e:
                voice_logger.error(f"Error playing welcome sound: {str(e)}")

    @app_commands.command(
        name="testsound",
        description="Test the welcome sound"
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(1, Config.SOUND_COMMAND_COOLDOWN)
    async def test_sound(self, interaction: discord.Interaction):
        """Test the welcome sound"""
        try:
            # Log FFmpeg path being used
            voice_logger.info(f"Using FFmpeg path: {self.ffmpeg_path}")
            
            # Verify FFmpeg exists
            if not os.path.isfile(self.ffmpeg_path) and self.ffmpeg_path != "ffmpeg":
                await interaction.response.send_message(
                    "*خطأ: لم يتم العثور على FFmpeg. يرجى التحقق من التثبيت.*",
                    ephemeral=True
                )
                return

            # Get the specific welcome channel
            welcome_channel = self.bot.get_channel(1309595750878937240)
            if not welcome_channel:
                await interaction.response.send_message(
                    "*لم يتم العثور على قناة الترحيب.*",
                    ephemeral=True
                )
                return

            await interaction.response.send_message("*جاري تشغيل صوت الترحيب...*")

            # Play welcome sound if it exists
            if os.path.exists('welcome.mp3'):
                # Connect to voice channel
                if not welcome_channel.guild.voice_client:
                    self.voice_client = await welcome_channel.connect()
                else:
                    self.voice_client = welcome_channel.guild.voice_client
                    if self.voice_client.channel != welcome_channel:
                        await self.voice_client.move_to(welcome_channel)

                # Play the welcome sound
                audio_source = discord.FFmpegPCMAudio(
                    'welcome.mp3',
                    executable=self.ffmpeg_path
                )
                transformed_source = discord.PCMVolumeTransformer(audio_source, volume=Config.DEFAULT_VOLUME)
                
                if not self.voice_client.is_playing():
                    self.voice_client.play(transformed_source)
                    voice_logger.info(f"Testing welcome sound in {welcome_channel.name}")
            else:
                await interaction.followup.send("*لم يتم تكوين ملف الصوت.*")

        except Exception as e:
            voice_logger.error(f"Error testing welcome sound: {str(e)}")
            await interaction.followup.send(f"*حدث خطأ أثناء تشغيل الصوت: {str(e)}*")

    @app_commands.command(
        name="volume",
        description="Change the bot's voice volume"
    )
    @app_commands.describe(
        volume="Volume level (0.0 to 1.0)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def set_volume(self, interaction: discord.Interaction, volume: float):
        """Change the volume (0.0 to 1.0)"""
        if not self.voice_client:
            await interaction.response.send_message(
                "*البوت غير متصل بالصوت.*",
                ephemeral=True
            )
            return

        try:
            # Ensure volume is between 0 and 1
            volume = min(1.0, max(0.0, volume))
            
            if self.voice_client.source:
                self.voice_client.source.volume = volume
                await interaction.response.send_message(f"*تم تغيير مستوى الصوت الى {volume}*")
                voice_logger.info(f"Volume changed to {volume} by {interaction.user.name}#{interaction.user.discriminator}")
            else:
                await interaction.response.send_message(
                    "*لا يوجد صوت قيد التشغيل.*",
                    ephemeral=True
                )
        except Exception as e:
            voice_logger.error(f"Error changing volume: {str(e)}")
            await interaction.response.send_message(
                "*حدث خطأ أثناء تغيير مستوى الصوت.*",
                ephemeral=True
            )

    async def _handle_disconnect(self):
        """Handle voice client disconnection"""
        voice_logger.warning("Voice client disconnected")
        
        if not self.should_stay_connected:
            voice_logger.info("Bot was intentionally disconnected, not attempting to reconnect")
            return
            
        if self.voice_client and self.voice_client.channel:
            channel = self.voice_client.channel
            
            while self.reconnect_attempts < self.max_reconnect_attempts and self.should_stay_connected:
                self.reconnect_attempts += 1
                voice_logger.info(f"Attempting to reconnect (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})")
                
                try:
                    # Wait with exponential backoff
                    delay = min(self.reconnect_delay * (2 ** (self.reconnect_attempts - 1)), self.max_reconnect_delay)
                    voice_logger.info(f"Waiting {delay} seconds before reconnecting...")
                    await asyncio.sleep(delay)
                    
                    if not self.should_stay_connected:
                        voice_logger.info("Reconnection cancelled - bot should not stay connected")
                        return
                    
                    # Reconnect
                    self.voice_client = await channel.connect(self_deaf=True)
                    
                    # Set up disconnect handler
                    if not hasattr(self.voice_client, '_event_listeners'):
                        self.voice_client._event_listeners = {}
                    self.voice_client.on_disconnect = self._handle_disconnect
                    
                    # Set up heartbeat monitoring
                    if hasattr(self.voice_client.ws, '_keep_alive'):
                        self.voice_client.ws._keep_alive.start()
                    
                    voice_logger.info("Successfully reconnected to voice")
                    
                    # Reset attempts and delay on success
                    self.reconnect_attempts = 0
                    self.reconnect_delay = 1
                    return
                    
                except Exception as e:
                    voice_logger.error(f"Failed to reconnect: {str(e)}")
                    if not self.should_stay_connected:
                        voice_logger.info("Stopping reconnection attempts - bot should not stay connected")
                        return
                    # Continue to next attempt
            
            # If we get here, we've exhausted all attempts
            voice_logger.error("Max reconnection attempts reached")
            self.reconnect_attempts = 0
            self.reconnect_delay = 1
            self.should_stay_connected = False
            try:
                await self.voice_client.disconnect()
            except:
                pass
            self.voice_client = None

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Error handler for application commands"""
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"*الرجاء الانتظار {error.retry_after:.1f} ثواني.*",
                ephemeral=True
            )
        elif isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "*لا تملك الصلاحية لأستخدام هذه الامر.*",
                ephemeral=True
            )
        else:
            voice_logger.error(f"Voice command error: {str(error)}")
            await interaction.response.send_message(
                "*حدث خطأ غير متوقع.*",
                ephemeral=True
            )

# Add imports at top
import asyncio

async def setup(bot):
    """Setup function for loading the cog"""
    # Create cog instance
    cog = VoiceCommands(bot)
    
    # Add cog to bot
    await bot.add_cog(cog)
    
    try:
        # Register app commands to guild
        guild = discord.Object(id=Config.GUILD_ID)
        bot.tree.add_command(cog.test_sound, guild=guild)
        bot.tree.add_command(cog.set_volume, guild=guild)
        print("Registered voice commands to guild")
    except Exception as e:
        print(f"Failed to register voice commands: {e}")
