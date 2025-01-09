import discord
from discord.ext import commands
from discord.ext.commands import Cog
import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import aiosqlite
import os
import re
from collections import defaultdict, deque
from config import Config

logger = logging.getLogger('discord')

class AutoModCommands(Cog):
    """Cog for handling automated moderation"""
    
    def __init__(self, bot):
        self.bot = bot
        self.settings = {
            "banned_words": Config.BLACKLISTED_WORDS,
            "banned_links": [d for d in Config.ALLOWED_DOMAINS if d not in ['discord.com', 'discord.gg']],
            "spam_threshold": Config.AUTOMOD_SPAM_THRESHOLD,
            "spam_interval": Config.AUTOMOD_SPAM_INTERVAL,
            "raid_threshold": Config.AUTOMOD_RAID_THRESHOLD,
            "raid_interval": Config.AUTOMOD_RAID_INTERVAL,
            "action_type": Config.AUTOMOD_ACTION,
            "is_enabled": Config.AUTOMOD_ENABLED
        }
        self.user_messages = defaultdict(lambda: deque(maxlen=50))  # Track recent messages per user
        self.recent_joins = deque(maxlen=50)  # Track recent joins
        self.db_path = './bot_dashboard.db'
        asyncio.create_task(self.setup_database())

    async def setup_database(self):
        """Initialize the SQLite database"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Create guild entry if it doesn't exist
                await db.execute('''
                    INSERT OR IGNORE INTO guilds (discord_id, name)
                    VALUES (?, ?)
                ''', (str(Config.GUILD_ID), "ArabLife"))
                
                # Create guild settings if they don't exist
                await db.execute('''
                    INSERT OR IGNORE INTO guild_settings (guild_id, custom_settings)
                    SELECT id, '{"automod": ' || ? || '}'
                    FROM guilds WHERE discord_id = ?
                ''', (json.dumps(self.settings), str(Config.GUILD_ID)))
                
                # Create automod entry if it doesn't exist
                await db.execute('''
                    INSERT OR IGNORE INTO automod (
                        guild_id,
                        banned_words,
                        banned_links,
                        spam_threshold,
                        spam_interval,
                        raid_threshold,
                        raid_interval,
                        action_type,
                        is_enabled
                    )
                    SELECT id, ?, ?, ?, ?, ?, ?, ?, ?
                    FROM guilds WHERE discord_id = ?
                ''', (
                    json.dumps(self.settings['banned_words']),
                    json.dumps(self.settings['banned_links']),
                    self.settings['spam_threshold'],
                    self.settings['spam_interval'],
                    self.settings['raid_threshold'],
                    self.settings['raid_interval'],
                    self.settings['action_type'],
                    self.settings['is_enabled'],
                    str(Config.GUILD_ID)
                ))
                
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to setup database: {str(e)}")

    async def save_settings(self):
        """Save current settings to database"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Get guild's database ID
                async with db.execute(
                    'SELECT id FROM guilds WHERE discord_id = ?',
                    (str(Config.GUILD_ID),)
                ) as cursor:
                    guild_result = await cursor.fetchone()
                    if not guild_result:
                        return
                    db_guild_id = guild_result[0]
                
                # Update automod settings
                await db.execute('''
                    UPDATE automod SET
                        banned_words = ?,
                        banned_links = ?,
                        spam_threshold = ?,
                        spam_interval = ?,
                        raid_threshold = ?,
                        raid_interval = ?,
                        action_type = ?,
                        is_enabled = ?
                    WHERE guild_id = ?
                ''', (
                    json.dumps(self.settings['banned_words']),
                    json.dumps(self.settings['banned_links']),
                    self.settings['spam_threshold'],
                    self.settings['spam_interval'],
                    self.settings['raid_threshold'],
                    self.settings['raid_interval'],
                    self.settings['action_type'],
                    self.settings['is_enabled'],
                    db_guild_id
                ))
                
                # Update guild settings
                await db.execute('''
                    UPDATE guild_settings 
                    SET custom_settings = json_set(custom_settings, '$.automod', ?)
                    WHERE guild_id = ?
                ''', (json.dumps(self.settings), db_guild_id))
                
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to save settings: {str(e)}")

    async def log_action(self, guild_id: int, user_id: int, action: str, reason: str):
        """Log automod action to database"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Get guild's database ID
                async with db.execute(
                    'SELECT id FROM guilds WHERE discord_id = ?',
                    (str(guild_id),)
                ) as cursor:
                    guild_result = await cursor.fetchone()
                    if not guild_result:
                        return
                    db_guild_id = guild_result[0]
                
                await db.execute('''
                    INSERT INTO automod_logs (guild_id, user_id, action, reason, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                ''', (db_guild_id, user_id, action, reason, datetime.now().isoformat()))
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to log action: {str(e)}")

    async def take_action(self, member: discord.Member, reason: str):
        """Take action based on settings"""
        action = self.settings['action_type']
        
        try:
            if action == 'warn':
                await member.send(f"⚠️ Warning: {reason}")
            elif action == 'mute':
                duration = timedelta(hours=1)
                await member.timeout(duration, reason=reason)
            elif action == 'kick':
                await member.kick(reason=reason)
            elif action == 'ban':
                await member.ban(reason=reason, delete_message_days=1)
                
            # Log the action
            await self.log_action(member.guild.id, member.id, action, reason)
            
            if hasattr(Config, 'AUDIT_LOG_CHANNEL_ID'):
                channel = member.guild.get_channel(Config.AUDIT_LOG_CHANNEL_ID)
                if channel:
                    await channel.send(f"🛡️ AutoMod Action: {action.title()}\nUser: {member.mention}\nReason: {reason}")
                    
        except discord.Forbidden:
            logger.error(f"Failed to {action} user {member.name}: Missing permissions")
        except Exception as e:
            logger.error(f"Failed to {action} user {member.name}: {str(e)}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Handle message filtering and spam detection"""
        if not self.settings['is_enabled'] or message.author.bot or not message.guild:
            return
            
        try:
            # Store message for spam detection
            user_id = message.author.id
            now = datetime.now()
            self.user_messages[user_id].append((message.content, now))
            
            # Check for spam
            recent_messages = [msg for msg, time in self.user_messages[user_id]
                             if (now - time).total_seconds() <= self.settings['spam_interval']]
            
            if len(recent_messages) >= self.settings['spam_threshold']:
                await message.delete()
                await self.take_action(
                    message.author,
                    f"Spam detected: {len(recent_messages)} messages in {self.settings['spam_interval']} seconds"
                )
                return
                
            # Check banned words
            content_lower = message.content.lower()
            for word in self.settings['banned_words']:
                if word.lower() in content_lower:
                    await message.delete()
                    await self.take_action(message.author, f"Banned word detected: {word}")
                    return
                    
            # Check banned links
            urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message.content)
            for url in urls:
                domain = url.split('/')[2]
                if domain in self.settings['banned_links']:
                    await message.delete()
                    await self.take_action(message.author, f"Banned link detected: {domain}")
                    return
                    
        except Exception as e:
            logger.error(f"Failed to process message: {str(e)}")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Handle raid detection"""
        if not self.settings['is_enabled']:
            return
            
        try:
            now = datetime.now()
            self.recent_joins.append(now)
            
            # Check for raid
            recent_count = sum(1 for join_time in self.recent_joins
                             if (now - join_time).total_seconds() <= self.settings['raid_interval'])
            
            if recent_count >= self.settings['raid_threshold']:
                # Enable raid mode
                try:
                    # Set to highest verification level
                    await member.guild.edit(verification_level=discord.VerificationLevel.highest)
                    
                    if hasattr(Config, 'AUDIT_LOG_CHANNEL_ID'):
                        channel = member.guild.get_channel(Config.AUDIT_LOG_CHANNEL_ID)
                        if channel:
                            await channel.send(
                                f"🚨 **RAID DETECTED**\n"
                                f"{recent_count} joins in {self.settings['raid_interval']} seconds\n"
                                f"Verification level set to highest."
                            )
                    
                    # Log raid detection
                    await self.log_action(
                        member.guild.id,
                        0,  # No specific user
                        "raid_protection",
                        f"Raid detected: {recent_count} joins in {self.settings['raid_interval']} seconds"
                    )
                    
                    # Reset after 10 minutes
                    await asyncio.sleep(600)
                    await member.guild.edit(verification_level=discord.VerificationLevel.medium)
                    
                    if hasattr(Config, 'AUDIT_LOG_CHANNEL_ID'):
                        channel = member.guild.get_channel(Config.AUDIT_LOG_CHANNEL_ID)
                        if channel:
                            await channel.send("✅ Raid protection disabled. Verification level restored.")
                            
                except discord.Forbidden:
                    logger.error("Failed to enable raid protection: Missing permissions")
                except Exception as e:
                    logger.error(f"Failed to enable raid protection: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Failed to process member join: {str(e)}")

    @commands.hybrid_command()
    @commands.has_permissions(administrator=True)
    async def automod(self, ctx: commands.Context, setting: str, value: str):
        """Configure AutoMod settings (Admin only)"""
        try:
            setting = setting.lower()
            
            if setting == "enable":
                self.settings['is_enabled'] = value.lower() == "true"
                await ctx.send(f"AutoMod {'enabled' if self.settings['is_enabled'] else 'disabled'}")
                
            elif setting == "action":
                if value not in ["warn", "mute", "kick", "ban"]:
                    await ctx.send("Invalid action type. Use: warn, mute, kick, or ban")
                    return
                self.settings['action_type'] = value
                await ctx.send(f"AutoMod action set to: {value}")
                
            elif setting == "addword":
                if value not in self.settings['banned_words']:
                    self.settings['banned_words'].append(value)
                    await ctx.send(f"Added '{value}' to banned words")
                else:
                    await ctx.send("Word already banned")
                    
            elif setting == "removeword":
                if value in self.settings['banned_words']:
                    self.settings['banned_words'].remove(value)
                    await ctx.send(f"Removed '{value}' from banned words")
                else:
                    await ctx.send("Word not found in banned list")
                    
            elif setting == "addlink":
                if value not in self.settings['banned_links']:
                    self.settings['banned_links'].append(value)
                    await ctx.send(f"Added '{value}' to banned links")
                else:
                    await ctx.send("Link already banned")
                    
            elif setting == "removelink":
                if value in self.settings['banned_links']:
                    self.settings['banned_links'].remove(value)
                    await ctx.send(f"Removed '{value}' from banned links")
                else:
                    await ctx.send("Link not found in banned list")
                    
            else:
                await ctx.send("Invalid setting. Available settings: enable, action, addword, removeword, addlink, removelink")
                return
                
            await self.save_settings()
            
        except Exception as e:
            logger.error(f"Failed to update automod settings: {str(e)}")
            await ctx.send("An error occurred while updating settings.")

    @commands.hybrid_command()
    @commands.has_permissions(administrator=True)
    async def automodstatus(self, ctx: commands.Context):
        """Show current AutoMod settings (Admin only)"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Get guild's database ID
                async with db.execute(
                    'SELECT id FROM guilds WHERE discord_id = ?',
                    (str(ctx.guild.id),)
                ) as cursor:
                    guild_result = await cursor.fetchone()
                    if not guild_result:
                        await ctx.send("Guild not found in database!")
                        return
                    db_guild_id = guild_result[0]
                
                embed = discord.Embed(title="AutoMod Status", color=discord.Color.blue())
                
                embed.add_field(name="Status", value="Enabled" if self.settings['is_enabled'] else "Disabled", inline=True)
                embed.add_field(name="Action", value=self.settings['action_type'].title(), inline=True)
                
                embed.add_field(
                    name="Spam Protection",
                    value=f"{self.settings['spam_threshold']} messages in {self.settings['spam_interval']}s",
                    inline=False
                )
                
                embed.add_field(
                    name="Raid Protection",
                    value=f"{self.settings['raid_threshold']} joins in {self.settings['raid_interval']}s",
                    inline=False
                )
                
                banned_words = ", ".join(self.settings['banned_words']) or "None"
                embed.add_field(name="Banned Words", value=banned_words, inline=False)
                
                banned_links = ", ".join(self.settings['banned_links']) or "None"
                embed.add_field(name="Banned Links", value=banned_links, inline=False)
                
                # Get recent actions
                async with db.execute('''
                    SELECT action, reason, timestamp
                    FROM automod_logs
                    WHERE guild_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 5
                ''', (db_guild_id,)) as cursor:
                    recent_actions = await cursor.fetchall()
                    
                if recent_actions:
                    actions_text = "\n".join(
                        f"{action.title()}: {reason} ({timestamp.split('T')[0]})"
                        for action, reason, timestamp in recent_actions
                    )
                    embed.add_field(name="Recent Actions", value=actions_text, inline=False)
                
                await ctx.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Failed to show automod status: {str(e)}")
            await ctx.send("An error occurred while fetching automod status.")

async def setup(bot):
    await bot.add_cog(AutoModCommands(bot))
