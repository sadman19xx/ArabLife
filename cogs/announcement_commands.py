import discord
from discord.ext import commands
from discord.commands import slash_command, Option
import re

class AnnouncementCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(
        name="announce",
        description="Send an announcement to a specified channel"
    )
    async def announce(
        self,
        ctx,
        message: Option(str, "The announcement message to send", required=True),
        channel: Option(discord.TextChannel, "The channel to send the announcement to", required=True)
    ):
        # Check if bot has permission to send messages in the target channel
        if not channel.permissions_for(ctx.guild.me).send_messages:
            await ctx.respond(
                f"Error: I don't have permission to send messages in {channel.mention}",
                ephemeral=True
            )
            return

        # Check if user has administrator permission
        if not ctx.author.guild_permissions.administrator:
            await ctx.respond(
                "Error: You need 'Administrator' permission to send announcements",
                ephemeral=True
            )
            return

        try:
            # Send the announcement
            await channel.send(f"@everyone {message}")
            
            # Confirm to the user
            await ctx.respond(
                f"✅ Announcement sent successfully to {channel.mention}",
                ephemeral=True
            )
        except discord.Forbidden:
            await ctx.respond(
                f"Error: I don't have permission to mention @everyone in {channel.mention}",
                ephemeral=True
            )
        except discord.HTTPException as e:
            await ctx.respond(
                f"Error: Failed to send announcement. {str(e)}",
                ephemeral=True
            )

def setup(bot):
    bot.add_cog(AnnouncementCommands(bot))
