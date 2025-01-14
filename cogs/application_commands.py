import discord
from discord.ext import commands
from discord import app_commands
import os
from typing import Optional

class ApplicationCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.staff_role_id = 1287486561914589346
        self.citizen_role_id = 1309555494586683474
        self.response_channel_id = 1309556312027430922

    def has_staff_role(self, member: discord.Member) -> bool:
        """Check if member has the required staff role."""
        return any(role.id == self.staff_role_id for role in member.roles)

    @app_commands.command(name="accept", description="Accept a user's application")
    async def accept(self, interaction: discord.Interaction, user: discord.Member):
        # Check if the command user has staff role
        if not self.has_staff_role(interaction.user):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return

        # Get the response channel first
        response_channel = self.bot.get_channel(self.response_channel_id)
        if not response_channel:
            await interaction.response.send_message("Could not find the response channel.", ephemeral=True)
            return

        # Get the citizen role
        citizen_role = interaction.guild.get_role(self.citizen_role_id)
        if not citizen_role:
            await interaction.response.send_message("Could not find the citizen role.", ephemeral=True)
            return

        # Send initial response
        await interaction.response.send_message(f"Processing approval for {user.mention}...", ephemeral=True)

        try:
            # Add the role to the user
            await user.add_roles(citizen_role)

            # Create and send response message with approved visa image
            embed = discord.Embed(
                title="Application Response",
                description=f"{user.mention} Visa Application Has Been Approved!\n\nAccepted By: {interaction.user.mention}",
                color=discord.Color.green()
            )

            # Attach the approved visa image
            file = discord.File("assets/accept.png", filename="accept.png")
            embed.set_image(url="attachment://accept.png")
            
            # Send the embed to the response channel
            await response_channel.send(embed=embed, file=file)

        except Exception as e:
            # Log the error but don't try to send another response
            print(f"Error in accept command: {str(e)}")

    @app_commands.command(name="reject", description="Reject a user's application")
    async def reject(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        # Check if the command user has staff role
        if not self.has_staff_role(interaction.user):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return

        # Get the response channel first
        response_channel = self.bot.get_channel(self.response_channel_id)
        if not response_channel:
            await interaction.response.send_message("Could not find the response channel.", ephemeral=True)
            return

        # Send initial response
        await interaction.response.send_message(f"Processing rejection for {user.mention}...", ephemeral=True)

        try:
            # Create and send response message with rejected visa image
            embed = discord.Embed(
                title="Application Response",
                description=f"{user.mention} Visa Application Has Been Rejected!\n\nRejected By: {interaction.user.mention}\nReason: {reason}",
                color=discord.Color.red()
            )

            # Attach the rejected visa image
            file = discord.File("assets/reject.png", filename="reject.png")
            embed.set_image(url="attachment://reject.png")
            
            # Send the embed to the response channel
            await response_channel.send(embed=embed, file=file)

        except Exception as e:
            # Log the error but don't try to send another response
            print(f"Error in reject command: {str(e)}")

async def setup(bot):
    await bot.add_cog(ApplicationCommands(bot))
