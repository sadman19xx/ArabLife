import discord
from discord.ext import commands
import logging
import asyncio
from collections import deque

logger = logging.getLogger('discord')

class VoiceCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.welcome_channel_id = 1309595750878937240
        self.log_channel_id = 1327648816874262549
        self.voice_client = None
        self.audio_queue = deque()
        self.is_playing = False
        self.lock = asyncio.Lock()
        
        # Start initial connection
        bot.loop.create_task(self.ensure_voice_connection())

    async def log_to_channel(self, message):
        """Send log message to Discord channel"""
        try:
            channel = self.bot.get_channel(self.log_channel_id)
            if channel:
                await channel.send(f"```\n{message}\n```")
        except Exception as e:
            logger.error(f"Failed to send log: {str(e)}")

    async def ensure_voice_connection(self):
        """Ensure bot is connected to voice channel"""
        await self.bot.wait_until_ready()
        await asyncio.sleep(5)  # Wait for bot to fully initialize
        
        while not self.bot.is_closed():
            try:
                async with self.lock:
                    channel = self.bot.get_channel(self.welcome_channel_id)
                    if not channel:
                        await asyncio.sleep(30)
                        continue

                    # Check if we need to connect
                    if not self.voice_client or not self.voice_client.is_connected():
                        # Clean up any existing connections
                        try:
                            if channel.guild.voice_client:
                                await channel.guild.voice_client.disconnect()
                                await asyncio.sleep(2)
                        except:
                            pass

                        # Connect to channel
                        self.voice_client = await channel.connect()
                        await asyncio.sleep(1)

                        # Ensure we're not deafened
                        await channel.guild.change_voice_state(
                            channel=channel,
                            self_deaf=False,
                            self_mute=False
                        )
                        
                        await self.log_to_channel("✅ Connected to voice channel")
                    
                    # Check if we're in the right channel and not deafened
                    elif self.voice_client.channel.id != self.welcome_channel_id:
                        await self.voice_client.move_to(channel)
                        await self.log_to_channel("🔄 Moved to correct channel")
                    
                    elif self.voice_client.guild.me.voice.self_deaf:
                        await channel.guild.change_voice_state(
                            channel=channel,
                            self_deaf=False,
                            self_mute=False
                        )
                        await self.log_to_channel("🔊 Undeafened bot")

            except Exception as e:
                await self.log_to_channel(f"❌ Connection error: {str(e)}")
                self.voice_client = None
                await asyncio.sleep(5)
                continue

            await asyncio.sleep(5)  # Check connection every 5 seconds

    async def play_welcome(self, member_name):
        """Add member to queue and play welcome sound"""
        self.audio_queue.append(member_name)
        
        if not self.is_playing:
            await self._play_next()

    async def _play_next(self):
        """Play next audio in queue"""
        if not self.audio_queue:
            self.is_playing = False
            return

        if not self.voice_client or not self.voice_client.is_connected():
            self.is_playing = False
            return

        try:
            member_name = self.audio_queue.popleft()
            self.is_playing = True

            audio = discord.FFmpegPCMAudio('welcome.mp3')
            self.voice_client.play(audio, after=lambda e: self.bot.loop.create_task(self._song_finished(e)))
            await self.log_to_channel(f"🎵 Playing welcome sound for {member_name}")

        except Exception as e:
            await self.log_to_channel(f"❌ Error playing audio: {str(e)}")
            self.is_playing = False
            await self._play_next()  # Try next in queue

    async def _song_finished(self, error):
        """Callback when song finishes"""
        if error:
            await self.log_to_channel(f"❌ Error during playback: {str(error)}")
        
        self.is_playing = False
        await self._play_next()  # Play next in queue if any

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Handle voice state updates"""
        if member.bot:
            return

        # Handle user joining welcome channel
        if after.channel and after.channel.id == self.welcome_channel_id:
            if before.channel != after.channel:
                await self.play_welcome(member.name)

async def setup(bot):
    await bot.add_cog(VoiceCommands(bot))
