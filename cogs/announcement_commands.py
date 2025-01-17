import discord
from discord.ext import commands
from discord import app_commands
import re

class AnnouncementCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="announce",
        description="Send an announcement to a specified channel"
    )
    @app_commands.describe(
        message="The announcement message to send",
        channel="The channel to send the announcement to"
    )
    async def announce(
        self,
        interaction: discord.Interaction,
        message: str,
        channel: discord.TextChannel
    ):
        # Check if bot has permission to send messages in the target channel
        if not channel.permissions_for(interaction.guild.me).send_messages:
            await interaction.response.send_message(
                f"Error: I don't have permission to send messages in {channel.mention}",
                ephemeral=True
            )
            return

        # Check if user has administrator permission
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "Error: You need 'Administrator' permission to send announcements",
                ephemeral=True
            )
            return

        try:
            # Send the announcement
            await channel.send(f"@everyone {message}")
            
            # Confirm to the user
            await interaction.response.send_message(
                f"✅ Announcement sent successfully to {channel.mention}",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                f"Error: I don't have permission to mention @everyone in {channel.mention}",
                ephemeral=True
            )
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f"Error: Failed to send announcement. {str(e)}",
                ephemeral=True
            )

def setup(bot):
    bot.add_cog(AnnouncementCommands(bot))
