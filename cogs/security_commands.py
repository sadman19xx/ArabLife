import discord
from discord.ext import commands
from discord import app_commands
from discord.ext.commands import Cog
import logging
import asyncio
import re
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Optional, List, Union
from config import Config
from utils.database import db
from utils.logger import LoggerMixin

class SecurityCommands(Cog, LoggerMixin):
    """Cog for security features like anti-raid, spam detection, etc."""
    
    def __init__(self, bot):
        self.bot = bot
        # Message tracking for spam detection
        self.user_messages = defaultdict(lambda: deque(maxlen=10))  # Last 10 messages per user
        self.user_message_times = defaultdict(lambda: deque(maxlen=5))  # Last 5 message timestamps per user
        # Join tracking for raid detection
        self.recent_joins = defaultdict(lambda: deque(maxlen=10))  # Track last 10 joins per guild
        self.raid_mode = defaultdict(bool)  # Raid mode status per guild
        # Cached settings
        self.guild_settings = {}
        # Task to clean old data
        self.cleanup_task = bot.loop.create_task(self.cleanup_old_data())

    async def cog_unload(self):
        """Cleanup when cog is unloaded"""
        self.cleanup_task.cancel()

    async def cleanup_old_data(self):
        """Periodically clean up old data"""
        while True:
            try:
                # Clean up message tracking older than 1 hour
                cutoff = datetime.now() - timedelta(hours=1)
                for user_times in self.user_message_times.values():
                    while user_times and user_times[0] < cutoff:
                        user_times.popleft()
                
                # Clean up join tracking older than 1 hour
                for guild_joins in self.recent_joins.values():
                    while guild_joins and guild_joins[0] < cutoff:
                        guild_joins.popleft()
                
                await asyncio.sleep(3600)  # Run every hour
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.log.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying

    async def get_guild_settings(self, guild_id: str) -> dict:
        """Get security settings for a guild"""
        if guild_id in self.guild_settings:
            return self.guild_settings[guild_id]
            
        async with db.transaction() as cursor:
            await cursor.execute("""
                SELECT settings FROM security_settings
                WHERE guild_id = ?
            """, (guild_id,))
            result = await cursor.fetchone()
            
            if not result:
                # Create default settings
                settings = {
                    "raid_protection": True,
                    "spam_protection": True,
                    "min_account_age": 7,  # days
                    "max_mentions": 5,
                    "allowed_domains": ["discord.com", "discord.gg"],
                    "warning_threshold": 3,
                    "warning_action": "timeout",  # timeout, kick, ban
                    "warning_duration": 3600,  # 1 hour
                    "exempt_roles": []
                }
                
                await cursor.execute("""
                    INSERT INTO security_settings (guild_id, settings)
                    VALUES (?, ?)
                """, (guild_id, str(settings)))
                
            else:
                settings = eval(result[0])  # Convert string to dict
                
        self.guild_settings[guild_id] = settings
        return settings

    def is_exempt(self, member: discord.Member, settings: dict) -> bool:
        """Check if member is exempt from security checks"""
        return any(role.id in settings['exempt_roles'] for role in member.roles)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Handle member joins and raid detection"""
        settings = await self.get_guild_settings(str(member.guild.id))
        if not settings['raid_protection']:
            return
            
        now = datetime.now(member.created_at.tzinfo)  # Use same timezone as member.created_at
        guild_joins = self.recent_joins[member.guild.id]
        guild_joins.append(now)
        
        # Check for raid (10 joins within 30 seconds)
        if len(guild_joins) == 10:
            time_diff = (guild_joins[-1] - guild_joins[0]).seconds
            if time_diff < 30:
                await self.enable_raid_mode(member.guild)

        # Account age check
        account_age = now - member.created_at  # Now both are timezone-aware
        if account_age < timedelta(days=settings['min_account_age']):
            await self.log_security(
                member.guild,
                f"⚠️ New account joined: {member.mention}\n"
                f"Account age: {account_age.days} days\n"
                f"Created: {member.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )

    async def enable_raid_mode(self, guild: discord.Guild):
        """Enable raid protection mode"""
        if not self.raid_mode[guild.id]:
            self.raid_mode[guild.id] = True
            current_level = guild.verification_level
            
            try:
                # Set to highest verification
                await guild.edit(verification_level=discord.VerificationLevel.highest)
                await self.log_security(
                    guild,
                    "🚨 **RAID MODE ENABLED**\n"
                    "• Verification level set to highest\n"
                    "• New members must wait 10 minutes to chat\n"
                    "• Phone verification required"
                )
                
                # Wait 10 minutes then disable
                await asyncio.sleep(600)
                if self.raid_mode[guild.id]:  # Check if still in raid mode
                    await guild.edit(verification_level=current_level)
                    self.raid_mode[guild.id] = False
                    await self.log_security(guild, "✅ Raid mode disabled. Verification level restored.")
                
            except discord.Forbidden:
                await self.log_security(guild, "❌ Failed to enable raid mode: Missing permissions")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Handle message scanning and spam detection"""
        if message.author.bot or not message.guild:
            return
            
        settings = await self.get_guild_settings(str(message.guild.id))
        if self.is_exempt(message.author, settings):
            return
            
        if settings['spam_protection']:
            await self.check_spam(message)
        await self.check_content(message, settings)

    async def check_spam(self, message: discord.Message):
        """Check for spam patterns"""
        user_id = message.author.id
        now = datetime.now()
        
        # Add message to tracking
        self.user_messages[user_id].append(message.content)
        self.user_message_times[user_id].append(now)
        
        # Check message similarity (spam)
        if len(self.user_messages[user_id]) == 10:
            if len(set(self.user_messages[user_id])) <= 2:  # If only 1-2 unique messages
                await self.warn_user(message.author, message.guild, "spam detection", message.author.id)
                await message.channel.send(
                    f"{message.author.mention} Stop spamming!",
                    delete_after=10
                )
        
        # Check message frequency
        if len(self.user_message_times[user_id]) == 5:
            time_diff = (self.user_message_times[user_id][-1] - self.user_message_times[user_id][0]).seconds
            if time_diff < 3:  # 5 messages in less than 3 seconds
                await self.warn_user(message.author, message.guild, "message frequency", message.author.id)
                await message.channel.send(
                    f"{message.author.mention} You're sending messages too quickly!",
                    delete_after=10
                )

    async def check_content(self, message: discord.Message, settings: dict):
        """Check message content for violations"""
        # Check mentions
        if len(message.mentions) > settings['max_mentions']:
            await message.delete()
            await self.warn_user(message.author, message.guild, "mass mentions", message.author.id)
            await message.channel.send(
                f"{message.author.mention} Too many mentions!",
                delete_after=10
            )
            return

        # Check blacklisted words
        async with db.transaction() as cursor:
            await cursor.execute("""
                SELECT word FROM blacklisted_words
                WHERE guild_id = ?
            """, (str(message.guild.id),))
            blacklisted = await cursor.fetchall()
            
        content_lower = message.content.lower()
        for (word,) in blacklisted:
            if word.lower() in content_lower:
                await message.delete()
                await self.warn_user(
                    message.author,
                    message.guild,
                    f"blacklisted word: {word}",
                    message.author.id
                )
                await message.channel.send(
                    f"{message.author.mention} That word is not allowed!",
                    delete_after=10
                )
                return

        # Check links
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message.content)
        for url in urls:
            domain = url.split('/')[2]
            if domain not in settings['allowed_domains']:
                await message.delete()
                await self.warn_user(message.author, message.guild, "unauthorized link", message.author.id)
                await message.channel.send(
                    f"{message.author.mention} Unauthorized link detected!",
                    delete_after=10
                )
                return

        # Check for discord invites
        if 'discord.gg/' in message.content and not message.author.guild_permissions.create_instant_invite:
            await message.delete()
            await self.warn_user(message.author, message.guild, "unauthorized invite", message.author.id)
            await message.channel.send(
                f"{message.author.mention} You're not allowed to post invite links!",
                delete_after=10
            )
            return

    async def warn_user(self, member: discord.Member, guild: discord.Guild, reason: str, moderator_id: int):
        """Handle user warnings and punishments"""
        settings = await self.get_guild_settings(str(guild.id))
        
        async with db.transaction() as cursor:
            # Clean expired warnings
            await cursor.execute("""
                UPDATE warnings 
                SET active = 0
                WHERE guild_id = ? 
                AND user_id = ?
                AND expires_at < CURRENT_TIMESTAMP
            """, (str(guild.id), str(member.id)))

            # Add new warning
            await cursor.execute("""
                INSERT INTO warnings (
                    guild_id, user_id, moderator_id, reason, 
                    created_at, expires_at, active
                )
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, 
                    datetime('now', '+' || ? || ' days'), 1)
            """, (
                str(guild.id), str(member.id), str(moderator_id),
                reason, settings['warning_expire_days']
            ))
            
            # Get warning count
            await cursor.execute("""
                SELECT COUNT(*) FROM warnings
                WHERE guild_id = ? AND user_id = ?
                AND active = 1
            """, (str(guild.id), str(member.id)))
            warning_count = (await cursor.fetchone())[0]
        
        await self.log_security(
            guild,
            f"⚠️ Warning issued to {member.mention}\n"
            f"Reason: {reason}\n"
            f"Warning count: {warning_count}"
        )
        
        # Handle repeated violations
        if warning_count >= settings['warning_threshold']:
            action = settings['warning_action']
            duration = settings['warning_duration']
            
            try:
                if action == 'timeout':
                    await member.timeout(
                        timedelta(seconds=duration),
                        reason=f"Multiple violations: {reason}"
                    )
                    action_text = f"timed out for {duration} seconds"
                elif action == 'kick':
                    await member.kick(reason=f"Multiple violations: {reason}")
                    action_text = "kicked"
                elif action == 'ban':
                    await member.ban(
                        reason=f"Multiple violations: {reason}",
                        delete_message_days=1
                    )
                    action_text = "banned"
                    
                await self.log_security(
                    guild,
                    f"🔨 User {member.mention} has been {action_text}\n"
                    f"Reason: Multiple violations ({warning_count} warnings)"
                )
            except discord.Forbidden:
                await self.log_security(
                    guild,
                    f"❌ Failed to {action} {member.mention}: Missing permissions"
                )

    async def log_security(self, guild: discord.Guild, message: str):
        """Log security events to the audit channel"""
        if hasattr(Config, 'AUDIT_LOG_CHANNEL_ID'):
            channel = guild.get_channel(Config.AUDIT_LOG_CHANNEL_ID)
            if channel:
                await channel.send(message)

    @app_commands.command(
        name="clearwarnings",
        description="Clear warnings for a user"
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 30)  # 30 second cooldown
    async def clear_warnings(
        self,
        interaction: discord.Interaction,
        member: discord.Member
    ):
        """Clear warnings for a user"""
        async with db.transaction() as cursor:
            await cursor.execute("""
                DELETE FROM warnings
                WHERE guild_id = ? AND user_id = ?
                RETURNING COUNT(*)
            """, (str(interaction.guild_id), str(member.id)))
            count = (await cursor.fetchone())[0]
            
        await interaction.response.send_message(
            f"Cleared {count} warnings for {member.mention}"
        )
        await self.log_security(
            interaction.guild,
            f"🗑️ Warnings cleared for {member.mention} by {interaction.user.mention}"
        )

    @app_commands.command(
        name="warnings",
        description="Check warnings for a user"
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 10)  # 10 second cooldown
    async def warnings(
        self,
        interaction: discord.Interaction,
        member: discord.Member
    ):
        """Check warnings for a user"""
        async with db.transaction() as cursor:
            await cursor.execute("""
                SELECT reason, timestamp FROM warnings
                WHERE guild_id = ? AND user_id = ?
                ORDER BY timestamp DESC
                LIMIT 10
            """, (str(interaction.guild_id), str(member.id)))
            warnings = await cursor.fetchall()
            
            await cursor.execute("""
                SELECT COUNT(*) FROM warnings
                WHERE guild_id = ? AND user_id = ?
            """, (str(interaction.guild_id), str(member.id)))
            total_count = (await cursor.fetchone())[0]
        
        if not warnings:
            await interaction.response.send_message(
                f"{member.mention} has no warnings."
            )
            return
            
        embed = discord.Embed(
            title=f"Warnings for {member.display_name}",
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        for reason, timestamp in warnings:
            embed.add_field(
                name=timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                value=reason,
                inline=False
            )
            
        if total_count > 10:
            embed.set_footer(text=f"Showing 10 most recent warnings. Total: {total_count}")
            
        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="raidmode",
        description="Manually toggle raid mode"
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 60)  # 60 second cooldown
    async def toggle_raid_mode(
        self,
        interaction: discord.Interaction,
        enable: bool
    ):
        """Manually toggle raid mode"""
        if enable == self.raid_mode.get(interaction.guild_id, False):
            status = "enabled" if enable else "disabled"
            await interaction.response.send_message(
                f"Raid mode is already {status}.",
                ephemeral=True
            )
            return
            
        if enable:
            self.raid_mode[interaction.guild_id] = True
            current_level = interaction.guild.verification_level
            
            try:
                await interaction.guild.edit(
                    verification_level=discord.VerificationLevel.highest
                )
                await interaction.response.send_message(
                    "🚨 Raid mode enabled. Verification level set to highest."
                )
                await self.log_security(
                    interaction.guild,
                    f"🚨 Raid mode manually enabled by {interaction.user.mention}"
                )
            except discord.Forbidden:
                await interaction.response.send_message(
                    "❌ Failed to enable raid mode: Missing permissions",
                    ephemeral=True
                )
        else:
            self.raid_mode[interaction.guild_id] = False
            try:
                await interaction.guild.edit(
                    verification_level=discord.VerificationLevel.medium
                )
                await interaction.response.send_message(
                    "✅ Raid mode disabled. Verification level set to medium."
                )
                await self.log_security(
                    interaction.guild,
                    f"✅ Raid mode manually disabled by {interaction.user.mention}"
                )
            except discord.Forbidden:
                await interaction.response.send_message(
                    "❌ Failed to disable raid mode: Missing permissions",
                    ephemeral=True
                )

    @app_commands.command(
        name="blacklist",
        description="Add or remove a word from the blacklist"
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 5)  # 5 second cooldown
    async def manage_blacklist(
        self,
        interaction: discord.Interaction,
        action: str,
        word: str
    ):
        """Manage blacklisted words"""
        if action not in ['add', 'remove']:
            await interaction.response.send_message(
                "Invalid action. Use 'add' or 'remove'.",
                ephemeral=True
            )
            return
            
        async with db.transaction() as cursor:
            if action == 'add':
                try:
                    await cursor.execute("""
                        INSERT INTO blacklisted_words (guild_id, word, added_by)
                        VALUES (?, ?, ?)
                    """, (str(interaction.guild_id), word.lower(), str(interaction.user.id)))
                    await interaction.response.send_message(
                        f"Added '{word}' to blacklist.",
                        ephemeral=True
                    )
                except aiosqlite.IntegrityError:
                    await interaction.response.send_message(
                        f"'{word}' is already blacklisted.",
                        ephemeral=True
                    )
            else:
                await cursor.execute("""
                    DELETE FROM blacklisted_words
                    WHERE guild_id = ? AND word = ?
                """, (str(interaction.guild_id), word.lower()))
                if cursor.rowcount > 0:
                    await interaction.response.send_message(
                        f"Removed '{word}' from blacklist.",
                        ephemeral=True
                    )
                else:
                    await interaction.response.send_message(
                        f"'{word}' is not in the blacklist.",
                        ephemeral=True
                    )

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Error handler for application commands"""
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"*الرجاء الانتظار {error.retry_after:.1f} ثواني.*",
                ephemeral=True
            )
        elif isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "*لا تملك الصلاحية لأستخدام هذه الامر.*",
                ephemeral=True
            )
        else:
            self.log.error(f"Security command error: {error}")
            await interaction.response.send_message(
                "*حدث خطأ غير متوقع.*",
                ephemeral=True
            )

async def setup(bot):
    """Setup function for loading the cog"""
    # Create cog instance
    cog = SecurityCommands(bot)
    
    # Add cog to bot
    await bot.add_cog(cog)
    
    try:
        # Register app commands to guild
        guild = discord.Object(id=Config.GUILD_ID)
        commands = [
            cog.clear_warnings,
            cog.warnings,
            cog.toggle_raid_mode
        ]
        for cmd in commands:
            bot.tree.add_command(cmd, guild=guild)
        print("Registered security commands to guild")
    except Exception as e:
        print(f"Failed to register security commands: {e}")
