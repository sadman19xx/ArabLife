import discord
from discord.ext import commands
from discord import app_commands
from discord.ext.commands import Cog, cooldown, BucketType
import logging
from config import Config

logger = logging.getLogger('discord')

class RoleCommands(Cog):
    """Cog for role management commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self._role_cache = {}
        
    async def _check_rate_limit(self, interaction: discord.Interaction) -> bool:
        """Check if user has exceeded rate limit"""
        async with self.bot.db.transaction() as cursor:
            # Get recent command usage
            await cursor.execute("""
                SELECT COUNT(*) FROM command_usage 
                WHERE guild_id = ? AND user_id = ? AND command_name = ? 
                AND used_at > datetime('now', '-1 minute')
            """, (str(interaction.guild_id), str(interaction.user.id), interaction.command.name))
            count = (await cursor.fetchone())[0]
            
            # Log command usage
            await cursor.execute("""
                INSERT INTO command_usage (guild_id, user_id, command_name)
                VALUES (?, ?, ?)
            """, (str(interaction.guild_id), str(interaction.user.id), interaction.command.name))
            
            return count < Config.ROLE_COMMAND_COOLDOWN
            
    async def _track_role_change(self, guild_id: int, user_id: int, role_id: int, assigned_by: int, is_add: bool):
        """Track role changes in database"""
        async with self.bot.db.transaction() as cursor:
            if is_add:
                await cursor.execute("""
                    INSERT OR REPLACE INTO user_roles (guild_id, user_id, role_id, assigned_by)
                    VALUES (?, ?, ?, ?)
                """, (str(guild_id), str(user_id), str(role_id), str(assigned_by)))
            else:
                await cursor.execute("""
                    DELETE FROM user_roles 
                    WHERE guild_id = ? AND user_id = ? AND role_id = ?
                """, (str(guild_id), str(user_id), str(role_id)))

    async def _check_role_hierarchy(self, interaction: discord.Interaction, member: discord.Member) -> bool:
        """Check if the bot's role is high enough to manage the target member's roles"""
        bot_member = interaction.guild.get_member(self.bot.user.id)
        return bot_member.top_role > member.top_role

    def _get_role(self, guild_id):
        """Get role from cache or fetch and cache it"""
        if guild_id not in self._role_cache:
            role = discord.utils.get(self.bot.get_guild(guild_id).roles, id=Config.ROLE_ID_TO_GIVE)
            if role:
                self._role_cache[guild_id] = role
        return self._role_cache.get(guild_id)

    async def cog_check(self, ctx):
        """Check if user has required permissions for any command in this cog"""
        if not ctx.guild:
            raise commands.NoPrivateMessage()
        return True

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
            logger.error(f"Unexpected error in role command: {str(error)}")
            await interaction.response.send_message(
                "*حدث خطأ غير متوقع.*",
                ephemeral=True
            )

async def setup(bot):
    """Setup function for loading the cog"""
    # Create cog instance
    cog = RoleCommands(bot)
    
    # Add cog to bot
    await bot.add_cog(cog)
