import discord
from discord.ext import commands
import logging
import os
import asyncio
from config import Config
from utils.logger import setup_logging

# Set up logging before anything else
logger = setup_logging(
    None,  # We'll update this with the bot instance later
    error_log_channel=1327648816874262549,
    audit_log_channel=1286684861234417704
)

# Set up intents with required privileges
intents = discord.Intents.default()
intents.members = True  # Required for on_member_join event
intents.voice_states = True  # Required for voice channel events and functionality

class ArabLifeBot(commands.Bot):
    """Custom bot class for ArabLife Discord server functionality"""
    
    def __init__(self) -> None:
        super().__init__(
            command_prefix='!',  # Add command prefix for traditional commands
            intents=intents,
            case_insensitive=True  # Make commands case-insensitive
        )
        
        # List of cogs to load (only existing cogs)
        self.initial_extensions = [
            'cogs.voice_commands',  # Load voice commands first for voice client management
            'cogs.welcome_commands',
            'cogs.application_commands',
            'cogs.help_commands',
            'cogs.announcement_commands',
            'cogs.role_commands',
            'cogs.status_commands'
        ]
        
        # Shared voice client for coordination between cogs
        self.shared_voice_client = None
        
        # Clear existing commands to remove stale ones
        self._clear_commands = True

    async def setup_hook(self) -> None:
        """Initialize bot setup"""
        # Clear existing commands if requested
        if self._clear_commands:
            self.tree.clear_commands(guild=None)
            logger.info('Cleared all existing commands')
            
        # Configure FFmpeg for voice
        if not os.path.exists(Config.FFMPEG_PATH):
            logger.warning(f"FFmpeg not found at {Config.FFMPEG_PATH}")
            # Try to find FFmpeg in system PATH
            import shutil
            ffmpeg_path = shutil.which('ffmpeg')
            if ffmpeg_path:
                logger.info(f"Found FFmpeg in system PATH: {ffmpeg_path}")
                Config.FFMPEG_PATH = ffmpeg_path
            else:
                logger.warning("FFmpeg not found in system PATH")
        
        # Configure voice-related settings
        discord.VoiceClient.warn_nacl = False
        discord.FFmpegPCMAudio.DEFAULT_EXECUTABLE = Config.FFMPEG_PATH
        
        # Configure voice connection settings
        discord.VoiceClient.default_timeout = Config.VOICE_TIMEOUT
        discord.VoiceClient.default_reconnect = True
        discord.VoiceClient.default_self_deaf = False
        discord.VoiceClient.default_self_mute = False
        
        # Load extensions
        try:
            for extension in self.initial_extensions:
                await self.load_extension(extension)
                logger.info(f'Loaded {extension}')
        except Exception as e:
            logger.error(f'Failed to load extensions: {str(e)}')

    async def on_error(self, event_method: str, *args, **kwargs) -> None:
        """Global error handler for all events"""
        logger.error(f'Error in {event_method}: {args} {kwargs}')
        
        # Special handling for voice state errors
        if event_method == "voice_state_update":
            voice_logger = logging.getLogger('discord.voice')
            voice_logger.error(f"Voice state error: {args} {kwargs}")
            
            try:
                if len(args) >= 3 and isinstance(args[0], discord.Member):
                    member = args[0]
                    guild = member.guild
                    
                    # Get voice client if it exists
                    voice_client = guild.voice_client
                    if voice_client:
                        # Check if connection is stale
                        if not voice_client.is_connected() or not voice_client.socket:
                            voice_logger.warning("Detected stale voice connection, cleaning up...")
                            try:
                                await voice_client.disconnect(force=True)
                            except:
                                pass
                        
                        # Check if websocket is closed
                        if hasattr(voice_client, 'ws') and voice_client.ws:
                            if voice_client.ws.closed:
                                voice_logger.warning("Detected closed websocket, cleaning up...")
                                try:
                                    await voice_client.disconnect(force=True)
                                except:
                                    pass
                                
                        # Ensure keep-alive is running
                        if hasattr(voice_client, 'ws') and voice_client.ws and hasattr(voice_client.ws, '_keep_alive'):
                            if not voice_client.ws._keep_alive.is_running():
                                voice_logger.warning("Keep-alive not running, restarting...")
                                voice_client.ws._keep_alive.start()
            except Exception as e:
                voice_logger.error(f"Error handling voice state: {str(e)}")
        
        await super().on_error(event_method, *args, **kwargs)

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        """Monitor voice state changes"""
        voice_logger = logging.getLogger('discord.voice')
        
        try:
            # Log all voice state changes for debugging
            voice_logger.debug(
                f"Voice state update for {member.name}: "
                f"channel: {before.channel} -> {after.channel}, "
                f"deaf: {before.deaf} -> {after.deaf}, "
                f"self_deaf: {before.self_deaf} -> {after.self_deaf}"
            )

            # Process bot's own voice state
            if member.id == self.user.id:
                if after.channel:
                    voice_logger.info(f"Bot joined voice channel: {after.channel.name}")
            # Handle voice state changes
            try:
                # Ensure bot is not deafened
                if after.deaf or after.self_deaf:
                    voice_logger.info("Bot is deafened, attempting to undeafen")
                    try:
                        await member.guild.change_voice_state(
                            channel=after.channel,
                            self_deaf=False,
                            self_mute=False
                        )
                        voice_logger.info("Successfully undeafened bot")
                    except Exception as e:
                        voice_logger.error(f"Failed to undeafen bot: {str(e)}")

                # Verify voice client health
                voice_client = member.guild.voice_client
                if voice_client:
                    # Check websocket health
                    if hasattr(voice_client, 'ws') and voice_client.ws:
                        if voice_client.ws.closed:
                            voice_logger.warning("Voice websocket closed, attempting to reconnect")
                            try:
                                await voice_client.disconnect(force=True)
                                await asyncio.sleep(1)
                                if after.channel:
                                    await after.channel.connect(
                                        timeout=Config.VOICE_TIMEOUT,
                                        reconnect=True,
                                        self_deaf=False,
                                        self_mute=False
                                    )
                            except Exception as e:
                                voice_logger.error(f"Failed to reconnect: {str(e)}")
                    
                    # Check keep-alive
                    if hasattr(voice_client, 'ws') and voice_client.ws and hasattr(voice_client.ws, '_keep_alive'):
                        if not voice_client.ws._keep_alive.is_running():
                            voice_logger.warning("Keep-alive not running, restarting")
                            voice_client.ws._keep_alive.start()

            except Exception as e:
                voice_logger.error(f"Error handling voice state: {str(e)}")
            
            # Update shared voice client
            voice_client = member.guild.voice_client
            if voice_client:
                try:
                    # Wait for connection to stabilize
                    await asyncio.sleep(2)
                    
                    # Verify connection is healthy
                    if voice_client.is_connected():
                        self.shared_voice_client = voice_client
                        voice_logger.info("Voice connection verified and shared")
                        
                        # Ensure we're not deafened
                        await asyncio.sleep(1)
                        await member.guild.change_voice_state(
                            channel=after.channel,
                            self_deaf=False,
                            self_mute=False
                        )
                    else:
                        voice_logger.warning("Voice connection unstable, cleaning up")
                        try:
                            await voice_client.disconnect(force=True)
                        except:
                            pass
                        self.shared_voice_client = None
                except Exception as e:
                    voice_logger.error(f"Voice connection error: {str(e)}")
                    try:
                        await voice_client.disconnect(force=True)
                    except:
                        pass
                    self.shared_voice_client = None
            else:
                voice_logger.info("Bot left voice channel")
                if self.shared_voice_client:
                    try:
                        await self.shared_voice_client.disconnect(force=True)
                    except:
                        pass
                    self.shared_voice_client = None
                    
        except Exception as e:
            voice_logger.error(f"Error monitoring voice state: {str(e)}")
            if self.shared_voice_client:
                try:
                    await self.shared_voice_client.disconnect(force=True)
                except:
                    pass
                self.shared_voice_client = None

    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
        """Error handler for application commands"""
        try:
            if isinstance(error, discord.app_commands.CommandInvokeError):
                error = error.original

            if isinstance(error, discord.NotFound) and error.code == 10062:
                # Interaction has expired - ignore this error
                return
            
            error_message = f"An error occurred: {str(error)}"
            
            try:
                if interaction.response.is_done():
                    await interaction.followup.send(error_message, ephemeral=True)
                else:
                    await interaction.response.send_message(error_message, ephemeral=True)
            except discord.NotFound:
                # If we can't respond to the interaction, log it
                logger.error(f"Failed to respond to interaction: {error_message}")
                
        except Exception as e:
            logger.error(f"Error in error handler: {str(e)}")

    async def on_ready(self) -> None:
        """Event triggered when the bot is ready"""
        logger.info('='*50)
        logger.info('             ARABLIFE BOT IS UP')
        logger.info('='*50)
        logger.info(f'Logged in as: {self.user.name}')
        logger.info(f'Bot ID: {self.user.id}')
        logger.info(f'Start Time: {discord.utils.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}')
        
        # Set the default status when the bot starts
        activity = discord.Activity(type=discord.ActivityType.watching, name="ArabLife")
        await self.change_presence(activity=activity)
        
        # Sync commands with Discord
        try:
            guild = discord.Object(id=Config.GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logger.info('Successfully synced application commands')
        except Exception as e:
            logger.error(f'Failed to sync commands: {str(e)}')
            
        logger.info('------')
        
        # Update logger with bot instance
        global logger
        logger = setup_logging(
            self,
            error_log_channel=1327648816874262549,
            audit_log_channel=1286684861234417704
        )

async def main():
    """Main function to run the bot"""
    # Validate configuration
    try:
        Config.validate_config()
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        return

    # Create and run bot
    try:
        async with ArabLifeBot() as bot:
            await bot.start(Config.TOKEN)
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}")

# Run the bot
if __name__ == "__main__":
    try:
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}")
