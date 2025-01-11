import discord
from discord.ext import commands
from discord import app_commands
from discord.ext.commands import Cog
import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Literal
import aiosqlite
import os
import re
from collections import defaultdict, deque
from config import Config
from utils.database import db

logger = logging.getLogger('discord')

class AutoModCommands(Cog):
    """Cog for handling automated moderation"""
    
    def __init__(self, bot):
        self.bot = bot
        self.user_messages = defaultdict(lambda: deque(maxlen=50))  # Track recent messages per user
        self.recent_joins = deque(maxlen=50)  # Track recent joins
        self.raid_mode = False
        self.similar_message_threshold = 0.85  # 85% similarity threshold for spam detection

    async def get_settings(self, guild_id: str) -> dict:
        """Get automod settings for a guild"""
        async with db.transaction() as cursor:
            await cursor.execute("""
                SELECT settings FROM automod_settings
                WHERE guild_id = ?
            """, (guild_id,))
            settings = await cursor.fetchone()
                
            if not settings:
                # Create default settings
                default_settings = {
                    "banned_words": Config.BLACKLISTED_WORDS,
                    "banned_links": [d for d in Config.ALLOWED_DOMAINS if d not in ['discord.com', 'discord.gg']],
                    "spam_threshold": Config.AUTOMOD_SPAM_THRESHOLD,
                    "spam_interval": Config.AUTOMOD_SPAM_INTERVAL,
                    "raid_threshold": Config.AUTOMOD_RAID_THRESHOLD,
                    "raid_interval": Config.AUTOMOD_RAID_INTERVAL,
                    "action_type": Config.AUTOMOD_ACTION,
                    "mute_duration": 3600,  # 1 hour default
                    "exempt_roles": [],
                    "exempt_channels": [],
                    "is_enabled": Config.AUTOMOD_ENABLED
                }
                
                await cursor.execute("""
                    INSERT INTO automod_settings (
                        guild_id, settings
                    ) VALUES (?, ?)
                """, (guild_id, json.dumps(default_settings)))
                
                return default_settings
                
            return json.loads(settings[0])

    async def update_settings(self, guild_id: str, settings: dict):
        """Update automod settings for a guild"""
        async with db.transaction() as cursor:
            await cursor.execute("""
                UPDATE automod_settings
                SET settings = ?, updated_at = CURRENT_TIMESTAMP
                WHERE guild_id = ?
            """, (json.dumps(settings), guild_id))

    async def log_action(self, guild_id: int, user_id: int, action: str, reason: str):
        """Log automod action to database"""
        try:
            async with db.transaction() as cursor:
                await cursor.execute('''
                    INSERT INTO automod_logs (guild_id, user_id, action, reason, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                ''', (str(guild_id), str(user_id), action, reason, datetime.now().isoformat()))
        except Exception as e:
            logger.error(f"Failed to log action: {str(e)}")

    async def take_action(self, member: discord.Member, reason: str, settings: dict):
        """Take action based on settings"""
        action = settings['action_type']
        
        try:
            if action == 'warn':
                await member.send(f"⚠️ Warning: {reason}")
            elif action == 'mute':
                duration = timedelta(seconds=settings['mute_duration'])
                await member.timeout(duration, reason=reason)
            elif action == 'kick':
                await member.kick(reason=reason)
            elif action == 'ban':
                await member.ban(reason=reason, delete_message_days=1)
                
            # Log the action
            await self.log_action(member.guild.id, member.id, action, reason)
            
            # Send to audit log channel
            if hasattr(Config, 'AUDIT_LOG_CHANNEL_ID'):
                channel = member.guild.get_channel(Config.AUDIT_LOG_CHANNEL_ID)
                if channel:
                    duration_text = f" for {settings['mute_duration']} seconds" if action == 'mute' else ""
                    await channel.send(
                        f"🛡️ AutoMod Action: {action.title()}{duration_text}\n"
                        f"User: {member.mention}\n"
                        f"Reason: {reason}"
                    )
                    
        except discord.Forbidden:
            logger.error(f"Failed to {action} user {member.name}: Missing permissions")
        except Exception as e:
            logger.error(f"Failed to {action} user {member.name}: {str(e)}")

    def is_exempt(self, message: discord.Message, settings: dict) -> bool:
        """Check if user/channel is exempt from automod"""
        # Check exempt roles
        for role in message.author.roles:
            if str(role.id) in settings['exempt_roles']:
                return True
                
        # Check exempt channels
        if str(message.channel.id) in settings['exempt_channels']:
            return True
            
        return False

    def message_similarity(self, msg1: str, msg2: str) -> float:
        """Calculate similarity ratio between two messages"""
        from difflib import SequenceMatcher
        return SequenceMatcher(None, msg1.lower(), msg2.lower()).ratio()

    def matches_wildcard(self, text: str, pattern: str) -> bool:
        """Check if text matches wildcard pattern"""
        import fnmatch
        return fnmatch.fnmatch(text.lower(), pattern.lower())

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Handle message filtering and spam detection"""
        if message.author.bot or not message.guild:
            return
            
        try:
            settings = await self.get_settings(str(message.guild.id))
            
            if not settings['is_enabled'] or self.is_exempt(message, settings):
                return
            
            # Store message for spam detection
            user_id = message.author.id
            now = datetime.now()
            self.user_messages[user_id].append((message.content, now))
            
            # Check for spam
            recent_messages = [
                msg for msg, time in self.user_messages[user_id]
                if (now - time).total_seconds() <= settings['spam_interval']
            ]
            
            if len(recent_messages) >= settings['spam_threshold']:
                # Check for message similarity
                if len(recent_messages) >= 2:
                    similar_count = 0
                    for i in range(len(recent_messages)-1):
                        if self.message_similarity(
                            recent_messages[i],
                            recent_messages[i+1]
                        ) > self.similar_message_threshold:
                            similar_count += 1
                            
                    if similar_count >= settings['spam_threshold'] - 1:
                        await message.delete()
                        await self.take_action(
                            message.author,
                            f"Spam detected: {len(recent_messages)} similar messages in {settings['spam_interval']} seconds",
                            settings
                        )
                        return
            
            # Check banned words with wildcards
            content_lower = message.content.lower()
            for word in settings['banned_words']:
                if self.matches_wildcard(content_lower, word):
                    await message.delete()
                    await self.take_action(
                        message.author,
                        f"Banned word/phrase detected: {word}",
                        settings
                    )
                    return
                    
            # Check banned links
            urls = re.findall(
                r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
                message.content
            )
            for url in urls:
                domain = url.split('/')[2]
                if any(self.matches_wildcard(domain, pattern) for pattern in settings['banned_links']):
                    await message.delete()
                    await self.take_action(
                        message.author,
                        f"Banned link detected: {domain}",
                        settings
                    )
                    return
                    
        except Exception as e:
            logger.error(f"Failed to process message: {str(e)}")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Handle raid detection"""
        try:
            settings = await self.get_settings(str(member.guild.id))
            
            if not settings['is_enabled']:
                return
                
            now = datetime.now()
            self.recent_joins.append(now)
            
            # Check for raid
            recent_count = sum(1 for join_time in self.recent_joins
                             if (now - join_time).total_seconds() <= settings['raid_interval'])
            
            if recent_count >= settings['raid_threshold']:
                if not self.raid_mode:  # Only trigger if not already in raid mode
                    self.raid_mode = True
                    try:
                        # Set to highest verification level
                        await member.guild.edit(verification_level=discord.VerificationLevel.highest)
                        
                        if hasattr(Config, 'AUDIT_LOG_CHANNEL_ID'):
                            channel = member.guild.get_channel(Config.AUDIT_LOG_CHANNEL_ID)
                            if channel:
                                await channel.send(
                                    f"🚨 **تم اكتشاف غارة!**\n"
                                    f"{recent_count} عضو انضموا خلال {settings['raid_interval']} ثانية\n"
                                    f"تم رفع مستوى التحقق إلى الأعلى."
                                )
                        
                        # Log raid detection
                        await self.log_action(
                            member.guild.id,
                            0,  # No specific user
                            "raid_protection",
                            f"تم اكتشاف غارة: {recent_count} عضو انضموا خلال {settings['raid_interval']} ثانية"
                        )
                        
                        # Reset after 10 minutes
                        await asyncio.sleep(600)
                        if self.raid_mode:  # Check if still in raid mode
                            self.raid_mode = False
                            await member.guild.edit(verification_level=discord.VerificationLevel.medium)
                            
                            if hasattr(Config, 'AUDIT_LOG_CHANNEL_ID'):
                                channel = member.guild.get_channel(Config.AUDIT_LOG_CHANNEL_ID)
                                if channel:
                                    await channel.send("✅ تم تعطيل حماية الغارات. تم استعادة مستوى التحقق.")
                                    
                    except discord.Forbidden:
                        logger.error("Failed to enable raid protection: Missing permissions")
                    except Exception as e:
                        logger.error(f"Failed to enable raid protection: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Failed to process member join: {str(e)}")

    @app_commands.command(
        name="automod_toggle",
        description="Enable or disable AutoMod"
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 30)  # 30 second cooldown
    async def automod_toggle(
        self,
        interaction: discord.Interaction,
        enabled: bool
    ):
        """Toggle AutoMod on/off"""
        try:
            settings = await self.get_settings(str(interaction.guild_id))
            settings['is_enabled'] = enabled
            await self.update_settings(str(interaction.guild_id), settings)
            
            await interaction.response.send_message(
                f"*تم {'تفعيل' if enabled else 'تعطيل'} نظام المراقبة التلقائية.*"
            )
        except Exception as e:
            logger.error(f"Failed to toggle automod: {str(e)}")
            await interaction.response.send_message(
                "*حدث خطأ أثناء تحديث الإعدادات.*",
                ephemeral=True
            )

    @app_commands.command(
        name="automod_action",
        description="Set the action to take when a rule is violated"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def set_action(
        self,
        interaction: discord.Interaction,
        action: Literal["warn", "mute", "kick", "ban"],
        mute_duration: Optional[int] = None
    ):
        """Set AutoMod action and mute duration"""
        try:
            settings = await self.get_settings(str(interaction.guild_id))
            settings['action_type'] = action
            
            if action == "mute" and mute_duration:
                settings['mute_duration'] = max(60, min(mute_duration, 2419200))  # 1 min to 28 days
                
            await self.update_settings(str(interaction.guild_id), settings)
            
            duration_text = f" لمدة {mute_duration} ثانية" if action == "mute" and mute_duration else ""
            await interaction.response.send_message(
                f"*تم تعيين إجراء المراقبة التلقائية إلى: {action}{duration_text}*"
            )
        except Exception as e:
            logger.error(f"Failed to set action: {str(e)}")
            await interaction.response.send_message(
                "*حدث خطأ أثناء تحديث الإعدادات.*",
                ephemeral=True
            )

    @app_commands.command(
        name="automod_exempt",
        description="Add/remove role or channel exemption from AutoMod"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def manage_exempt(
        self,
        interaction: discord.Interaction,
        action: Literal["add", "remove"],
        target: Union[discord.Role, discord.TextChannel]
    ):
        """Manage AutoMod exemptions"""
        try:
            settings = await self.get_settings(str(interaction.guild_id))
            
            if isinstance(target, discord.Role):
                exempt_list = settings['exempt_roles']
                target_type = "role"
            else:
                exempt_list = settings['exempt_channels']
                target_type = "channel"
                
            target_id = str(target.id)
            
            if action == "add":
                if target_id not in exempt_list:
                    exempt_list.append(target_id)
                    action_text = "إضافة"
                else:
                    await interaction.response.send_message(
                        f"*{target.name} معفى بالفعل.*",
                        ephemeral=True
                    )
                    return
            else:
                if target_id in exempt_list:
                    exempt_list.remove(target_id)
                    action_text = "إزالة"
                else:
                    await interaction.response.send_message(
                        f"*{target.name} غير معفى.*",
                        ephemeral=True
                    )
                    return
                    
            if isinstance(target, discord.Role):
                settings['exempt_roles'] = exempt_list
            else:
                settings['exempt_channels'] = exempt_list
                
            await self.update_settings(str(interaction.guild_id), settings)
            
            await interaction.response.send_message(
                f"*تم {action_text} {target.name} من قائمة الإعفاء.*"
            )
        except Exception as e:
            logger.error(f"Failed to manage exemptions: {str(e)}")
            await interaction.response.send_message(
                "*حدث خطأ أثناء تحديث الإعدادات.*",
                ephemeral=True
            )

    @app_commands.command(
        name="automod_word",
        description="Add/remove banned word or phrase (supports wildcards)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 5)  # 5 second cooldown
    async def manage_words(
        self,
        interaction: discord.Interaction,
        action: Literal["add", "remove"],
        word: str
    ):
        """Manage banned words"""
        try:
            settings = await self.get_settings(str(interaction.guild_id))
            
            if action == "add":
                if word not in settings['banned_words']:
                    settings['banned_words'].append(word)
                    action_text = "إضافة"
                else:
                    await interaction.response.send_message(
                        "*هذه الكلمة محظورة بالفعل.*",
                        ephemeral=True
                    )
                    return
            else:
                if word in settings['banned_words']:
                    settings['banned_words'].remove(word)
                    action_text = "إزالة"
                else:
                    await interaction.response.send_message(
                        "*هذه الكلمة غير موجودة في القائمة المحظورة.*",
                        ephemeral=True
                    )
                    return
                    
            await self.update_settings(str(interaction.guild_id), settings)
            
            await interaction.response.send_message(
                f"*تم {action_text} '{word}' من الكلمات المحظورة.*"
            )
        except Exception as e:
            logger.error(f"Failed to manage words: {str(e)}")
            await interaction.response.send_message(
                "*حدث خطأ أثناء تحديث الإعدادات.*",
                ephemeral=True
            )

    @app_commands.command(
        name="automod_link",
        description="Add/remove banned domain (supports wildcards)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def manage_links(
        self,
        interaction: discord.Interaction,
        action: Literal["add", "remove"],
        domain: str
    ):
        """Manage banned domains"""
        try:
            settings = await self.get_settings(str(interaction.guild_id))
            
            if action == "add":
                if domain not in settings['banned_links']:
                    settings['banned_links'].append(domain)
                    action_text = "إضافة"
                else:
                    await interaction.response.send_message(
                        "*هذا النطاق محظور بالفعل.*",
                        ephemeral=True
                    )
                    return
            else:
                if domain in settings['banned_links']:
                    settings['banned_links'].remove(domain)
                    action_text = "إزالة"
                else:
                    await interaction.response.send_message(
                        "*هذا النطاق غير موجود في القائمة المحظورة.*",
                        ephemeral=True
                    )
                    return
                    
            await self.update_settings(str(interaction.guild_id), settings)
            
            await interaction.response.send_message(
                f"*تم {action_text} '{domain}' من النطاقات المحظورة.*"
            )
        except Exception as e:
            logger.error(f"Failed to manage links: {str(e)}")
            await interaction.response.send_message(
                "*حدث خطأ أثناء تحديث الإعدادات.*",
                ephemeral=True
            )

    @app_commands.command(
        name="automod_status",
        description="Show current AutoMod settings"
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 10)  # 10 second cooldown
    async def automod_status(self, interaction: discord.Interaction):
        """Show current AutoMod settings"""
        try:
            settings = await self.get_settings(str(interaction.guild_id))
            
            embed = discord.Embed(
                title="حالة المراقبة التلقائية",
                color=discord.Color.blue()
            )
            
            # Basic settings
            embed.add_field(
                name="الحالة",
                value="مفعل" if settings['is_enabled'] else "معطل",
                inline=True
            )
            
            action_text = settings['action_type']
            if action_text == "mute":
                action_text += f" ({settings['mute_duration']} ثانية)"
            embed.add_field(name="الإجراء", value=action_text, inline=True)
            
            # Protection settings
            embed.add_field(
                name="الحماية من السبام",
                value=f"{settings['spam_threshold']} رسائل في {settings['spam_interval']} ثانية",
                inline=False
            )
            
            embed.add_field(
                name="الحماية من الغارات",
                value=f"{settings['raid_threshold']} انضمام في {settings['raid_interval']} ثانية",
                inline=False
            )
            
            # Exemptions
            exempt_roles = []
            for role_id in settings['exempt_roles']:
                role = interaction.guild.get_role(int(role_id))
                if role:
                    exempt_roles.append(role.mention)
            
            exempt_channels = []
            for channel_id in settings['exempt_channels']:
                channel = interaction.guild.get_channel(int(channel_id))
                if channel:
                    exempt_channels.append(channel.mention)
            
            if exempt_roles:
                embed.add_field(
                    name="الرتب المعفاة",
                    value=", ".join(exempt_roles),
                    inline=False
                )
            
            if exempt_channels:
                embed.add_field(
                    name="القنوات المعفاة",
                    value=", ".join(exempt_channels),
                    inline=False
                )
            
            # Filters
            banned_words = ", ".join(f"`{w}`" for w in settings['banned_words']) or "لا يوجد"
            embed.add_field(
                name="الكلمات المحظورة",
                value=banned_words,
                inline=False
            )
            
            banned_links = ", ".join(f"`{d}`" for d in settings['banned_links']) or "لا يوجد"
            embed.add_field(
                name="النطاقات المحظورة",
                value=banned_links,
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Failed to show automod status: {str(e)}")
            await interaction.response.send_message(
                "*حدث خطأ أثناء عرض الإعدادات.*",
                ephemeral=True
            )

    @app_commands.command(
        name="automod_spam",
        description="Configure spam detection settings"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def set_spam_settings(
        self,
        interaction: discord.Interaction,
        messages: Optional[int] = None,
        interval: Optional[int] = None,
        similarity: Optional[float] = None
    ):
        """Configure spam detection settings"""
        try:
            settings = await self.get_settings(str(interaction.guild_id))
            
            if messages is not None:
                settings['spam_threshold'] = max(2, min(messages, 10))
            if interval is not None:
                settings['spam_interval'] = max(5, min(interval, 30))
            if similarity is not None:
                self.similar_message_threshold = max(0.5, min(similarity, 1.0))
                
            await self.update_settings(str(interaction.guild_id), settings)
            
            await interaction.response.send_message(
                f"*تم تحديث إعدادات الحماية من السبام:*\n"
                f"• عدد الرسائل: {settings['spam_threshold']}\n"
                f"• الفترة الزمنية: {settings['spam_interval']} ثانية\n"
                f"• نسبة التشابه: {self.similar_message_threshold * 100}%"
            )
        except Exception as e:
            logger.error(f"Failed to set spam settings: {str(e)}")
            await interaction.response.send_message(
                "*حدث خطأ أثناء تحديث الإعدادات.*",
                ephemeral=True
            )

    @app_commands.command(
        name="automod_raid",
        description="Configure raid protection settings"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def set_raid_settings(
        self,
        interaction: discord.Interaction,
        joins: Optional[int] = None,
        interval: Optional[int] = None
    ):
        """Configure raid protection settings"""
        try:
            settings = await self.get_settings(str(interaction.guild_id))
            
            if joins is not None:
                settings['raid_threshold'] = max(3, min(joins, 20))
            if interval is not None:
                settings['raid_interval'] = max(10, min(interval, 60))
                
            await self.update_settings(str(interaction.guild_id), settings)
            
            await interaction.response.send_message(
                f"*تم تحديث إعدادات الحماية من الغارات:*\n"
                f"• عدد الانضمامات: {settings['raid_threshold']}\n"
                f"• الفترة الزمنية: {settings['raid_interval']} ثانية"
            )
        except Exception as e:
            logger.error(f"Failed to set raid settings: {str(e)}")
            await interaction.response.send_message(
                "*حدث خطأ أثناء تحديث الإعدادات.*",
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
            logger.error(f"AutoMod command error: {str(error)}")
            await interaction.response.send_message(
                "*حدث خطأ غير متوقع.*",
                ephemeral=True
            )

async def setup(bot):
    """Setup function for loading the cog"""
    # Create cog instance
    cog = AutoModCommands(bot)
    
    # Add cog to bot
    await bot.add_cog(cog)
    
    try:
        # Register app commands to guild
        guild = discord.Object(id=Config.GUILD_ID)
        commands = [
            cog.automod_toggle,
            cog.set_action,
            cog.manage_exempt,
            cog.manage_words,
            cog.manage_links,
            cog.automod_status,
            cog.set_spam_settings,
            cog.set_raid_settings
        ]
        for cmd in commands:
            bot.tree.add_command(cmd, guild=guild)
        print("Registered automod commands to guild")
    except Exception as e:
        print(f"Failed to register automod commands: {e}")
