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

class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="تذكرة رفعة (شكوى على لاعب)",
                description="عدم التقيد بالقوانين والشغب في افساد متعة اللعب وتخلك الحدود",
                emoji="👊",
                value="player_report"
            ),
            discord.SelectOption(
                label="تذكرة لوزارة الصحة",
                description="عدم اتباع البروتوكول لوزارة الصحة و وجود احتجاز واضح بالقانون",
                emoji="🏥",
                value="health"
            ),
            discord.SelectOption(
                label="تذكرة لوزارة الداخلية",
                description="عدم اتباع البروتوكول لوزارة الداخلية وتطلع على احد منسوبيها",
                emoji="👮",
                value="interior"
            ),
            discord.SelectOption(
                label="ملاحظات واقتراحات",
                description="رايك مهم في تطوير السيرفر",
                emoji="📝",
                value="feedback"
            )
        ]
        super().__init__(
            placeholder="اختر نوع التذكرة",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_select"
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await TicketCommands.create_ticket(interaction, self.values[0])

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

class StaffView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="استلام", style=discord.ButtonStyle.blurple, emoji="📌", custom_id="claim_ticket", row=0)
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await TicketCommands.claim_ticket(interaction)

    @discord.ui.button(label="اغلاق", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_ticket", row=0)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await TicketCommands.close_ticket(interaction)

    @discord.ui.button(label="اعادة فتح", style=discord.ButtonStyle.success, emoji="🔓", custom_id="reopen_ticket", row=0)
    async def reopen_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await TicketCommands.reopen_ticket(interaction)

    @discord.ui.button(label="حذف", style=discord.ButtonStyle.red, emoji="🗑️", custom_id="delete_ticket", row=0)
    async def delete_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await TicketCommands.delete_ticket(interaction)

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
                title="فريق الدعم في خدمتك",
                description=(
                    "الرجاء الضغط على أحد الخيارات المناسبة لمشكلتك\n\n"
                    "👊 **تذكرة رفعة (شكوى على لاعب)**\n"
                    "عدم التقيد بالقوانين والشغب في افساد متعة اللعب وتخلك الحدود\n\n"
                    "🏥 **تذكرة لوزارة الصحة**\n"
                    "عدم اتباع البروتوكول لوزارة الصحة و وجود احتجاز واضح بالقانون\n\n"
                    "👮 **تذكرة لوزارة الداخلية**\n"
                    "عدم اتباع البروتوكول لوزارة الداخلية وتطلع على احد منسوبيها\n\n"
                    "📝 **ملاحظات واقتراحات**\n"
                    "رايك مهم في تطوير السيرفر"
                ),
                color=discord.Color.blue()
            )
            
            await interaction.channel.send(embed=embed, view=TicketView())
            await interaction.response.send_message("*تم إعداد نظام التذاكر بنجاح.*", ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error setting up ticket system: {str(e)}")
            await interaction.response.send_message("*حدث خطأ أثناء إعداد نظام التذاكر.*", ephemeral=True)

    @staticmethod
    async def create_ticket(interaction: discord.Interaction, ticket_type: str):
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
            # Get ticket type details
            ticket_types = {
                "player_report": {
                    "name": "شكوى-على-لاعب",
                    "emoji": "👊",
                    "color": discord.Color.red(),
                    "role_id": Config.PLAYER_REPORT_ROLE_ID
                },
                "health": {
                    "name": "وزارة-الصحة",
                    "emoji": "🏥",
                    "color": discord.Color.green(),
                    "role_id": Config.HEALTH_DEPT_ROLE_ID
                },
                "interior": {
                    "name": "وزارة-الداخلية",
                    "emoji": "👮",
                    "color": discord.Color.blue(),
                    "role_id": Config.INTERIOR_DEPT_ROLE_ID
                },
                "feedback": {
                    "name": "اقتراح",
                    "emoji": "📝",
                    "color": discord.Color.gold(),
                    "role_id": Config.FEEDBACK_ROLE_ID
                }
            }
            
            ticket_info = ticket_types.get(ticket_type)
            if not ticket_info:
                await interaction.followup.send("*نوع تذكرة غير صالح.*", ephemeral=True)
                return

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
                f"{ticket_info['emoji']}-{ticket_info['name']}-{interaction.user.name}",
                overwrites=overwrites,
                category=category
            )
            
            # Store ticket info
            cog.active_tickets[ticket_channel.id] = {
                "user_id": interaction.user.id,
                "claimed_by": None,
                "created_at": datetime.now().isoformat(),
                "ticket_type": ticket_type
            }
            cog.save_tickets()

            # Get department role and ticket number
            dept_role = interaction.guild.get_role(ticket_info['role_id'])
            dept_mention = dept_role.mention if dept_role else "فريق الدعم"
            ticket_number = len(cog.active_tickets) + 1
            
            # Create welcome embed
            embed = discord.Embed(color=ticket_info['color'])
            
            # Set author with ticket info
            embed.set_author(
                name=f"تذكرة جديدة • #{ticket_number}",
                icon_url=interaction.guild.icon.url if interaction.guild.icon else None
            )
            
            # Add ticket information fields
            embed.add_field(
                name="صاحب التذكرة",
                value=interaction.user.mention,
                inline=True
            )
            embed.add_field(
                name="القسم",
                value=f"{ticket_info['emoji']} {ticket_info['name']}",
                inline=True
            )
            embed.add_field(
                name="الحالة",
                value="🟢 مفتوحة",
                inline=True
            )
            
            # Add response time field
            embed.add_field(
                name="وقت الرد المتوقع",
                value="خلال 24 ساعة",
                inline=False
            )
            
            # Add instructions
            embed.add_field(
                name="تعليمات",
                value=(
                    "• يرجى وصف مشكلتك بالتفصيل\n"
                    "• اذكر جميع المعلومات المهمة\n"
                    "• كن محترماً ومتعاوناً مع فريق الدعم"
                ),
                inline=False
            )
            
            # Set footer with timestamp
            embed.set_footer(
                text=interaction.guild.name,
                icon_url=interaction.guild.icon.url if interaction.guild.icon else None
            )
            embed.timestamp = datetime.now()
            
            # Send message with department mention
            await ticket_channel.send(
                f"{dept_mention}\n" + 
                f"مرحباً {interaction.user.mention}، سيتم الرد على تذكرتك في أقرب وقت ممكن.",
                embed=embed,
                view=StaffView()
            )
            
            # Send confirmation
            await interaction.followup.send(
                f"*تم إنشاء تذكرتك في {ticket_channel.mention}*",
                ephemeral=True
            )

            # Log ticket creation
            if hasattr(Config, 'TICKET_LOG_CHANNEL_ID'):
                log_channel = interaction.guild.get_channel(Config.TICKET_LOG_CHANNEL_ID)
                if log_channel:
                    await log_channel.send(
                        f"{ticket_info['emoji']} تم إنشاء تذكرة {ticket_info['name']} بواسطة {interaction.user.mention} ({ticket_channel.mention})"
                    )

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

    @staticmethod
    async def reopen_ticket(interaction: discord.Interaction):
        """Reopen a closed ticket"""
        try:
            # Update channel permissions
            await interaction.channel.set_permissions(interaction.guild.default_role, read_messages=False)
            ticket_user = await interaction.guild.fetch_member(interaction.client.get_cog("TicketCommands").active_tickets[interaction.channel.id]["user_id"])
            if ticket_user:
                await interaction.channel.set_permissions(ticket_user, read_messages=True, send_messages=True)
            
            embed = discord.Embed(
                description=f"تم إعادة فتح التذكرة من قبل {interaction.user.mention}",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)

            # Log reopen
            if hasattr(Config, 'TICKET_LOG_CHANNEL_ID'):
                log_channel = interaction.guild.get_channel(Config.TICKET_LOG_CHANNEL_ID)
                if log_channel:
                    await log_channel.send(f"🔓 تم إعادة فتح التذكرة {interaction.channel.mention} من قبل {interaction.user.mention}")

        except Exception as e:
            logger.error(f"Error reopening ticket: {str(e)}")
            await interaction.response.send_message("*حدث خطأ أثناء إعادة فتح التذكرة.*", ephemeral=True)

    @staticmethod
    async def delete_ticket(interaction: discord.Interaction):
        """Delete a ticket immediately"""
        try:
            # Save transcript first
            await TicketCommands.save_transcript(interaction)
            
            # Log deletion
            if hasattr(Config, 'TICKET_LOG_CHANNEL_ID'):
                log_channel = interaction.guild.get_channel(Config.TICKET_LOG_CHANNEL_ID)
                if log_channel:
                    await log_channel.send(f"🗑️ تم حذف التذكرة {interaction.channel.name} من قبل {interaction.user.mention}")

            # Remove from active tickets
            interaction.client.get_cog("TicketCommands").active_tickets.pop(interaction.channel.id, None)
            
            # Delete channel immediately
            await interaction.channel.delete()

        except Exception as e:
            logger.error(f"Error deleting ticket: {str(e)}")
            await interaction.response.send_message("*حدث خطأ أثناء حذف التذكرة.*", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TicketCommands(bot))
