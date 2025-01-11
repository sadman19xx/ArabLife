import discord
from discord.ext import commands
from discord import app_commands
from discord.ext.commands import Cog
import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Union
import aiosqlite
import os
from config import Config
from utils.database import db

logger = logging.getLogger('discord')

class LevelingCommands(Cog):
    """Cog for handling user leveling and XP system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.user_cooldowns: Dict[int, datetime] = {}

    async def get_settings(self, guild_id: str) -> dict:
        """Get leveling settings for a guild"""
        async with aiosqlite.connect(db.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("""
                SELECT * FROM leveling_settings
                WHERE guild_id = ?
            """, (guild_id,)) as cursor:
                settings = await cursor.fetchone()
                
            if not settings:
                # Create default settings
                await conn.execute("""
                    INSERT INTO leveling_settings (
                        guild_id, xp_per_message, xp_cooldown,
                        level_up_channel_id, level_up_message,
                        role_rewards, channel_multipliers, role_multipliers
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    guild_id,
                    Config.XP_PER_MESSAGE,
                    Config.XP_COOLDOWN,
                    Config.LEVEL_UP_CHANNEL_ID,
                    Config.LEVEL_UP_MESSAGE,
                    "{}",  # role_rewards
                    "{}",  # channel_multipliers
                    "{}"   # role_multipliers
                ))
                await conn.commit()
                
                # Get newly created settings
                async with conn.execute("""
                    SELECT * FROM leveling_settings
                    WHERE guild_id = ?
                """, (guild_id,)) as cursor:
                    settings = await cursor.fetchone()
                    
            return dict(settings)

    async def calculate_xp_gain(self, message: discord.Message, base_xp: int) -> int:
        """Calculate XP gain with multipliers"""
        settings = await self.get_settings(str(message.guild.id))
        multiplier = 1.0
        
        # Channel multiplier
        channel_multipliers = json.loads(settings['channel_multipliers'])
        if str(message.channel.id) in channel_multipliers:
            multiplier *= float(channel_multipliers[str(message.channel.id)])
            
        # Role multipliers (highest role multiplier applies)
        role_multipliers = json.loads(settings['role_multipliers'])
        max_role_multiplier = 1.0
        for role in message.author.roles:
            if str(role.id) in role_multipliers:
                role_mult = float(role_multipliers[str(role.id)])
                max_role_multiplier = max(max_role_multiplier, role_mult)
        
        multiplier *= max_role_multiplier
        
        return int(base_xp * multiplier)

    async def handle_level_up(self, member: discord.Member, new_level: int):
        """Handle level up event including role rewards"""
        settings = await self.get_settings(str(member.guild.id))
        
        try:
            # Send level up message
            if settings['level_up_channel_id']:
                channel = self.bot.get_channel(int(settings['level_up_channel_id']))
                if channel:
                    message = settings['level_up_message'].format(
                        user=member.mention,
                        level=new_level
                    )
                    await channel.send(message)

            # Handle role rewards
            role_rewards = json.loads(settings['role_rewards'])
            for level_str, role_id in role_rewards.items():
                if int(level_str) == new_level:
                    role = member.guild.get_role(int(role_id))
                    if role:
                        await member.add_roles(role)
                        logger.info(f"Added role {role.name} to {member.name} for reaching level {new_level}")
                        
        except Exception as e:
            logger.error(f"Failed to handle level up: {str(e)}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Handle XP gain from messages"""
        if message.author.bot or not message.guild:
            return
            
        try:
            settings = await self.get_settings(str(message.guild.id))
            
            # Check if leveling is enabled
            if not settings['leveling_enabled']:
                return
                
            # Check cooldown
            user_id = message.author.id
            now = datetime.now()
            if user_id in self.user_cooldowns:
                time_diff = (now - self.user_cooldowns[user_id]).total_seconds()
                if time_diff < settings['xp_cooldown']:
                    return
                    
            self.user_cooldowns[user_id] = now
            
            # Calculate XP with multipliers
            xp_amount = await self.calculate_xp_gain(
                message,
                settings['xp_per_message']
            )
            
            # Add XP using database handler
            new_level = await db.add_xp(
                str(message.guild.id),
                str(message.author.id),
                xp_amount
            )
            
            if new_level:
                await self.handle_level_up(message.author, new_level)
                
        except Exception as e:
            logger.error(f"Failed to process message XP: {str(e)}")

    @app_commands.command(
        name="rank",
        description="Check your or another user's rank"
    )
    async def rank(
        self,
        interaction: discord.Interaction,
        member: discord.Member = None
    ):
        """Check your or another user's rank"""
        try:
            target = member or interaction.user
            
            async with aiosqlite.connect(db.db_path) as conn:
                conn.row_factory = aiosqlite.Row
                
                # Get user's XP and level
                async with conn.execute("""
                    SELECT xp, level FROM user_levels
                    WHERE guild_id = ? AND user_id = ?
                """, (str(interaction.guild_id), str(target.id))) as cursor:
                    result = await cursor.fetchone()
                
                if not result:
                    await interaction.response.send_message(
                        f"{target.mention} لم يكتسب أي نقاط خبرة بعد!",
                        ephemeral=True
                    )
                    return
                
                xp, level = result['xp'], result['level']
                
                # Get user's rank
                async with conn.execute("""
                    SELECT COUNT(*) as rank FROM user_levels 
                    WHERE guild_id = ? AND xp > (
                        SELECT xp FROM user_levels 
                        WHERE guild_id = ? AND user_id = ?
                    )
                """, (str(interaction.guild_id), str(interaction.guild_id), str(target.id))) as cursor:
                    rank = (await cursor.fetchone())['rank'] + 1
                
                # Calculate progress
                next_level_xp = db.calculate_level(xp + 1) * 100  # Simplified calculation
                current_level_xp = xp - (level * 100)  # Simplified calculation
                progress = (current_level_xp / next_level_xp) * 100 if next_level_xp > 0 else 0
                
                # Get role multipliers
                settings = await self.get_settings(str(interaction.guild_id))
                role_multipliers = json.loads(settings['role_multipliers'])
                active_multiplier = 1.0
                for role in target.roles:
                    if str(role.id) in role_multipliers:
                        active_multiplier = max(
                            active_multiplier,
                            float(role_multipliers[str(role.id)])
                        )
                
                embed = discord.Embed(
                    title="معلومات المستوى",
                    color=discord.Color.blue()
                )
                embed.set_author(
                    name=target.display_name,
                    icon_url=target.display_avatar.url
                )
                embed.add_field(name="الترتيب", value=f"#{rank}", inline=True)
                embed.add_field(name="المستوى", value=str(level), inline=True)
                embed.add_field(name="نقاط الخبرة", value=f"{xp} XP", inline=True)
                
                # Add multiplier info if active
                if active_multiplier > 1.0:
                    embed.add_field(
                        name="مضاعف نقاط الخبرة",
                        value=f"x{active_multiplier}",
                        inline=True
                    )
                
                # Create progress bar
                progress_bar = "█" * int(progress / 10) + "░" * (10 - int(progress / 10))
                embed.add_field(
                    name="التقدم للمستوى التالي",
                    value=f"`{progress_bar}` {progress:.1f}%",
                    inline=False
                )
                
                await interaction.response.send_message(embed=embed)
                
        except Exception as e:
            logger.error(f"Failed to get rank: {str(e)}")
            await interaction.response.send_message(
                "*حدث خطأ أثناء جلب معلومات المستوى.*",
                ephemeral=True
            )

    @app_commands.command(
        name="leaderboard",
        description="Show the server's XP leaderboard"
    )
    async def leaderboard(self, interaction: discord.Interaction):
        """Show the server's XP leaderboard"""
        try:
            async with aiosqlite.connect(db.db_path) as conn:
                conn.row_factory = aiosqlite.Row
                
                async with conn.execute("""
                    SELECT user_id, xp, level 
                    FROM user_levels 
                    WHERE guild_id = ?
                    ORDER BY xp DESC 
                    LIMIT 10
                """, (str(interaction.guild_id),)) as cursor:
                    results = await cursor.fetchall()
                
                if not results:
                    await interaction.response.send_message(
                        "*لم يكتسب أحد أي نقاط خبرة بعد!*",
                        ephemeral=True
                    )
                    return
                
                embed = discord.Embed(
                    title="🏆 قائمة المتصدرين",
                    color=discord.Color.gold()
                )
                
                medals = ["🥇", "🥈", "🥉"]
                for i, row in enumerate(results, 1):
                    member = interaction.guild.get_member(int(row['user_id']))
                    name = member.display_name if member else f"User {row['user_id']}"
                    
                    medal = medals[i-1] if i <= 3 else "👤"
                    embed.add_field(
                        name=f"{medal} #{i} {name}",
                        value=f"المستوى {row['level']} | {row['xp']} XP",
                        inline=False
                    )
                
                await interaction.response.send_message(embed=embed)
                
        except Exception as e:
            logger.error(f"Failed to get leaderboard: {str(e)}")
            await interaction.response.send_message(
                "*حدث خطأ أثناء جلب قائمة المتصدرين.*",
                ephemeral=True
            )

    @app_commands.command(
        name="setxp",
        description="Set a user's XP (Admin only)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setxp(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        xp: int
    ):
        """Set a user's XP (Admin only)"""
        try:
            if xp < 0:
                await interaction.response.send_message(
                    "*لا يمكن أن تكون نقاط الخبرة سالبة!*",
                    ephemeral=True
                )
                return
            
            new_level = db.calculate_level(xp)
            
            async with aiosqlite.connect(db.db_path) as conn:
                await conn.execute("""
                    INSERT OR REPLACE INTO user_levels (guild_id, user_id, xp, level)
                    VALUES (?, ?, ?, ?)
                """, (str(interaction.guild_id), str(member.id), xp, new_level))
                await conn.commit()
            
            await interaction.response.send_message(
                f"*تم تعيين نقاط خبرة {member.mention} إلى {xp} (المستوى {new_level})*"
            )
            
        except Exception as e:
            logger.error(f"Failed to set XP: {str(e)}")
            await interaction.response.send_message(
                "*حدث خطأ أثناء تعيين نقاط الخبرة.*",
                ephemeral=True
            )

    @app_commands.command(
        name="setmultiplier",
        description="Set XP multiplier for a role or channel"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def set_multiplier(
        self,
        interaction: discord.Interaction,
        target: Union[discord.Role, discord.TextChannel],
        multiplier: float
    ):
        """Set XP multiplier for a role or channel"""
        try:
            if multiplier <= 0:
                await interaction.response.send_message(
                    "*يجب أن يكون المضاعف أكبر من 0.*",
                    ephemeral=True
                )
                return
                
            settings = await self.get_settings(str(interaction.guild_id))
            
            if isinstance(target, discord.Role):
                # Update role multiplier
                role_multipliers = json.loads(settings['role_multipliers'])
                role_multipliers[str(target.id)] = multiplier
                
                async with aiosqlite.connect(db.db_path) as conn:
                    await conn.execute("""
                        UPDATE leveling_settings
                        SET role_multipliers = ?
                        WHERE guild_id = ?
                    """, (json.dumps(role_multipliers), str(interaction.guild_id)))
                    await conn.commit()
                    
                await interaction.response.send_message(
                    f"*تم تعيين مضاعف نقاط الخبرة للرتبة {target.mention} إلى {multiplier}x*"
                )
            else:
                # Update channel multiplier
                channel_multipliers = json.loads(settings['channel_multipliers'])
                channel_multipliers[str(target.id)] = multiplier
                
                async with aiosqlite.connect(db.db_path) as conn:
                    await conn.execute("""
                        UPDATE leveling_settings
                        SET channel_multipliers = ?
                        WHERE guild_id = ?
                    """, (json.dumps(channel_multipliers), str(interaction.guild_id)))
                    await conn.commit()
                    
                await interaction.response.send_message(
                    f"*تم تعيين مضاعف نقاط الخبرة للقناة {target.mention} إلى {multiplier}x*"
                )
                
        except Exception as e:
            logger.error(f"Failed to set multiplier: {str(e)}")
            await interaction.response.send_message(
                "*حدث خطأ أثناء تعيين المضاعف.*",
                ephemeral=True
            )

    @app_commands.command(
        name="removemultiplier",
        description="Remove XP multiplier from a role or channel"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_multiplier(
        self,
        interaction: discord.Interaction,
        target: Union[discord.Role, discord.TextChannel]
    ):
        """Remove XP multiplier from a role or channel"""
        try:
            settings = await self.get_settings(str(interaction.guild_id))
            
            if isinstance(target, discord.Role):
                # Remove role multiplier
                role_multipliers = json.loads(settings['role_multipliers'])
                if str(target.id) in role_multipliers:
                    del role_multipliers[str(target.id)]
                    
                    async with aiosqlite.connect(db.db_path) as conn:
                        await conn.execute("""
                            UPDATE leveling_settings
                            SET role_multipliers = ?
                            WHERE guild_id = ?
                        """, (json.dumps(role_multipliers), str(interaction.guild_id)))
                        await conn.commit()
                        
                    await interaction.response.send_message(
                        f"*تم إزالة مضاعف نقاط الخبرة من الرتبة {target.mention}*"
                    )
                else:
                    await interaction.response.send_message(
                        "*لا يوجد مضاعف نقاط خبرة لهذه الرتبة.*",
                        ephemeral=True
                    )
            else:
                # Remove channel multiplier
                channel_multipliers = json.loads(settings['channel_multipliers'])
                if str(target.id) in channel_multipliers:
                    del channel_multipliers[str(target.id)]
                    
                    async with aiosqlite.connect(db.db_path) as conn:
                        await conn.execute("""
                            UPDATE leveling_settings
                            SET channel_multipliers = ?
                            WHERE guild_id = ?
                        """, (json.dumps(channel_multipliers), str(interaction.guild_id)))
                        await conn.commit()
                        
                    await interaction.response.send_message(
                        f"*تم إزالة مضاعف نقاط الخبرة من القناة {target.mention}*"
                    )
                else:
                    await interaction.response.send_message(
                        "*لا يوجد مضاعف نقاط خبرة لهذه القناة.*",
                        ephemeral=True
                    )
                    
        except Exception as e:
            logger.error(f"Failed to remove multiplier: {str(e)}")
            await interaction.response.send_message(
                "*حدث خطأ أثناء إزالة المضاعف.*",
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
            logger.error(f"Leveling command error: {str(error)}")
            await interaction.response.send_message(
                "*حدث خطأ غير متوقع.*",
                ephemeral=True
            )

async def setup(bot):
    """Setup function for loading the cog"""
    # Create cog instance
    cog = LevelingCommands(bot)
    
    # Add cog to bot
    await bot.add_cog(cog)
    
    try:
        # Register app commands to guild
        guild = discord.Object(id=Config.GUILD_ID)
        commands = [
            cog.rank,
            cog.leaderboard,
            cog.setxp,
            cog.set_multiplier,
            cog.remove_multiplier
        ]
        for cmd in commands:
            bot.tree.add_command(cmd, guild=guild)
        print("Registered leveling commands to guild")
    except Exception as e:
        print(f"Failed to register leveling commands: {e}")
