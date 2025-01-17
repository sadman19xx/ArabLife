import discord
from discord.ext import commands
import logging
import asyncio

logger = logging.getLogger('discord')

class VoiceCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = 1309595750878937240
        self.voice = None
        self.lock = asyncio.Lock()
        self.ready = asyncio.Event()
        bot.loop.create_task(self._connection_loop())

    async def _log(self, msg: str):
        """Log message to both console and channel"""
        logger.info(msg)
        try:
            channel = self.bot.get_channel(self.channel_id)
            if channel:
                await channel.send(f"```\n{msg}\n```")
        except:
            pass

    async def _connection_loop(self):
        """Maintain voice connection"""
        await self.bot.wait_until_ready()
        await asyncio.sleep(5)  # Wait for bot to initialize
        self.ready.set()

        while not self.bot.is_closed():
            try:
                channel = self.bot.get_channel(self.channel_id)
                if not channel:
                    await asyncio.sleep(5)
                    continue

                async with self.lock:
                    # Check if we need to connect
                    if not self.voice or not self.voice.is_connected():
                        # Clean up any existing connection
                        if channel.guild.voice_client:
                            await channel.guild.voice_client.disconnect()
                            await asyncio.sleep(2)

                        # Connect to voice
                        self.voice = await channel.connect(
                            timeout=None,
                            reconnect=True
                        )
                        await self._log("Connected to voice channel")

            except Exception as e:
                await self._log(f"Connection error: {str(e)}")
                self.voice = None
                await asyncio.sleep(5)

            await asyncio.sleep(5)

    async def _play_welcome(self, member_name: str):
        """Play welcome sound"""
        await self.ready.wait()  # Wait for bot to be ready
        
        async with self.lock:
            if not self.voice or not self.voice.is_connected():
                return

            try:
                if self.voice.is_playing():
                    self.voice.stop()

                audio = discord.FFmpegPCMAudio('welcome.mp3')
                self.voice.play(audio)
                await self._log(f"Playing welcome for {member_name}")

            except Exception as e:
                await self._log(f"Playback error: {str(e)}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Handle voice states"""
        await self.ready.wait()  # Wait for bot to be ready

        # Only handle user joins
        if not member.bot and after.channel and after.channel.id == self.channel_id:
            if before.channel != after.channel:
                await self._play_welcome(member.name)

    @commands.command()
    async def rejoin(self, ctx):
        """Force reconnection"""
        self.voice = None  # This will trigger reconnect in connection loop

async def setup(bot):
    await bot.add_cog(VoiceCommands(bot))
