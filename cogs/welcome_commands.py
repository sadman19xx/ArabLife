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
        self.welcome_sound_path = os.path.abspath('welcome.mp3')

    @property
    def voice_client(self):
        """Get the current voice client from bot's shared client"""
        return self.bot.shared_voice_client

    @voice_client.setter
    def voice_client(self, client):
        """Set the bot's shared voice client"""
        self.bot.shared_voice_client = client

    async def play_welcome_sound(self, voice_channel: discord.VoiceChannel = None):
        """Play welcome sound in voice channel"""
        try:
            # Use provided channel or default to configured welcome channel
            if voice_channel is None:
                voice_channel = self.bot.get_channel(Config.WELCOME_VOICE_CHANNEL_ID)
                if not voice_channel:
                    self.logger.error(f"Could not find voice channel with ID {Config.WELCOME_VOICE_CHANNEL_ID}")
                    return
                if not isinstance(voice_channel, discord.VoiceChannel):
                    self.logger.error(f"Channel with ID {Config.WELCOME_VOICE_CHANNEL_ID} is not a voice channel")
                    return

            # Check if sound file exists
            if not os.path.exists(self.welcome_sound_path):
                self.logger.error(f"Welcome sound file not found at {self.welcome_sound_path}")
                return
                
            # Check if FFMPEG path is set and valid
            if not Config.FFMPEG_PATH or not os.path.exists(Config.FFMPEG_PATH):
                self.logger.error(f"FFMPEG not found at {Config.FFMPEG_PATH}")
                return

            self.logger.info(f"Attempting to join voice channel {voice_channel.name}")

            # Clean up any existing voice client first
            if voice_channel.guild.voice_client:
                try:
                    await voice_channel.guild.voice_client.disconnect(force=True)
                except:
                    pass

            # Connect to voice channel with timeout and health check
            try:
                self.voice_client = await voice_channel.connect(timeout=20.0, self_deaf=True)
                self.logger.info("Successfully connected to voice channel")
                
                # Verify connection is healthy
                if not self.voice_client.is_connected():
                    raise discord.ClientException("Voice client reports disconnected state after connect")
                    
                # Set up heartbeat monitoring
                if hasattr(self.voice_client.ws, '_keep_alive'):
                    if not self.voice_client.ws._keep_alive.is_running():
                        self.voice_client.ws._keep_alive.start()
                        
            except asyncio.TimeoutError:
                self.logger.error("Timeout while connecting to voice channel")
                return
            except discord.ClientException as e:
                self.logger.error(f"Failed to connect to voice channel: {str(e)}")
                # Clean up failed connection
                try:
                    if voice_channel.guild.voice_client:
                        await voice_channel.guild.voice_client.disconnect(force=True)
                except:
                    pass
                return

            # Play the welcome sound with improved options
            if not self.voice_client.is_playing():
                try:
                    audio_source = discord.FFmpegPCMAudio(
                        self.welcome_sound_path,
                        executable=Config.FFMPEG_PATH,
                        options=f'-loglevel warning -filter:a volume={Config.WELCOME_SOUND_VOLUME}'  # Added warning level
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
            # Clean up on error
            try:
                if voice_channel.guild.voice_client:
                    await voice_channel.guild.voice_client.disconnect(force=True)
            except:
                pass

    async def cleanup_voice(self, error):
        """Cleanup after playing sound"""
        try:
            if error:
                self.logger.error(f"Error during playback: {str(error)}")
                
            await asyncio.sleep(1)  # Wait a bit to ensure audio is finished
            
            if self.voice_client:
                if self.voice_client.is_playing():
                    self.voice_client.stop()
                    self.logger.info("Stopped audio playback")
                
                # Disconnect after playing
                try:
                    await self.voice_client.disconnect(force=True)
                    self.logger.info("Disconnected from voice after playback")
                except:
                    pass
                self.voice_client = None
                
        except Exception as e:
            self.logger.error(f"Error cleaning up voice client: {str(e)}")
            # Final cleanup attempt
            try:
                if self.voice_client:
                    await self.voice_client.disconnect(force=True)
            except:
                pass
            self.voice_client = None

    @discord.app_commands.command(
        name="testwelcome",
        description="Test the welcome sound in the configured channel"
    )
    async def test_welcome(self, interaction: discord.Interaction):
        """Slash command to test welcome sound"""
        try:
            # Defer the response since voice operations can take time
            await interaction.response.defer(ephemeral=True)
            
            # Attempt to play welcome sound
            await self.play_welcome_sound()
            
            # Send confirmation
            await interaction.followup.send(
                "Testing welcome sound in configured welcome channel...",
                ephemeral=True
            )
            
        except discord.NotFound:
            self.logger.warning("Test welcome interaction expired")
        except Exception as e:
            self.logger.error(f"Error in test welcome slash command: {str(e)}")
            try:
                await interaction.followup.send(
                    f"Error testing welcome sound: {str(e)}",
                    ephemeral=True
                )
            except:
                pass

    @commands.Cog.listener()
    async def on_ready(self):
        """Initialize welcome channel settings when bot starts"""
        try:
            # Get the voice channel
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
        """Play welcome sound when a member joins the welcome voice channel"""
        if member.bot:
            return

        try:
            # Check if member joined the welcome channel
            if (before.channel != after.channel and 
                after.channel and 
                after.channel.id == Config.WELCOME_VOICE_CHANNEL_ID):
                self.logger.info(f"Member {member.name} joined welcome channel, attempting to play welcome sound")
                await self.play_welcome_sound()
        except Exception as e:
            self.logger.error(f"Error handling voice state update: {str(e)}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Play welcome sound when a member joins the server"""
        if member.bot:
            return

        try:
            self.logger.info(f"Member {member.name} joined server, attempting to play welcome sound")
            await self.play_welcome_sound()  # Use default welcome channel
            
        except Exception as e:
            self.logger.error(f"Error handling member join: {str(e)}")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Handle member leave event"""
        pass  # No action needed for member leave
        
async def setup(bot):
    """Setup function for loading the cog"""
    cog = WelcomeCommands(bot)
    await bot.add_cog(cog)
    
    try:
        # Register app commands to guild
        guild = discord.Object(id=Config.GUILD_ID)
        bot.tree.add_command(cog.test_welcome, guild=guild)
        print("Registered welcome test command to guild")
    except Exception as e:
        print(f"Failed to register welcome test command: {e}")
