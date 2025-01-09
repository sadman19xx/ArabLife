import discord
from discord.ext import commands
from discord.ext.commands import Cog
import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
import aiosqlite
import os
from config import Config

logger = logging.getLogger('discord')

class LevelingCommands(Cog):
    """Cog for handling user leveling and XP system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.settings = {
            "is_enabled": Config.LEVELING_ENABLED,
            "xp_per_message": Config.XP_PER_MESSAGE,
            "xp_cooldown": Config.XP_COOLDOWN,
            "level_up_channel_id": Config.LEVEL_UP_CHANNEL_ID,
            "level_up_message": Config.LEVEL_UP_MESSAGE,
            "role_rewards": json.loads(Config.ROLE_REWARDS)
        }
        self.user_cooldowns: Dict[int, datetime] = {}
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
                    SELECT id, '{"leveling": ' || ? || '}'
                    FROM guilds WHERE discord_id = ?
                ''', (json.dumps(self.settings), str(Config.GUILD_ID)))
                
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to setup database: {str(e)}")

    async def save_settings(self):
        """Save current settings to database"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    UPDATE guild_settings 
                    SET custom_settings = json_set(custom_settings, '$.leveling', ?)
                    WHERE guild_id = (SELECT id FROM guilds WHERE discord_id = ?)
                ''', (json.dumps(self.settings), str(Config.GUILD_ID)))
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to save settings: {str(e)}")

    def calculate_xp_for_level(self, level: int) -> int:
        """Calculate XP required for a specific level"""
        return 5 * (level ** 2) + 50 * level + 100

    def calculate_level_from_xp(self, xp: int) -> int:
        """Calculate level based on total XP"""
        level = 0
        while xp >= self.calculate_xp_for_level(level):
            xp -= self.calculate_xp_for_level(level)
            level += 1
        return level

    async def add_xp(self, user_id: int, guild_id: int, xp_amount: int) -> Optional[int]:
        """Add XP to user and return new level if leveled up"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Get guild's database ID
                async with db.execute(
                    'SELECT id FROM guilds WHERE discord_id = ?',
                    (str(guild_id),)
                ) as cursor:
                    guild_result = await cursor.fetchone()
                    if not guild_result:
                        return None
                    db_guild_id = guild_result[0]
                
                # Get or create leveling entry
                async with db.execute(
                    'SELECT xp, level FROM leveling WHERE guild_id = ? AND user_discord_id = ?',
                    (db_guild_id, str(user_id))
                ) as cursor:
                    result = await cursor.fetchone()
                
                if result:
                    current_xp, current_level = result
                else:
                    current_xp, current_level = 0, 0
                    await db.execute(
                        'INSERT INTO leveling (guild_id, user_discord_id, xp, level) VALUES (?, ?, 0, 0)',
                        (db_guild_id, str(user_id))
                    )
                
                new_xp = current_xp + xp_amount
                new_level = self.calculate_level_from_xp(new_xp)
                
                await db.execute('''
                    UPDATE leveling 
                    SET xp = ?, level = ?, last_message_time = ?
                    WHERE guild_id = ? AND user_discord_id = ?
                ''', (new_xp, new_level, datetime.now(), db_guild_id, str(user_id)))
                
                await db.commit()
                return new_level if new_level > current_level else None
                
        except Exception as e:
            logger.error(f"Failed to add XP: {str(e)}")
            return None

    async def handle_level_up(self, member: discord.Member, new_level: int):
        """Handle level up event including role rewards"""
        if not self.settings['is_enabled']:
            return

        try:
            # Send level up message
            if self.settings['level_up_channel_id']:
                channel = self.bot.get_channel(int(self.settings['level_up_channel_id']))
                if channel:
                    message = self.settings['level_up_message'].format(
                        user=member.mention,
                        level=new_level
                    )
                    await channel.send(message)

            # Handle role rewards
            for reward in self.settings['role_rewards']:
                if reward['level'] == new_level:
                    role = member.guild.get_role(int(reward['role_id']))
                    if role:
                        await member.add_roles(role)
                        logger.info(f"Added role {role.name} to {member.name} for reaching level {new_level}")
                        
        except Exception as e:
            logger.error(f"Failed to handle level up: {str(e)}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Handle XP gain from messages"""
        if not self.settings['is_enabled'] or message.author.bot or not message.guild:
            return
            
        try:
            # Check cooldown
            user_id = message.author.id
            now = datetime.now()
            if user_id in self.user_cooldowns:
                time_diff = (now - self.user_cooldowns[user_id]).total_seconds()
                if time_diff < self.settings['xp_cooldown']:
                    return
                    
            self.user_cooldowns[user_id] = now
            
            # Add XP
            new_level = await self.add_xp(user_id, message.guild.id, self.settings['xp_per_message'])
            if new_level:
                await self.handle_level_up(message.author, new_level)
                
        except Exception as e:
            logger.error(f"Failed to process message XP: {str(e)}")

    @commands.hybrid_command()
    async def rank(self, ctx: commands.Context, member: discord.Member = None):
        """Check your or another user's rank"""
        try:
            target = member or ctx.author
            
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
                
                # Get user's XP and level
                async with db.execute(
                    'SELECT xp, level FROM leveling WHERE guild_id = ? AND user_discord_id = ?',
                    (db_guild_id, str(target.id))
                ) as cursor:
                    result = await cursor.fetchone()
                
                if not result:
                    await ctx.send(f"{target.mention} has not earned any XP yet!")
                    return
                
                xp, level = result
                
                # Get user's rank
                async with db.execute('''
                    SELECT COUNT(*) FROM leveling 
                    WHERE guild_id = ? AND xp > (
                        SELECT xp FROM leveling 
                        WHERE guild_id = ? AND user_discord_id = ?
                    )
                ''', (db_guild_id, db_guild_id, str(target.id))) as cursor:
                    rank = (await cursor.fetchone())[0] + 1
                
                next_level_xp = self.calculate_xp_for_level(level)
                current_level_xp = xp - sum(self.calculate_xp_for_level(i) for i in range(level))
                progress = (current_level_xp / next_level_xp) * 100
                
                embed = discord.Embed(title="Rank Information", color=discord.Color.blue())
                embed.set_author(name=target.display_name, icon_url=target.avatar.url if target.avatar else None)
                embed.add_field(name="Rank", value=f"#{rank}", inline=True)
                embed.add_field(name="Level", value=str(level), inline=True)
                embed.add_field(name="XP", value=f"{xp} XP", inline=True)
                embed.add_field(name="Progress to Next Level", value=f"{progress:.1f}%", inline=True)
                
                await ctx.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Failed to get rank: {str(e)}")
            await ctx.send("An error occurred while fetching rank information.")

    @commands.hybrid_command()
    async def leaderboard(self, ctx: commands.Context):
        """Show the server's XP leaderboard"""
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
                
                async with db.execute('''
                    SELECT user_discord_id, xp, level 
                    FROM leveling 
                    WHERE guild_id = ?
                    ORDER BY xp DESC 
                    LIMIT 10
                ''', (db_guild_id,)) as cursor:
                    results = await cursor.fetchall()
                
                if not results:
                    await ctx.send("No one has earned any XP yet!")
                    return
                
                embed = discord.Embed(title="XP Leaderboard", color=discord.Color.gold())
                
                for i, (user_id, xp, level) in enumerate(results, 1):
                    member = ctx.guild.get_member(int(user_id))
                    name = member.display_name if member else f"User {user_id}"
                    
                    embed.add_field(
                        name=f"#{i} {name}",
                        value=f"Level {level} | {xp} XP",
                        inline=False
                    )
                
                await ctx.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Failed to get leaderboard: {str(e)}")
            await ctx.send("An error occurred while fetching the leaderboard.")

    @commands.hybrid_command()
    @commands.has_permissions(administrator=True)
    async def setxp(self, ctx: commands.Context, member: discord.Member, xp: int):
        """Set a user's XP (Admin only)"""
        try:
            if xp < 0:
                await ctx.send("XP cannot be negative!")
                return
            
            new_level = self.calculate_level_from_xp(xp)
            
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
                
                await db.execute('''
                    INSERT OR REPLACE INTO leveling (guild_id, user_discord_id, xp, level)
                    VALUES (?, ?, ?, ?)
                ''', (db_guild_id, str(member.id), xp, new_level))
                
                await db.commit()
            
            await ctx.send(f"Set {member.mention}'s XP to {xp} (Level {new_level})")
            
        except Exception as e:
            logger.error(f"Failed to set XP: {str(e)}")
            await ctx.send("An error occurred while setting XP.")

async def setup(bot):
    await bot.add_cog(LevelingCommands(bot))
