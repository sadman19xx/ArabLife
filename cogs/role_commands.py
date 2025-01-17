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

    @app_commands.command(
        name='مقبول',
        description='Give visa role to a member'
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    async def give_role(self, interaction: discord.Interaction, member: discord.Member):
        """Give the specified role to a member"""
        # Check if user has allowed role
        if not any(role.id in Config.ROLE_IDS_ALLOWED for role in interaction.user.roles):
            await interaction.response.send_message('*لا تملك الصلاحية لأستخدام هذا الامر.*', ephemeral=True)
            return

        # Input validation
        if member.bot:
            await interaction.response.send_message('*لا يمكن إعطاء التأشيرة للبوتات.*', ephemeral=True)
            return
            
        # Rate limit check
        if not await self._check_rate_limit(interaction):
            await interaction.response.send_message(
                f'*الرجاء الانتظار {Config.ROLE_COMMAND_COOLDOWN} ثواني.*',
                ephemeral=True
            )
            return
        """Give the specified role to a member"""
        # Security checks
        if not self._check_role_hierarchy(interaction, member):
            await interaction.response.send_message('*لا يمكن تعديل أدوار هذا العضو.*', ephemeral=True)
            return

        role = self._get_role(interaction.guild_id)
        if not role:
            await interaction.response.send_message('*لا توجد تاشيرات.*', ephemeral=True)
            return

        if role in member.roles:
            await interaction.response.send_message(f'*تم أصدار التاشيرة من قبل.*', ephemeral=True)
            return

        try:
            await member.add_roles(role)
            
            # Track role assignment
            await self._track_role_change(
                interaction.guild_id,
                member.id,
                role.id,
                interaction.user.id,
                True
            )
            
            response = '*تم أصدار التاشيرة بنجاح.*'
            
            await interaction.response.send_message(response)
            logger.info(f"Role '{role.name}' assigned to {member.name}#{member.discriminator} by {interaction.user.name}#{interaction.user.discriminator}")
        except discord.Forbidden:
            await interaction.response.send_message('*لا املك الصلاحية لتعديل الأدوار.*', ephemeral=True)
            logger.error(f"Failed to assign role: Insufficient permissions")
        except discord.HTTPException as e:
            await interaction.response.send_message('*حدث خطأ اثناء تعديل الأدوار.*', ephemeral=True)
            logger.error(f"Failed to assign role: {str(e)}")

    @app_commands.command(
        name='مرفوض',
        description='Remove visa role from a member'
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.checks.cooldown(1, Config.ROLE_COMMAND_COOLDOWN)
    async def remove_role(self, interaction: discord.Interaction, member: discord.Member):
        """Remove the specified role from a member"""
        # Check if user has allowed role
        if not any(role.id in Config.ROLE_IDS_ALLOWED for role in interaction.user.roles):
            await interaction.response.send_message('*لا تملك الصلاحية لأستخدام هذا الامر.*', ephemeral=True)
            return

        # Security checks
        if not self._check_role_hierarchy(interaction, member):
            await interaction.response.send_message('*لا يمكن تعديل أدوار هذا العضو.*', ephemeral=True)
            return

        role = self._get_role(interaction.guild_id)
        if not role:
            await interaction.response.send_message('*لا توجد تاشيرات.*', ephemeral=True)
            return

        if role not in member.roles:
            await interaction.response.send_message(f'*لا يوجد لديه تاشيرة من قبل.*', ephemeral=True)
            return

        try:
            await member.remove_roles(role)
            
            # Track role removal
            await self._track_role_change(
                interaction.guild_id,
                member.id,
                role.id,
                interaction.user.id,
                False
            )
            
            response = '*تم الغاء التاشيرة بنجاح.*'
            
            await interaction.response.send_message(response)
            logger.info(f"Role '{role.name}' removed from {member.name}#{member.discriminator} by {interaction.user.name}#{interaction.user.discriminator}")
        except discord.Forbidden:
            await interaction.response.send_message('*لا املك الصلاحية لتعديل الأدوار.*', ephemeral=True)
            logger.error(f"Failed to remove role: Insufficient permissions")
        except discord.HTTPException as e:
            await interaction.response.send_message('*حدث خطأ اثناء تعديل الأدوار.*', ephemeral=True)
            logger.error(f"Failed to remove role: {str(e)}")

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
    
    try:
        # Register app commands to guild
        guild = discord.Object(id=Config.GUILD_ID)
        bot.tree.add_command(cog.give_role, guild=guild)
        bot.tree.add_command(cog.remove_role, guild=guild)
        print("Registered role commands to guild")
    except Exception as e:
        print(f"Failed to register role commands: {e}")
