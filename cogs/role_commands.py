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
        self.visa_image_url = "https://i.imgur.com/XYZ123.png"  # Replace with your actual image URL

    def _check_role_hierarchy(self, interaction_or_ctx, member):
        """Check if the bot's role is high enough to manage the target member's roles"""
        guild = interaction_or_ctx.guild if isinstance(interaction_or_ctx, discord.Interaction) else interaction_or_ctx.guild
        bot_member = guild.get_member(self.bot.user.id)
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

    def has_allowed_role():
        """Check if user has one of the allowed roles"""
        async def predicate(ctx):
            user_roles = {role.id for role in ctx.author.roles}
            if not any(role_id in user_roles for role_id in Config.ROLE_IDS_ALLOWED):
                raise commands.MissingPermissions(['Required role'])
            return True
        return commands.check(predicate)

    def has_remove_role():
        """Check if user has the role that can use مرفوض command"""
        async def predicate(ctx):
            user_roles = {role.id for role in ctx.author.roles}
            if Config.ROLE_ID_REMOVE_ALLOWED not in user_roles:
                raise commands.MissingPermissions(['Required role to remove roles'])
            return True
        return commands.check(predicate)

    async def send_visa_dm(self, member, action="granted"):
        """Send visa status message with image to member"""
        try:
            embed = discord.Embed(
                title="WELCOME TO LOS SANTOS!" if action == "granted" else "VISA REVOKED",
                description="YOUR VISA HAS BEEN " + action.upper(),
                color=discord.Color.green() if action == "granted" else discord.Color.red()
            )
            embed.set_image(url=self.visa_image_url)
            await member.send(embed=embed)
            return True
        except discord.Forbidden:
            return False

    @app_commands.command(
        name='مقبول',
        description='Give visa role to a member'
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    @app_commands.checks.cooldown(1, Config.ROLE_COMMAND_COOLDOWN)
    async def give_role(self, interaction: discord.Interaction, member: discord.Member):
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
            dm_sent = await self.send_visa_dm(member, "granted")
            
            response = '*تم أصدار التاشيرة بنجاح.*'
            if not dm_sent:
                response += '\n*لم نتمكن من ارسال رسالة خاصة للعضو.*'
            
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
            dm_sent = await self.send_visa_dm(member, "revoked")
            
            response = '*تم الغاء التاشيرة بنجاح.*'
            if not dm_sent:
                response += '\n*لم نتمكن من ارسال رسالة خاصة للعضو.*'
            
            await interaction.response.send_message(response)
            logger.info(f"Role '{role.name}' removed from {member.name}#{member.discriminator} by {interaction.user.name}#{interaction.user.discriminator}")
        except discord.Forbidden:
            await interaction.response.send_message('*لا املك الصلاحية لتعديل الأدوار.*', ephemeral=True)
            logger.error(f"Failed to remove role: Insufficient permissions")
        except discord.HTTPException as e:
            await interaction.response.send_message('*حدث خطأ اثناء تعديل الأدوار.*', ephemeral=True)
            logger.error(f"Failed to remove role: {str(e)}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def test_visa_dm(self, ctx):
        """Test the visa DM functionality"""
        try:
            granted = await self.send_visa_dm(ctx.author, "granted")
            await ctx.send("Sent 'granted' visa DM" if granted else "Failed to send DM")
            
            revoked = await self.send_visa_dm(ctx.author, "revoked")
            await ctx.send("Sent 'revoked' visa DM" if revoked else "Failed to send DM")
        except Exception as e:
            await ctx.send(f"Error testing DMs: {str(e)}")

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
