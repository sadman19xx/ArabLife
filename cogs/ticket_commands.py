import discord
from discord.ext import commands, tasks
from discord import app_commands
from discord.ext.commands import Cog
import logging
import asyncio
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from config import Config
from utils.database import db
from utils.logger import LoggerMixin
import io
import json

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


class TicketCommands(Cog, LoggerMixin):
    """Cog for ticket system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.active_tickets = {}  # Cache for active tickets
        self.load_tickets_from_db.start()  # Start background task

    def cog_unload(self):
        """Cleanup when cog is unloaded"""
        self.load_tickets_from_db.cancel()

    @tasks.loop(minutes=5)
    async def load_tickets_from_db(self):
        """Periodically load active tickets from database"""
        try:
            async with db.transaction() as cursor:
                await cursor.execute("""
                    SELECT channel_id, user_id, claimed_by, ticket_type, created_at
                    FROM tickets
                    WHERE status = 'open'
                """)
                tickets = await cursor.fetchall()
                
                self.active_tickets = {
                    str(ticket[0]): {
                        "user_id": str(ticket[1]),
                        "claimed_by": str(ticket[2]) if ticket[2] else None,
                        "ticket_type": ticket[3],
                        "created_at": ticket[4]
                    }
                    for ticket in tickets
                }
        except Exception as e:
            self.log.error(f"Error loading tickets from database: {e}")

    @load_tickets_from_db.before_loop
    async def before_load_tickets(self):
        """Wait for bot to be ready before starting task"""
        await self.bot.wait_until_ready()

    async def get_ticket_types(self) -> Dict[str, Dict]:
        """Get ticket type configurations"""
        return {
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

    @staticmethod
    async def create_ticket(interaction: discord.Interaction, ticket_type: str):
        """Create a new ticket"""
        cog = interaction.client.get_cog("TicketCommands")
        
        # Check if user has an active ticket
        async with db.transaction() as cursor:
            await cursor.execute("""
                SELECT COUNT(*) FROM tickets
                WHERE user_id = ? AND status = 'open'
            """, (str(interaction.user.id),))
            active_tickets = (await cursor.fetchone())[0]
            
            if active_tickets > 0:
                await interaction.followup.send(
                    "*لديك تذكرة نشطة بالفعل.*",
                    ephemeral=True
                )
                return

        try:
            ticket_types = await cog.get_ticket_types()
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
            
            # Store ticket in database
            async with db.transaction() as cursor:
                await cursor.execute("""
                    INSERT INTO tickets (
                        channel_id, user_id, ticket_type, status, created_at
                    ) VALUES (?, ?, ?, 'open', CURRENT_TIMESTAMP)
                    RETURNING id
                """, (str(ticket_channel.id), str(interaction.user.id), ticket_type))
                ticket_id = (await cursor.fetchone())[0]
            
            # Update cache
            cog.active_tickets[str(ticket_channel.id)] = {
                "user_id": str(interaction.user.id),
                "claimed_by": None,
                "ticket_type": ticket_type,
                "created_at": datetime.now().isoformat()
            }

            # Get department role and create welcome embed
            dept_role = interaction.guild.get_role(ticket_info['role_id'])
            dept_mention = dept_role.mention if dept_role else "فريق الدعم"
            
            embed = discord.Embed(color=ticket_info['color'])
            embed.set_author(
                name=f"تذكرة جديدة • #{ticket_id}",
                icon_url=interaction.guild.icon.url if interaction.guild.icon else None
            )
            
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
            
            embed.add_field(
                name="وقت الرد المتوقع",
                value="خلال 24 ساعة",
                inline=False
            )
            
            embed.add_field(
                name="تعليمات",
                value=(
                    "• يرجى وصف مشكلتك بالتفصيل\n"
                    "• اذكر جميع المعلومات المهمة\n"
                    "• كن محترماً ومتعاوناً مع فريق الدعم"
                ),
                inline=False
            )
            
            embed.set_footer(
                text=interaction.guild.name,
                icon_url=interaction.guild.icon.url if interaction.guild.icon else None
            )
            embed.timestamp = datetime.now()
            
            await ticket_channel.send(
                f"{dept_mention}\n" + 
                f"مرحباً {interaction.user.mention}، سيتم الرد على تذكرتك في أقرب وقت ممكن.",
                embed=embed,
                view=StaffView()
            )
            
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
            cog.log.error(f"Error creating ticket: {e}")
            await interaction.followup.send("*حدث خطأ أثناء إنشاء التذكرة.*", ephemeral=True)

    @staticmethod
    async def claim_ticket(interaction: discord.Interaction):
        """Claim a ticket"""
        cog = interaction.client.get_cog("TicketCommands")
        
        if not interaction.channel.id in cog.active_tickets:
            await interaction.response.send_message("*هذه ليست قناة تذكرة.*", ephemeral=True)
            return

        ticket_data = cog.active_tickets[str(interaction.channel.id)]
        
        # Check if user has staff role
        if not interaction.user.get_role(Config.TICKET_STAFF_ROLE_ID):
            await interaction.response.send_message("*لا تملك صلاحية المطالبة بالتذاكر.*", ephemeral=True)
            return

        # Check if ticket is already claimed
        if ticket_data["claimed_by"]:
            claimer = interaction.guild.get_member(int(ticket_data["claimed_by"]))
            await interaction.response.send_message(
                f"*هذه التذكرة تم المطالبة بها من قبل {claimer.mention}*",
                ephemeral=True
            )
            return

        try:
            # Update database
            async with db.transaction() as cursor:
                await cursor.execute("""
                    UPDATE tickets 
                    SET claimed_by = ?, claimed_at = CURRENT_TIMESTAMP
                    WHERE channel_id = ?
                """, (str(interaction.user.id), str(interaction.channel.id)))
            
            # Update cache
            ticket_data["claimed_by"] = str(interaction.user.id)

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
                    await log_channel.send(
                        f"✋ تم المطالبة بالتذكرة {interaction.channel.mention} من قبل {interaction.user.mention}"
                    )

        except Exception as e:
            cog.log.error(f"Error claiming ticket: {e}")
            await interaction.response.send_message(
                "*حدث خطأ أثناء المطالبة بالتذكرة.*",
                ephemeral=True
            )

    @staticmethod
    async def close_ticket(interaction: discord.Interaction):
        """Close a ticket"""
        cog = interaction.client.get_cog("TicketCommands")
        
        if str(interaction.channel.id) not in cog.active_tickets:
            await interaction.response.send_message("*هذه ليست قناة تذكرة.*", ephemeral=True)
            return

        try:
            # Save transcript
            messages = []
            async for message in interaction.channel.history(limit=None, oldest_first=True):
                timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
                content = message.content or "[No content]"
                for embed in message.embeds:
                    content += f"\n[Embed: {embed.title or 'No title'}]"
                for attachment in message.attachments:
                    content += f"\n[Attachment: {attachment.filename}]"
                messages.append(f"[{timestamp}] {message.author}: {content}")

            transcript = "\n".join(messages)
            transcript_file = discord.File(
                io.StringIO(transcript),
                filename=f"transcript-{interaction.channel.name}.txt"
            )

            # Update database
            async with db.transaction() as cursor:
                await cursor.execute("""
                    UPDATE tickets 
                    SET status = 'closed', closed_at = CURRENT_TIMESTAMP, 
                        closed_by = ?, transcript = ?
                    WHERE channel_id = ?
                """, (
                    str(interaction.user.id),
                    transcript,
                    str(interaction.channel.id)
                ))

            # Remove from cache
            del cog.active_tickets[str(interaction.channel.id)]

            # Send closing message
            embed = discord.Embed(
                title="إغلاق التذكرة",
                description="سيتم حذف هذه القناة خلال 5 ثواني...",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            
            # Log closure and transcript
            if hasattr(Config, 'TICKET_LOG_CHANNEL_ID'):
                log_channel = interaction.guild.get_channel(Config.TICKET_LOG_CHANNEL_ID)
                if log_channel:
                    await log_channel.send(
                        f"🔒 تم إغلاق التذكرة {interaction.channel.name} من قبل {interaction.user.mention}",
                        file=transcript_file
                    )
            
            # Wait and delete channel
            await asyncio.sleep(5)
            await interaction.channel.delete()

        except Exception as e:
            cog.log.error(f"Error closing ticket: {e}")
            await interaction.followup.send(
                "*حدث خطأ أثناء إغلاق التذكرة.*",
                ephemeral=True
            )

    @staticmethod
    async def reopen_ticket(interaction: discord.Interaction):
        """Reopen a closed ticket"""
        cog = interaction.client.get_cog("TicketCommands")
        
        try:
            # Update database
            async with db.transaction() as cursor:
                await cursor.execute("""
                    UPDATE tickets 
                    SET status = 'open', reopened_at = CURRENT_TIMESTAMP,
                        reopened_by = ?
                    WHERE channel_id = ?
                """, (str(interaction.user.id), str(interaction.channel.id)))
            
            # Update permissions
            await interaction.channel.set_permissions(
                interaction.guild.default_role,
                read_messages=False
            )
            ticket_user = await interaction.guild.fetch_member(
                int(cog.active_tickets[str(interaction.channel.id)]["user_id"])
            )
            if ticket_user:
                await interaction.channel.set_permissions(
                    ticket_user,
                    read_messages=True,
                    send_messages=True
                )
            
            embed = discord.Embed(
                description=f"تم إعادة فتح التذكرة من قبل {interaction.user.mention}",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)

            # Log reopen
            if hasattr(Config, 'TICKET_LOG_CHANNEL_ID'):
                log_channel = interaction.guild.get_channel(Config.TICKET_LOG_CHANNEL_ID)
                if log_channel:
                    await log_channel.send(
                        f"🔓 تم إعادة فتح التذكرة {interaction.channel.mention} من قبل {interaction.user.mention}"
                    )

        except Exception as e:
            cog.log.error(f"Error reopening ticket: {e}")
            await interaction.response.send_message(
                "*حدث خطأ أثناء إعادة فتح التذكرة.*",
                ephemeral=True
            )

    @staticmethod
    async def delete_ticket(interaction: discord.Interaction):
        """Delete a ticket immediately"""
        cog = interaction.client.get_cog("TicketCommands")
        
        if str(interaction.channel.id) not in cog.active_tickets:
            await interaction.response.send_message("*هذه ليست قناة تذكرة.*", ephemeral=True)
            return

        try:
            # Save transcript first
            messages = []
            async for message in interaction.channel.history(limit=None, oldest_first=True):
                timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
                content = message.content or "[No content]"
                for embed in message.embeds:
                    content += f"\n[Embed: {embed.title or 'No title'}]"
                for attachment in message.attachments:
                    content += f"\n[Attachment: {attachment.filename}]"
                messages.append(f"[{timestamp}] {message.author}: {content}")

            transcript = "\n".join(messages)
            transcript_file = discord.File(
                io.StringIO(transcript),
                filename=f"transcript-{interaction.channel.name}.txt"
            )
            
            # Update database
            async with db.transaction() as cursor:
                await cursor.execute("""
                    UPDATE tickets 
                    SET status = 'deleted', deleted_at = CURRENT_TIMESTAMP,
                        deleted_by = ?, transcript = ?
                    WHERE channel_id = ?
                """, (
                    str(interaction.user.id),
                    transcript,
                    str(interaction.channel.id)
                ))
            
            # Remove from cache
            del cog.active_tickets[str(interaction.channel.id)]
            
            # Log deletion and transcript
            if hasattr(Config, 'TICKET_LOG_CHANNEL_ID'):
                log_channel = interaction.guild.get_channel(Config.TICKET_LOG_CHANNEL_ID)
                if log_channel:
                    await log_channel.send(
                        f"🗑️ تم حذف التذكرة {interaction.channel.name} من قبل {interaction.user.mention}",
                        file=transcript_file
                    )

            # Delete channel immediately
            await interaction.channel.delete()

        except Exception as e:
            cog.log.error(f"Error deleting ticket: {e}")
            await interaction.followup.send(
                "*حدث خطأ أثناء حذف التذكرة.*",
                ephemeral=True
            )

    @app_commands.command(
        name="setup-tickets",
        description="Setup the ticket system"
    )
    @app_commands.checks.has_permissions(administrator=True)
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
            self.log.error(f"Error setting up ticket system: {e}")
            await interaction.response.send_message("*حدث خطأ أثناء إعداد نظام التذاكر.*", ephemeral=True)

    @app_commands.command(
        name="ticket-stats",
        description="Show ticket statistics"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket_stats(self, interaction: discord.Interaction):
        """Show ticket statistics"""
        try:
            async with db.transaction() as cursor:
                # Get total tickets
                await cursor.execute("SELECT COUNT(*) FROM tickets")
                total_tickets = (await cursor.fetchone())[0]
                
                # Get open tickets
                await cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'open'")
                open_tickets = (await cursor.fetchone())[0]
                
                # Get tickets by type
                await cursor.execute("""
                    SELECT ticket_type, COUNT(*) 
                    FROM tickets 
                    GROUP BY ticket_type
                """)
                type_stats = await cursor.fetchall()
                
                # Get average response time
                await cursor.execute("""
                    SELECT AVG(JULIANDAY(closed_at) - JULIANDAY(created_at)) * 24
                    FROM tickets 
                    WHERE status = 'closed'
                """)
                avg_response = (await cursor.fetchone())[0]
                
            embed = discord.Embed(
                title="📊 إحصائيات التذاكر",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="إجمالي التذاكر",
                value=str(total_tickets),
                inline=True
            )
            embed.add_field(
                name="التذاكر المفتوحة",
                value=str(open_tickets),
                inline=True
            )
            
            if avg_response:
                embed.add_field(
                    name="متوسط وقت الرد",
                    value=f"{avg_response:.1f} ساعات",
                    inline=True
                )
            
            # Add type statistics
            ticket_types = await self.get_ticket_types()
            for ticket_type, count in type_stats:
                type_info = ticket_types.get(ticket_type, {})
                embed.add_field(
                    name=f"{type_info.get('emoji', '❓')} {type_info.get('name', ticket_type)}",
                    value=str(count),
                    inline=True
                )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            self.log.error(f"Error getting ticket stats: {e}")
            await interaction.response.send_message(
                "*حدث خطأ أثناء جلب إحصائيات التذاكر.*",
                ephemeral=True
            )

    @app_commands.command(
        name="ticket-search",
        description="Search for tickets"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket_search(
        self,
        interaction: discord.Interaction,
        user: Optional[discord.Member] = None,
        ticket_type: Optional[str] = None,
        status: Optional[str] = None
    ):
        """Search for tickets with filters"""
        try:
            query = "SELECT * FROM tickets WHERE 1=1"
            params = []
            
            if user:
                query += " AND user_id = ?"
                params.append(str(user.id))
            
            if ticket_type:
                query += " AND ticket_type = ?"
                params.append(ticket_type)
                
            if status:
                query += " AND status = ?"
                params.append(status)
                
            query += " ORDER BY created_at DESC LIMIT 10"
            
            async with db.transaction() as cursor:
                await cursor.execute(query, params)
                tickets = await cursor.fetchall()
                
            if not tickets:
                await interaction.response.send_message(
                    "*لم يتم العثور على تذاكر.*",
                    ephemeral=True
                )
                return
                
            embed = discord.Embed(
                title="🔍 نتائج البحث",
                color=discord.Color.blue()
            )
            
            ticket_types = await self.get_ticket_types()
            
            for ticket in tickets:
                type_info = ticket_types.get(ticket['ticket_type'], {})
                embed.add_field(
                    name=f"{type_info.get('emoji', '❓')} تذكرة #{ticket['id']}",
                    value=(
                        f"المستخدم: <@{ticket['user_id']}>\n"
                        f"الحالة: {ticket['status']}\n"
                        f"التاريخ: {ticket['created_at']}"
                    ),
                    inline=False
                )
                
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            self.log.error(f"Error searching tickets: {e}")
            await interaction.response.send_message(
                "*حدث خطأ أثناء البحث عن التذاكر.*",
                ephemeral=True
            )

async def setup(bot):
    """Setup function for loading the cog"""
    # Create cog instance
    cog = TicketCommands(bot)
    
    # Add cog to bot
    await bot.add_cog(cog)
    
    try:
        # Register app commands to guild
        guild = discord.Object(id=Config.GUILD_ID)
        commands = [
            cog.setup_tickets,
            cog.ticket_stats,
            cog.ticket_search
        ]
        for cmd in commands:
            bot.tree.add_command(cmd, guild=guild)
        print("Registered ticket commands to guild")
    except Exception as e:
        print(f"Failed to register ticket commands: {e}")
