import discord
from discord.ext import commands
import logging
import os
from config import Config
from utils.logger import setup_logging

# Configure discord.py logging
for logger_name in ['discord', 'discord.client', 'discord.http', 'discord.shard']:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.CRITICAL)  # Only show critical errors

# Set up voice-related logging
voice_loggers = ['discord.gateway', 'discord.voice_client', 'discord.voice']
for logger_name in voice_loggers:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)  # Show all voice-related logs for debugging

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
            print('Cleared all existing commands')
            
        # Load extensions
        try:
            for extension in self.initial_extensions:
                await self.load_extension(extension)
                print(f'Loaded {extension}')
        except Exception as e:
            print(f'Failed to load extensions: {str(e)}')

    async def on_error(self, event_method: str, *args, **kwargs) -> None:
        """Global error handler for all events"""
        print(f'Error in {event_method}: {args} {kwargs}')
        
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
            # Only process bot's own voice state
            if member.id != self.user.id:
                return
                
            # Log voice state changes
            if before.channel != after.channel:
                if after.channel:
                    voice_logger.info(f"Bot joined voice channel: {after.channel.name}")
                    # Ensure bot is not deafened
                    if after.deaf or after.self_deaf:
                        try:
                            await member.guild.change_voice_state(
                                channel=after.channel,
                                self_deaf=False,
                                self_mute=False
                            )
                            voice_logger.info("Undeafened bot in voice channel")
                        except Exception as e:
                            voice_logger.error(f"Failed to undeafen bot: {str(e)}")
                    
                    # Update shared voice client
                    voice_client = member.guild.voice_client
                    if voice_client:
                        self.shared_voice_client = voice_client
                        # Wait a moment to verify connection
                        await asyncio.sleep(0.5)
                        if not voice_client.is_connected():
                            voice_logger.warning("Voice client disconnected immediately after connect")
                            try:
                                await voice_client.disconnect(force=True)
                            except:
                                pass
                            self.shared_voice_client = None
                        
                        # Start keep-alive if needed
                        if (hasattr(voice_client, 'ws') and 
                            voice_client.ws and 
                            hasattr(voice_client.ws, '_keep_alive') and 
                            not voice_client.ws._keep_alive.is_running()):
                            voice_client.ws._keep_alive.start()
                            voice_logger.info("Started voice keep-alive")
                else:
                    voice_logger.info("Bot left voice channel")
                    try:
                        if self.shared_voice_client:
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
                print(f"Failed to respond to interaction: {error_message}")
                
        except Exception as e:
            print(f"Error in error handler: {str(e)}")

    async def on_ready(self) -> None:
        """Event triggered when the bot is ready"""
        print('='*50)
        print('             ARABLIFE BOT IS UP')
        print('='*50)
        print(f'Logged in as: {self.user.name}')
        print(f'Bot ID: {self.user.id}')
        print(f'Start Time: {discord.utils.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}')
        
        # Set the default status when the bot starts
        activity = discord.Activity(type=discord.ActivityType.watching, name="ArabLife")
        await self.change_presence(activity=activity)
        
        # Sync commands with Discord
        try:
            guild = discord.Object(id=Config.GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print('Successfully synced application commands')
        except Exception as e:
            print(f'Failed to sync commands: {str(e)}')
            
        print('------')
        
        # Set up logging with Discord channels
        setup_logging(
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
        print(f"Configuration error: {str(e)}")
        return

    # Create and run bot
    try:
        async with ArabLifeBot() as bot:
            await bot.start(Config.TOKEN)
    except Exception as e:
        print(f"Failed to start bot: {str(e)}")

# Run the bot
if __name__ == "__main__":
    try:
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print(f"Fatal error: {str(e)}")
