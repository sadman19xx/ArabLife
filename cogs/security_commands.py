import discord
from discord.ext import commands
from discord.ext.commands import Cog
import logging
from config import Config
from collections import defaultdict, deque
from datetime import datetime, timedelta
import re
import asyncio

logger = logging.getLogger('discord')

class SecurityCommands(Cog):
    """Cog for security features like anti-raid, spam detection, etc."""
    
    def __init__(self, bot):
        self.bot = bot
        # Message tracking for spam detection
        self.user_messages = defaultdict(lambda: deque(maxlen=10))  # Last 10 messages per user
        self.user_message_times = defaultdict(lambda: deque(maxlen=5))  # Last 5 message timestamps per user
        # Join tracking for raid detection
        self.recent_joins = deque(maxlen=10)  # Track last 10 joins
        self.raid_mode = False
        # Link tracking
        self.allowed_domains = set(['discord.com', 'discord.gg'])  # Allowed domains
        # Mention tracking
        self.max_mentions = 5  # Maximum mentions per message
        # Cached warnings
        self.user_warnings = defaultdict(int)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Handle member joins and raid detection"""
        now = datetime.now()
        self.recent_joins.append(now)
        
        # Check for raid (10 joins within 30 seconds)
        if len(self.recent_joins) == 10:
            time_diff = (self.recent_joins[-1] - self.recent_joins[0]).seconds
            if time_diff < 30:
                await self.enable_raid_mode(member.guild)

        # Account age check
        account_age = now - member.created_at
        if account_age < timedelta(days=7):
            await self.log_security(member.guild, f"⚠️ New account joined: {member.mention} (Account age: {account_age.days} days)")

    async def enable_raid_mode(self, guild):
        """Enable raid protection mode"""
        if not self.raid_mode:
            self.raid_mode = True
            # Get verification level
            current_level = guild.verification_level
            
            try:
                # Set to highest verification
                await guild.edit(verification_level=discord.VerificationLevel.highest)
                await self.log_security(guild, "🚨 **RAID MODE ENABLED**\nVerification level set to highest.")
                
                # Wait 10 minutes then disable
                await asyncio.sleep(600)
                await guild.edit(verification_level=current_level)
                self.raid_mode = False
                await self.log_security(guild, "✅ Raid mode disabled. Verification level restored.")
                
            except discord.Forbidden:
                await self.log_security(guild, "❌ Failed to enable raid mode: Missing permissions")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle message scanning and spam detection"""
        if message.author.bot:
            return

        await self.check_spam(message)
        await self.check_content(message)

    async def check_spam(self, message):
        """Check for spam patterns"""
        user_id = message.author.id
        now = datetime.now()
        
        # Add message to tracking
        self.user_messages[user_id].append(message.content)
        self.user_message_times[user_id].append(now)
        
        # Check message similarity (spam)
        if len(self.user_messages[user_id]) == 10:
            if len(set(self.user_messages[user_id])) <= 2:  # If only 1-2 unique messages
                await self.warn_user(message, "spam detection")
                await message.channel.send(f"{message.author.mention} Stop spamming!")
        
        # Check message frequency
        if len(self.user_message_times[user_id]) == 5:
            time_diff = (self.user_message_times[user_id][-1] - self.user_message_times[user_id][0]).seconds
            if time_diff < 3:  # 5 messages in less than 3 seconds
                await self.warn_user(message, "message frequency")
                await message.channel.send(f"{message.author.mention} You're sending messages too quickly!")

    async def check_content(self, message):
        """Check message content for violations"""
        # Check mentions
        if len(message.mentions) > self.max_mentions:
            await message.delete()
            await self.warn_user(message, "mass mentions")
            await message.channel.send(f"{message.author.mention} Too many mentions!")
            return

        # Check links
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message.content)
        for url in urls:
            domain = url.split('/')[2]
            if domain not in self.allowed_domains:
                await message.delete()
                await self.warn_user(message, "unauthorized link")
                await message.channel.send(f"{message.author.mention} Unauthorized link detected!")
                return

        # Check for discord invites
        if 'discord.gg/' in message.content and not message.author.guild_permissions.create_instant_invite:
            await message.delete()
            await self.warn_user(message, "unauthorized invite")
            await message.channel.send(f"{message.author.mention} You're not allowed to post invite links!")
            return

    async def warn_user(self, message, reason):
        """Handle user warnings and punishments"""
        self.user_warnings[message.author.id] += 1
        warning_count = self.user_warnings[message.author.id]
        
        await self.log_security(message.guild, 
            f"⚠️ Warning issued to {message.author.mention}\n"
            f"Reason: {reason}\n"
            f"Warning count: {warning_count}"
        )
        
        # Handle repeated violations
        if warning_count >= 3:
            try:
                # Try to timeout user for 1 hour
                await message.author.timeout(timedelta(hours=1), reason=f"Multiple violations: {reason}")
                await self.log_security(message.guild, f"🔇 User {message.author.mention} has been timed out for 1 hour.")
            except discord.Forbidden:
                await self.log_security(message.guild, f"❌ Failed to timeout {message.author.mention}: Missing permissions")

    async def log_security(self, guild, message):
        """Log security events to the audit channel"""
        if hasattr(Config, 'AUDIT_LOG_CHANNEL_ID'):
            channel = guild.get_channel(Config.AUDIT_LOG_CHANNEL_ID)
            if channel:
                await channel.send(message)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def clearwarnings(self, ctx, member: discord.Member):
        """Clear warnings for a user"""
        if member.id in self.user_warnings:
            old_count = self.user_warnings[member.id]
            del self.user_warnings[member.id]
            await ctx.send(f"Cleared {old_count} warnings for {member.mention}")
            await self.log_security(ctx.guild, f"🗑️ Warnings cleared for {member.mention} by {ctx.author.mention}")
        else:
            await ctx.send(f"{member.mention} has no warnings.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def warnings(self, ctx, member: discord.Member):
        """Check warnings for a user"""
        count = self.user_warnings.get(member.id, 0)
        await ctx.send(f"{member.mention} has {count} warning(s).")

async def setup(bot):
    await bot.add_cog(SecurityCommands(bot))
