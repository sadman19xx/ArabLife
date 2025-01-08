import discord
from discord.ext import commands
from discord.ext.commands import Cog
from discord import app_commands
import logging
from config import Config
import asyncio
import json
from datetime import datetime
import io

logger = logging.getLogger('discord')

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.primary, emoji="🎫", custom_id="create_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await TicketCommands.create_ticket(interaction)

class StaffView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Claim Ticket", style=discord.ButtonStyle.green, emoji="✋", custom_id="claim_ticket")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await TicketCommands.claim_ticket(interaction)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, emoji="🔒", custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await TicketCommands.close_ticket(interaction)

    @discord.ui.button(label="Save Transcript", style=discord.ButtonStyle.gray, emoji="📑", custom_id="save_transcript")
    async def save_transcript(self, interaction: discord.Interaction, button: discord.ui.Button):
        await TicketCommands.save_transcript(interaction)

class TicketCommands(Cog):
    """Cog for MEE6-like ticket system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.active_tickets = {}  # {channel_id: {"user_id": id, "claimed_by": id}}
        self.load_tickets()

    def load_tickets(self):
        """Load active tickets from JSON file"""
        try:
            with open('tickets.json', 'r') as f:
                self.active_tickets = json.load(f)
        except FileNotFoundError:
            self.active_tickets = {}

    def save_tickets(self):
        """Save active tickets to JSON file"""
        with open('tickets.json', 'w') as f:
            json.dump(self.active_tickets, f)

    @app_commands.command(name="setup-tickets")
    @app_commands.default_permissions(administrator=True)
    async def setup_tickets(self, interaction: discord.Interaction):
        """Setup the ticket system with buttons"""
        try:
            embed = discord.Embed(
                title="نظام التذاكر",
                description=(
                    "مرحباً بك في نظام التذاكر!\n\n"
                    "للحصول على المساعدة، اضغط على الزر أدناه لإنشاء تذكرة جديدة.\n"
                    "سيقوم فريق الدعم بالرد عليك في أقرب وقت ممكن."
                ),
                color=discord.Color.blue()
            )
            
            await interaction.channel.send(embed=embed, view=TicketView())
            await interaction.response.send_message("*تم إعداد نظام التذاكر بنجاح.*", ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error setting up ticket system: {str(e)}")
            await interaction.response.send_message("*حدث خطأ أثناء إعداد نظام التذاكر.*", ephemeral=True)

    @staticmethod
    async def create_ticket(interaction: discord.Interaction):
        """Create a new ticket"""
        cog = interaction.client.get_cog("TicketCommands")
        
        # Check if user has an active ticket
        for ticket_data in cog.active_tickets.values():
            if ticket_data["user_id"] == interaction.user.id:
                await interaction.followup.send(
                    "*لديك تذكرة نشطة بالفعل.*",
                    ephemeral=True
                )
                return

        try:
            # Create ticket channel
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            
            # Add staff role permissions
            if hasattr(Config, 'TICKET_STAFF_ROLE_ID'):
                staff_role = interaction.guild.get_role(Config.TICKET_STAFF_ROLE_ID)
                if staff_role:
                    overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

            # Create channel in ticket category
            category = interaction.guild.get_channel(Config.TICKET_CATEGORY_ID)
            ticket_channel = await interaction.guild.create_text_channel(
                f"ticket-{interaction.user.name}",
                overwrites=overwrites,
                category=category
            )
            
            # Store ticket info
            cog.active_tickets[ticket_channel.id] = {
                "user_id": interaction.user.id,
                "claimed_by": None,
                "created_at": datetime.now().isoformat()
            }
            cog.save_tickets()

            # Send initial message
            embed = discord.Embed(
                title="تذكرة جديدة",
                description=(
                    f"مرحباً {interaction.user.mention}!\n\n"
                    "سيقوم فريق الدعم بالرد عليك قريباً.\n"
                    "يرجى وصف مشكلتك بالتفصيل."
                ),
                color=discord.Color.green()
            )
            await ticket_channel.send(embed=embed, view=StaffView())
            
            # Send confirmation
            await interaction.followup.send(
                f"*تم إنشاء تذكرتك في {ticket_channel.mention}*",
                ephemeral=True
            )

            # Log ticket creation
            if hasattr(Config, 'TICKET_LOG_CHANNEL_ID'):
                log_channel = interaction.guild.get_channel(Config.TICKET_LOG_CHANNEL_ID)
                if log_channel:
                    await log_channel.send(f"🎫 تم إنشاء تذكرة جديدة بواسطة {interaction.user.mention} ({ticket_channel.mention})")

        except Exception as e:
            logger.error(f"Error creating ticket: {str(e)}")
            await interaction.followup.send("*حدث خطأ أثناء إنشاء التذكرة.*", ephemeral=True)

    @staticmethod
    async def claim_ticket(interaction: discord.Interaction):
        """Claim a ticket"""
        cog = interaction.client.get_cog("TicketCommands")
        
        if not interaction.channel.id in cog.active_tickets:
            await interaction.response.send_message("*هذه ليست قناة تذكرة.*", ephemeral=True)
            return

        ticket_data = cog.active_tickets[interaction.channel.id]
        
        # Check if user has staff role
        if not interaction.user.get_role(Config.TICKET_STAFF_ROLE_ID):
            await interaction.response.send_message("*لا تملك صلاحية المطالبة بالتذاكر.*", ephemeral=True)
            return

        # Check if ticket is already claimed
        if ticket_data["claimed_by"]:
            claimer = interaction.guild.get_member(ticket_data["claimed_by"])
            await interaction.response.send_message(
                f"*هذه التذكرة تم المطالبة بها من قبل {claimer.mention}*",
                ephemeral=True
            )
            return

        try:
            # Update ticket data
            ticket_data["claimed_by"] = interaction.user.id
            cog.save_tickets()

            # Send confirmation
            embed = discord.Embed(
                description=f"تم المطالبة بالتذكرة من قبل {interaction.user.mention}",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)

            # Log claim
            if hasattr(Config, 'TICKET_LOG_CHANNEL_ID'):
                log_channel = interaction.guild.get_channel(Config.TICKET_LOG_CHANNEL_ID)
                if log_channel:
                    await log_channel.send(f"✋ تم المطالبة بالتذكرة {interaction.channel.mention} من قبل {interaction.user.mention}")

        except Exception as e:
            logger.error(f"Error claiming ticket: {str(e)}")
            await interaction.response.send_message("*حدث خطأ أثناء المطالبة بالتذكرة.*", ephemeral=True)

    @staticmethod
    async def save_transcript(interaction: discord.Interaction):
        """Save ticket transcript"""
        try:
            messages = []
            async for message in interaction.channel.history(limit=None, oldest_first=True):
                timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
                messages.append(f"[{timestamp}] {message.author}: {message.content}")

            transcript = "\n".join(messages)
            
            # Create file
            file = discord.File(
                io.StringIO(transcript),
                filename=f"transcript-{interaction.channel.name}.txt"
            )

            # Send to log channel
            if hasattr(Config, 'TICKET_LOG_CHANNEL_ID'):
                log_channel = interaction.guild.get_channel(Config.TICKET_LOG_CHANNEL_ID)
                if log_channel:
                    await log_channel.send(
                        f"📑 Transcript for {interaction.channel.mention}",
                        file=file
                    )

            await interaction.response.send_message("*تم حفظ نسخة من المحادثة.*", ephemeral=True)

        except Exception as e:
            logger.error(f"Error saving transcript: {str(e)}")
            await interaction.response.send_message("*حدث خطأ أثناء حفظ نسخة المحادثة.*", ephemeral=True)

    @staticmethod
    async def close_ticket(interaction: discord.Interaction):
        """Close a ticket"""
        cog = interaction.client.get_cog("TicketCommands")
        
        if not interaction.channel.id in cog.active_tickets:
            await interaction.response.send_message("*هذه ليست قناة تذكرة.*", ephemeral=True)
            return

        try:
            # Save transcript first
            await TicketCommands.save_transcript(interaction)

            # Send closing message
            embed = discord.Embed(
                title="إغلاق التذكرة",
                description="سيتم حذف هذه القناة خلال 5 ثواني...",
                color=discord.Color.red()
            )
            await interaction.channel.send(embed=embed)
            
            # Log closure
            if hasattr(Config, 'TICKET_LOG_CHANNEL_ID'):
                log_channel = interaction.guild.get_channel(Config.TICKET_LOG_CHANNEL_ID)
                if log_channel:
                    await log_channel.send(f"🔒 تم إغلاق التذكرة {interaction.channel.name} من قبل {interaction.user.mention}")

            # Remove from active tickets
            del cog.active_tickets[interaction.channel.id]
            cog.save_tickets()
            
            # Wait and delete channel
            await asyncio.sleep(5)
            await interaction.channel.delete()

        except Exception as e:
            logger.error(f"Error closing ticket: {str(e)}")
            await interaction.response.send_message("*حدث خطأ أثناء إغلاق التذكرة.*", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketCommands(bot))
