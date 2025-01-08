import discord
import os
from discord.ext import commands
from discord import app_commands
from config import Config
import logging

class WelcomeCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Send welcome message when a member joins"""
        if member.bot:
            return

        # Get the welcome channel
        welcome_channel = self.bot.get_channel(Config.WELCOME_CHANNEL_ID)
        if not welcome_channel:
            self.logger.warning(f"Welcome channel not found (ID: {Config.WELCOME_CHANNEL_ID})")
            return

        try:
            # Create welcome embed
            embed = discord.Embed(color=Config.WELCOME_EMBED_COLOR)
            
            # Set author with member's name and avatar
            embed.set_author(
                name=f"{member.name} حياك في سيرفر",
                icon_url=member.display_avatar.url
            )
            
            # Set the main image as member's avatar
            embed.set_thumbnail(url=member.display_avatar.url)
            
            # Add member number field
            embed.add_field(
                name="Member",
                value=f"#{member.guild.member_count}",
                inline=False
            )
            
            # Send welcome message and embed
            await welcome_channel.send(embed=embed)
        except Exception as e:
            self.logger.error(f"Error sending welcome message: {str(e)}")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Send goodbye message when a member leaves"""
        if member.bot:
            return

        # Get the welcome channel (we'll use the same channel for goodbye messages)
        welcome_channel = self.bot.get_channel(Config.WELCOME_CHANNEL_ID)
        if not welcome_channel:
            self.logger.warning(f"Welcome channel not found (ID: {Config.WELCOME_CHANNEL_ID})")
            return

        try:
            # Create goodbye embed
            embed = discord.Embed(color=0xff0000)  # Red color for goodbye
            
            # Set author with member's name and avatar
            embed.set_author(
                name=f"{member.name} غادر السيرفر",
                icon_url=member.display_avatar.url
            )
            
            # Set the main image as member's avatar
            embed.set_thumbnail(url=member.display_avatar.url)
            
            # Add member count field
            embed.add_field(
                name="Current Members",
                value=f"#{member.guild.member_count}",
                inline=False
            )
            
            # Send goodbye message
            await welcome_channel.send(embed=embed)
        except Exception as e:
            self.logger.error(f"Error sending goodbye message: {str(e)}")

    @app_commands.command(
        name="setwelcomechannel",
        description="Set the channel for welcome and goodbye messages"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def set_welcome_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Set the welcome channel"""
        try:
            # Update the welcome channel in the environment
            os.environ['WELCOME_CHANNEL_ID'] = str(channel.id)
            Config.WELCOME_CHANNEL_ID = channel.id
            
            await interaction.response.send_message(
                f"*تم تعيين قناة الترحيب إلى {channel.mention}*"
            )
        except Exception as e:
            self.logger.error(f"Error setting welcome channel: {str(e)}")
            await interaction.response.send_message(
                "*حدث خطأ أثناء تعيين قناة الترحيب*",
                ephemeral=True
            )

    @app_commands.command(
        name="testwelcome",
        description="Test the welcome message"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def test_welcome(self, interaction: discord.Interaction):
        """Test the welcome message"""
        try:
            # Simulate a welcome message for the command user
            member = interaction.user
            welcome_channel = self.bot.get_channel(Config.WELCOME_CHANNEL_ID)
            
            if not welcome_channel:
                await interaction.response.send_message(
                    "*لم يتم العثور على قناة الترحيب. يرجى تعيين قناة الترحيب أولاً.*",
                    ephemeral=True
                )
                return

            # Create welcome embed
            embed = discord.Embed(color=Config.WELCOME_EMBED_COLOR)
            
            # Set author with member's name and avatar
            embed.set_author(
                name=f"{member.name} حياك في سيرفر",
                icon_url=member.display_avatar.url
            )
            
            # Set the main image as member's avatar
            embed.set_thumbnail(url=member.display_avatar.url)
            
            # Add member number field
            embed.add_field(
                name="Member",
                value=f"#{member.guild.member_count}",
                inline=False
            )
            
            # Send test welcome message
            await welcome_channel.send(
                "**[TEST]**",
                embed=embed
            )
            
            await interaction.response.send_message(
                "*تم إرسال رسالة الترحيب التجريبية*",
                ephemeral=True
            )
        except Exception as e:
            self.logger.error(f"Error testing welcome message: {str(e)}")
            await interaction.response.send_message(
                "*حدث خطأ أثناء اختبار رسالة الترحيب*",
                ephemeral=True
            )

async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(WelcomeCommands(bot))
