import discord
from discord.ext import commands
from discord import app_commands
from discord.ext.commands import Cog
import logging
import os
import asyncio
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
        self.log_channel_id = 1327648816874262549  # Channel for error logs
        
        # Override voice logger to also log to Discord channel
        async def log_to_discord(message, error=False):
            try:
                channel = self.bot.get_channel(self.log_channel_id)
                if channel:
                    await channel.send(f"```\n{message}\n```")
            except Exception as e:
                voice_logger.error(f"Failed to send log to Discord: {str(e)}")
        
        # Store original error function
        self._original_error = voice_logger.error
        
        # Override error function to also log to Discord
        def new_error(message):
            self._original_error(message)
            asyncio.create_task(log_to_discord(message, error=True))
        
        voice_logger.error = new_error
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10  # Increased max attempts
        self.reconnect_delay = 1  # Start with 1 second delay
        self.max_reconnect_delay = 30  # Maximum delay between attempts
        self.should_stay_connected = True
        self.welcome_channel_id = 1309595750878937240
        self.is_connecting = False  # Lock to prevent multiple simultaneous connection attempts
        # Connect to welcome channel on startup and start connection check
        bot.loop.create_task(self._delayed_startup())

    def _find_welcome_sound(self):
        """Find welcome.mp3 in possible locations"""
        possible_locations = [
            '/root/ArabLife/welcome.mp3',  # Root directory
            os.path.join('/root/ArabLife', 'welcome.mp3'),  # Using os.path.join
            'welcome.mp3',  # Current working directory fallback
        ]
        
        for location in possible_locations:
            voice_logger.info(f"Looking for welcome sound at: {location}")
            if os.path.exists(location):
                voice_logger.info(f"Found welcome sound at: {location}")
                return location
        
        voice_logger.error("Could not find welcome.mp3 in any expected location")
        return None

    async def _delayed_startup(self):
        """Handle startup with appropriate delays"""
        await self.bot.wait_until_ready()
        await asyncio.sleep(15)  # Initial delay to let bot fully initialize
        
        # Start connection check loop
        self.bot.loop.create_task(self._connection_check())
        
        # Initial connection attempt
        try:
            await self._ensure_voice_connected()
        except Exception as e:
            voice_logger.error(f"Initial connection failed: {str(e)}")

    async def _connection_check(self):
        """Periodically check and ensure voice connection"""
        await self.bot.wait_until_ready()
        # Initial delay to let bot fully initialize
        await asyncio.sleep(15)  # Wait 15 seconds before first connection attempt
        
        while not self.bot.is_closed():
            try:
                welcome_channel = self.bot.get_channel(self.welcome_channel_id)
                if welcome_channel:
                    current_voice = welcome_channel.guild.voice_client
                    needs_reconnect = (
                        not self.voice_client or 
                        not self.voice_client.is_connected() or 
                        self.voice_client.channel != welcome_channel or
                        (current_voice and current_voice.channel != welcome_channel)
                    )
                    
                    if needs_reconnect:
                        voice_logger.info("Connection check: Reconnecting to voice channel")
                        try:
                            # Clean up any existing connection first
                            if current_voice:
                                try:
                                    await current_voice.disconnect(force=True)
                                    await asyncio.sleep(2)  # Wait 2 seconds after disconnect
                                except:
                                    pass
                            
                            # Try to connect
                            await self._ensure_voice_connected()
                            # If successful, wait longer before next check
                            await asyncio.sleep(60)  # 60 seconds if successful
                            continue
                        except Exception as e:
                            voice_logger.error(f"Connection check failed: {str(e)}")
                            # Shorter delay if connection failed
                            await asyncio.sleep(15)
                            continue
                
                # Normal check interval
                await asyncio.sleep(45)  # Check every 45 seconds
            except Exception as e:
                voice_logger.error(f"Error in connection check: {str(e)}")
                await asyncio.sleep(15)  # 15 second delay on error before next check

    async def _ensure_voice_connected(self):
        """Ensure bot is connected to welcome channel"""
        if self.is_connecting:
            voice_logger.info("Connection already in progress, skipping")
            return
            
        self.is_connecting = True
        try:
            welcome_channel = self.bot.get_channel(self.welcome_channel_id)
            if not welcome_channel:
                voice_logger.error("Could not find welcome channel")
                return
            
            # Check if we need to connect
            if not welcome_channel.guild.voice_client or welcome_channel.guild.voice_client.channel != welcome_channel:
                # Clean up any existing connection
                if welcome_channel.guild.voice_client:
                    try:
                        await welcome_channel.guild.voice_client.disconnect(force=True)
                        await asyncio.sleep(2)  # Increased delay after disconnect
                    except Exception as e:
                        voice_logger.error(f"Error cleaning up existing connection: {str(e)}")
                        await asyncio.sleep(2)  # Wait even if cleanup failed
                
                # Connect to the channel with increased timeout
                for attempt in range(2):  # Try up to 2 times
                    try:
                        voice_logger.info(f"Attempting to connect (attempt {attempt + 1}/2)")
                        self.voice_client = await welcome_channel.connect(timeout=60.0, self_deaf=False, self_mute=False)
                        break  # If successful, break the loop
                    except asyncio.TimeoutError:
                        voice_logger.error(f"Timeout while connecting to voice channel (attempt {attempt + 1}/2)")
                        if attempt < 1:  # If this isn't the last attempt
                            await asyncio.sleep(3)  # Wait before retrying
                            continue
                        raise  # Re-raise on last attempt
                    except Exception as e:
                        voice_logger.error(f"Error connecting to voice channel: {str(e)}")
                        if attempt < 1:
                            await asyncio.sleep(3)
                            continue
                        raise
                
                # Set up connection
                if not hasattr(self.voice_client, '_event_listeners'):
                    self.voice_client._event_listeners = {}
                self.voice_client.on_disconnect = self._handle_disconnect
                
                # Reset reconnect attempts
                self.reconnect_attempts = 0
                self.should_stay_connected = True
                
                # Set up heartbeat monitoring
                if hasattr(self.voice_client.ws, '_keep_alive'):
                    if not self.voice_client.ws._keep_alive.is_running():
                        self.voice_client.ws._keep_alive.start()
                
                voice_logger.info(f"Connected to welcome channel {welcome_channel.name}")
                
                # Add small delay to ensure connection is stable
                await asyncio.sleep(0.5)
                
                # Verify connection is healthy
                if not self.voice_client.is_connected():
                    raise discord.ClientException("Voice client reports disconnected state after connect")
            else:
                # Already connected to correct channel
                self.voice_client = welcome_channel.guild.voice_client
                self.should_stay_connected = True
                voice_logger.info("Already connected to welcome channel")
                
        except Exception as e:
            voice_logger.error(f"Error ensuring voice connection: {str(e)}")
            # Try to clean up on error
            try:
                if welcome_channel and welcome_channel.guild.voice_client:
                    await welcome_channel.guild.voice_client.disconnect(force=True)
            except:
                pass
            raise
        finally:
            # Always release the connection lock
            self.is_connecting = False

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
        # First check if ffmpeg is in PATH
        import shutil
        ffmpeg_in_path = shutil.which('ffmpeg')
        if ffmpeg_in_path:
            return ffmpeg_in_path

        common_paths = [
            r"C:\ffmpeg\bin\ffmpeg.exe",  # Windows custom install
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",  # Windows program files
            r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",  # Windows program files x86
            "/usr/bin/ffmpeg",  # Linux default
            "/usr/local/bin/ffmpeg",  # Linux alternative
            "/opt/homebrew/bin/ffmpeg",  # macOS Homebrew
        ]
        
        for path in common_paths:
            if os.path.isfile(path):
                return path
        
        # Default to just 'ffmpeg' and let the system resolve it
        return "ffmpeg"

    @Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Triggered when a member joins/leaves/moves between voice channels"""
        # Ignore bot's own voice state updates
        if member.bot:
            return

        # Check if member joined the specific channel
        if after.channel and after.channel.id == self.welcome_channel_id and before.channel != after.channel:
            welcome_channel = after.channel
            try:
                # Ensure we're connected to the voice channel
                if not welcome_channel.guild.voice_client or welcome_channel.guild.voice_client.channel != welcome_channel:
                    await self._ensure_voice_connected()
                
                # Find welcome.mp3 file
                welcome_file = self._find_welcome_sound()
                if self.voice_client and welcome_file:
                    try:
                        # Play the welcome sound with options for better stability
                        audio_source = discord.FFmpegPCMAudio(
                            welcome_file,
                            executable=self.ffmpeg_path,
                            options='-loglevel warning'
                        )
                        transformed_source = discord.PCMVolumeTransformer(audio_source, volume=Config.DEFAULT_VOLUME)
                        
                        if not self.voice_client.is_playing():
                            try:
                                self.voice_client.play(transformed_source, after=lambda e: asyncio.create_task(self._after_play(e)))
                                voice_logger.info(f"Playing welcome sound for {member.name}#{member.discriminator} in {welcome_channel.name}")
                            except Exception as play_error:
                                voice_logger.error(f"Error playing welcome sound: {str(play_error)}")
                    except Exception as audio_error:
                        voice_logger.error(f"Error playing audio: {str(audio_error)}")
                else:
                    voice_logger.warning("Welcome sound file not found or voice client not available")
            except Exception as e:
                voice_logger.error(f"Error in voice state update: {str(e)}")

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

            # Find welcome.mp3 file
            welcome_file = self._find_welcome_sound()
            if welcome_file:
                # Ensure we're connected to the voice channel
                if not welcome_channel.guild.voice_client or welcome_channel.guild.voice_client.channel != welcome_channel:
                    await self._ensure_voice_connected()
                
                # Play welcome sound if we have a voice client
                if self.voice_client:
                    try:
                        # Play the welcome sound with better stability options
                        audio_source = discord.FFmpegPCMAudio(
                            welcome_file,
                            executable=self.ffmpeg_path,
                            options='-loglevel warning'
                        )
                        transformed_source = discord.PCMVolumeTransformer(audio_source, volume=Config.DEFAULT_VOLUME)
                        
                        if not self.voice_client.is_playing():
                            try:
                                self.voice_client.play(transformed_source, after=lambda e: asyncio.create_task(self._after_play(e)))
                                voice_logger.info(f"Testing welcome sound in {welcome_channel.name}")
                            except Exception as play_error:
                                voice_logger.error(f"Error playing welcome sound: {str(play_error)}")
                                raise
                    except Exception as e:
                        voice_logger.error(f"Error playing audio: {str(e)}")
                        raise
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
        if self.is_connecting:
            voice_logger.info("Connection attempt already in progress, skipping reconnect")
            return
            
        voice_logger.warning("Voice client disconnected")
        
        if not self.should_stay_connected:
            voice_logger.info("Bot was intentionally disconnected, not attempting to reconnect")
            return
            
        if self.voice_client and self.voice_client.channel:
            channel = self.voice_client.channel
            guild = channel.guild
            
            # Set connecting flag
            self.is_connecting = True
            
            try:
                # Clean up existing voice client
                if guild.voice_client:
                    try:
                        await guild.voice_client.disconnect(force=True)
                        await asyncio.sleep(2)  # Increased delay after disconnect
                    except:
                        pass
                
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
                        
                        # Ensure no existing connection
                        if guild.voice_client:
                            try:
                                await guild.voice_client.disconnect(force=True)
                                await asyncio.sleep(2)  # Wait after disconnect
                            except:
                                pass
                        
                        # Reconnect with increased timeout
                        self.voice_client = await channel.connect(timeout=60.0, self_deaf=False, self_mute=False)
                        
                        # Set up disconnect handler
                        if not hasattr(self.voice_client, '_event_listeners'):
                            self.voice_client._event_listeners = {}
                        self.voice_client.on_disconnect = self._handle_disconnect
                        
                        # Set up heartbeat monitoring
                        if hasattr(self.voice_client.ws, '_keep_alive'):
                            if not self.voice_client.ws._keep_alive.is_running():
                                self.voice_client.ws._keep_alive.start()
                        
                        # Verify connection is healthy
                        if not self.voice_client.is_connected():
                            raise discord.ClientException("Voice client reports disconnected state after reconnect")
                        
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
                        
                        # Clean up failed connection
                        try:
                            if guild.voice_client:
                                await guild.voice_client.disconnect(force=True)
                        except:
                            pass
                        
                        # Continue to next attempt
                
                # If we get here, we've exhausted all attempts
                voice_logger.error("Max reconnection attempts reached")
                self.reconnect_attempts = 0
                self.reconnect_delay = 1
                self.should_stay_connected = False
                
                # Final cleanup
                try:
                    if guild.voice_client:
                        await guild.voice_client.disconnect(force=True)
                except:
                    pass
                self.voice_client = None
            except Exception as e:
                voice_logger.error(f"Error in reconnection loop: {str(e)}")
                self.should_stay_connected = False
                self.voice_client = None
            finally:
                # Always release the connection lock
                self.is_connecting = False

    async def _after_play(self, error):
        """Callback for after audio finishes playing"""
        if error:
            voice_logger.error(f"Error during playback: {str(error)}")
        else:
            voice_logger.info("Successfully finished playing welcome sound")
        
        # Ensure we stay connected after playing
        if self.voice_client and self.voice_client.is_connected():
            self.should_stay_connected = True
            # Reset any cleanup flags
            if hasattr(self.voice_client, '_player') and self.voice_client._player:
                self.voice_client._player = None

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
