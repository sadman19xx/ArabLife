import discord
import os
import io
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageOps
from discord.ext import commands
from discord import app_commands
from config import Config
import logging
from typing import Tuple
import math

async def create_welcome_image(member: discord.Member, member_count: int) -> discord.File:
    """Create a welcome image with background and circular avatar"""
    async with aiohttp.ClientSession() as session:
        # Download background image
        async with session.get(Config.WELCOME_BACKGROUND_URL) as resp:
            background_data = io.BytesIO(await resp.read())
            background = Image.open(background_data)
            
        # Download avatar image
        async with session.get(str(member.display_avatar.url)) as resp:
            avatar_data = io.BytesIO(await resp.read())
            avatar = Image.open(avatar_data)

    # Resize background if needed
    background = background.resize((1100, 450))
    
    # Create circular mask for avatar
    size = (220, 220)
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + size, fill=255)
    
    # Resize and make avatar circular
    avatar = avatar.resize(size)
    output = ImageOps.fit(avatar, mask.size, centering=(0.5, 0.5))
    output.putalpha(mask)
    
    # Calculate center position for avatar
    avatar_pos = ((background.width - size[0]) // 2, 50)
    
    # Paste avatar onto background
    background.paste(output, avatar_pos, output)
    
    # Add text
    draw = ImageDraw.Draw(background)
    
    # Add semi-transparent overlay for better text readability
    overlay = Image.new('RGBA', background.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle([(0, 280), (background.width, 450)], fill=(0, 0, 0, 128))
    background = Image.alpha_composite(background.convert('RGBA'), overlay)
    
    # Load Arabic font
    title_font = ImageFont.truetype("fonts/arabic.ttf", 60)
    count_font = ImageFont.truetype("fonts/arabic.ttf", 40)
    
    # Add text with the Arabic font
    draw = ImageDraw.Draw(background)
    
    # Welcome text (right to left for Arabic)
    welcome_text = f"{member.name} حياك في سيرفر"
    text_bbox = draw.textbbox((0, 0), welcome_text, font=title_font)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = (background.width - text_width) // 2
    draw.text((text_x, 300), welcome_text, font=title_font, fill='white')
    
    # Member count
    count_text = f"Member #{member_count}"
    count_bbox = draw.textbbox((0, 0), count_text, font=count_font)
    count_width = count_bbox[2] - count_bbox[0]
    count_x = (background.width - count_width) // 2
    draw.text((count_x, 380), count_text, font=count_font, fill='white')
    
    # Save to buffer
    buffer = io.BytesIO()
    background.save(buffer, 'PNG')
    buffer.seek(0)
    
    return discord.File(buffer, 'welcome.png')

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
            # Create and send welcome image
            welcome_image = await create_welcome_image(member, member.guild.member_count)
            await welcome_channel.send(file=welcome_image)
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
            # Create goodbye embed with dark theme
            embed = discord.Embed(color=0x2f3136)  # Discord dark theme color
            
            # Set large member avatar in center
            embed.set_image(url=member.display_avatar.url)
            
            # Add goodbye text and member count
            embed.description = (
                f"**{member.name}** غادر السيرفر\n"
                f"Member #{member.guild.member_count}"
            )
            
            # Set footer with server name
            embed.set_footer(
                text=member.guild.name,
                icon_url=member.guild.icon.url if member.guild.icon else None
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
        name="setwelcomebackground",
        description="Set the background image for welcome messages"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def set_welcome_background(self, interaction: discord.Interaction, url: str):
        """Set the welcome background image URL"""
        try:
            # Validate URL by trying to download the image
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        await interaction.response.send_message(
                            "*رابط الصورة غير صالح.*",
                            ephemeral=True
                        )
                        return
                    
                    # Try to open as image
                    image_data = await resp.read()
                    try:
                        Image.open(io.BytesIO(image_data))
                    except:
                        await interaction.response.send_message(
                            "*الملف ليس صورة صالحة.*",
                            ephemeral=True
                        )
                        return
            
            # Update background URL
            os.environ['WELCOME_BACKGROUND_URL'] = url
            Config.WELCOME_BACKGROUND_URL = url
            
            await interaction.response.send_message(
                "*تم تعيين خلفية رسالة الترحيب.*"
            )
        except Exception as e:
            self.logger.error(f"Error setting welcome background: {str(e)}")
            await interaction.response.send_message(
                "*حدث خطأ أثناء تعيين خلفية رسالة الترحيب.*",
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

            # Create and send welcome image
            welcome_image = await create_welcome_image(member, member.guild.member_count)
            await welcome_channel.send(file=welcome_image)
            
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
