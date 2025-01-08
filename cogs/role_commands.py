import discord
from discord.ext import commands
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

    def _check_role_hierarchy(self, ctx, member):
        """Check if the bot's role is high enough to manage the target member's roles"""
        bot_member = ctx.guild.get_member(self.bot.user.id)
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

    @commands.command(name='مقبول')
    @has_allowed_role()
    @cooldown(1, Config.ROLE_COMMAND_COOLDOWN, BucketType.user)
    async def give_role(self, ctx, member: discord.Member):
        """Give the specified role to a member"""
        # Security checks
        if not self._check_role_hierarchy(ctx, member):
            await ctx.send('*لا يمكن تعديل أدوار هذا العضو.*')
            return

        role = self._get_role(ctx.guild.id)
        if not role:
            await ctx.send('*لا توجد تاشيرات.*')
            return

        if role in member.roles:
            await ctx.send(f'*تم أصدار التاشيرة من قبل.*')
            return

        try:
            await member.add_roles(role)
            dm_sent = await self.send_visa_dm(member, "granted")
            
            response = '*تم أصدار التاشيرة بنجاح.*'
            if not dm_sent:
                response += '\n*لم نتمكن من ارسال رسالة خاصة للعضو.*'
            
            await ctx.send(response)
            logger.info(f"Role '{role.name}' assigned to {member.name}#{member.discriminator} by {ctx.author.name}#{ctx.author.discriminator}")
        except discord.Forbidden:
            await ctx.send('*لا املك الصلاحية لتعديل الأدوار.*')
            logger.error(f"Failed to assign role: Insufficient permissions")
        except discord.HTTPException as e:
            await ctx.send('*حدث خطأ اثناء تعديل الأدوار.*')
            logger.error(f"Failed to assign role: {str(e)}")

    @commands.command(name='مرفوض')
    @has_remove_role()
    @cooldown(1, Config.ROLE_COMMAND_COOLDOWN, BucketType.user)
    async def remove_role(self, ctx, member: discord.Member):
        """Remove the specified role from a member"""
        # Security checks
        if not self._check_role_hierarchy(ctx, member):
            await ctx.send('*لا يمكن تعديل أدوار هذا العضو.*')
            return

        role = self._get_role(ctx.guild.id)
        if not role:
            await ctx.send('*لا توجد تاشيرات.*')
            return

        if role not in member.roles:
            await ctx.send(f'*لا يوجد لديه تاشيرة من قبل.*')
            return

        try:
            await member.remove_roles(role)
            dm_sent = await self.send_visa_dm(member, "revoked")
            
            response = '*تم الغاء التاشيرة بنجاح.*'
            if not dm_sent:
                response += '\n*لم نتمكن من ارسال رسالة خاصة للعضو.*'
            
            await ctx.send(response)
            logger.info(f"Role '{role.name}' removed from {member.name}#{member.discriminator} by {ctx.author.name}#{ctx.author.discriminator}")
        except discord.Forbidden:
            await ctx.send('*لا املك الصلاحية لتعديل الأدوار.*')
            logger.error(f"Failed to remove role: Insufficient permissions")
        except discord.HTTPException as e:
            await ctx.send('*حدث خطأ اثناء تعديل الأدوار.*')
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

    @give_role.error
    @remove_role.error
    async def role_command_error(self, ctx, error):
        """Error handler for role commands"""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send('*لا تملك الصلاحية لأستخدام هذه الامر.*')
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f'*الرجاء الانتظار {error.retry_after:.1f} ثواني.*')
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send('*لا يوجد شخص بهذا الاسم.*')
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send('*لا يمكن استخدام هذا الأمر في الرسائل الخاصة.*')
        else:
            logger.error(f"Unexpected error in role command: {str(error)}")
            await ctx.send('*حدث خطأ غير متوقع.*')

async def setup(bot):
    await bot.add_cog(RoleCommands(bot))
