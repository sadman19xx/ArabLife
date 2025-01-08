import discord
import logging
from discord.ext import commands
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Fetch variables from environment
TOKEN = os.getenv('TOKEN')
ROLE_IDS_ALLOWED = list(map(int, os.getenv('ROLE_IDS_ALLOWED').split(',')))
ROLE_ID_TO_GIVE = int(os.getenv('ROLE_ID_TO_GIVE'))
ROLE_ID_REMOVE_ALLOWED = int(os.getenv('ROLE_ID_REMOVE_ALLOWED'))
ROLE_ACTIVITY_LOG_CHANNEL_ID = int(os.getenv('ROLE_ACTIVITY_LOG_CHANNEL_ID'))
AUDIT_LOG_CHANNEL_ID = int(os.getenv('AUDIT_LOG_CHANNEL_ID'))
GUILD_ID = int(os.getenv('GUILD_ID'))  # Guild ID moved to .env

# Configure logging
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)

# Custom filter to distinguish role-related logs
class RoleLogFilter(logging.Filter):
    def filter(self, record):
        return "Role" in record.getMessage()

# Custom filter to distinguish general logs from role-related logs
class GeneralLogFilter(logging.Filter):
    def filter(self, record):
        return "Role" not in record.getMessage()

# Custom log handler to send logs to a Discord channel
class DiscordLogHandler(logging.Handler):
    def __init__(self, bot, channel_id):
        super().__init__()
        self.bot = bot
        self.channel_id = channel_id

    async def send_log(self, message):
        channel = self.bot.get_channel(self.channel_id)
        if channel:
            await channel.send(message)

    def emit(self, record):
        log_entry = self.format(record)
        self.bot.loop.create_task(self.send_log(log_entry))

intents = discord.Intents.default()
intents.members = True  # Required to manage roles
intents.message_content = True  # Enable reading message content for commands

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

    # Create role-specific log handler and general log handler
    role_audit_handler = DiscordLogHandler(bot, ROLE_ACTIVITY_LOG_CHANNEL_ID)
    audit_log_handler = DiscordLogHandler(bot, AUDIT_LOG_CHANNEL_ID)

    # Apply custom filters
    role_audit_handler.addFilter(RoleLogFilter())  # Logs role-related actions
    audit_log_handler.addFilter(GeneralLogFilter())  # Logs everything except role-related actions

    formatter = logging.Formatter('%(asctime)s - %(message)s')
    role_audit_handler.setFormatter(formatter)
    audit_log_handler.setFormatter(formatter)

    logger.addHandler(role_audit_handler)  # Role-related logs
    logger.addHandler(audit_log_handler)   # General logs

    # Set the default status when the bot starts
    activity = discord.Activity(type=discord.ActivityType.watching, name="you my love")
    await bot.change_presence(activity=activity)

    # Sync slash commands for a specific guild (instant availability)
    guild = discord.Object(id=GUILD_ID)
    await bot.tree.sync(guild=guild)
    
    guild_object = bot.get_guild(GUILD_ID)
    if guild_object:
        print(f"Successfully synced commands to guild: {guild_object.name}")
    else:
        print("Failed to fetch the guild object.")
    
    # Uncomment the following line to sync globally (can take up to 1 hour)
    # await bot.tree.sync()

# Check if the user has one of the allowed roles to use the bot
def has_allowed_role():
    def predicate(ctx):
        user_roles = {role.id for role in ctx.author.roles}
        for role_id in ROLE_IDS_ALLOWED:
            if role_id in user_roles:
                return True
        raise commands.MissingPermissions(['Required role'])
    return commands.check(predicate)

# Check if the user has the role that can use مرفوض command
def has_remove_role():
    def predicate(ctx):
        user_roles = {role.id for role in ctx.author.roles}
        if ROLE_ID_REMOVE_ALLOWED in user_roles:
            return True
        raise commands.MissingPermissions(['Required role to remove roles'])
    return commands.check(predicate)

# Command to give the specific role (قبول)
@bot.command()
@has_allowed_role()
async def مقبول(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, id=ROLE_ID_TO_GIVE)
    if not role:
        await ctx.send('*لا توجد تاشيرات.*')
        return

    if role in member.roles:
        await ctx.send(f'*تم أصدار التاشيرة من قبل.*')
    else:
        await member.add_roles(role)
        await ctx.send(f'*تم أصدار التاشيرة بنجاح.*')

        # Log the action in the role log channel
        logger.info(f"Role '{role.name}' assigned to {member.name}#{member.discriminator} by {ctx.author.name}#{ctx.author.discriminator}")

# Command to remove the specific role from a member (مرفوض)
@bot.command()
@has_remove_role()
async def مرفوض(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, id=ROLE_ID_TO_GIVE)
    if not role:
        await ctx.send('*لا توجد تاشيرات.*')
        return

    if role not in member.roles:
        await ctx.send(f'*لا يوجد لديه تاشيرة من قبل.*')
    else:
        await member.remove_roles(role)
        await ctx.send(f'*تم الغاء التاشيرة بنجاح.*')

        # Log the action in the role log channel
        logger.info(f"Role '{role.name}' removed from {member.name}#{member.discriminator} by {ctx.author.name}#{ctx.author.discriminator}")

# Command to dynamically set any status
@bot.command()
@commands.has_permissions(administrator=True)
async def setstatus(ctx, activity_type: str, *, message: str):
    """Change the bot's status dynamically.
    Usage: /setstatus <type> <message>
    Types: playing, streaming, listening, watching, competing
    """
    activity_types = {
        "playing": discord.ActivityType.playing,
        "streaming": discord.ActivityType.streaming,
        "listening": discord.ActivityType.listening,
        "watching": discord.ActivityType.watching,
        "competing": discord.ActivityType.competing,
    }

    if activity_type.lower() not in activity_types:
        await ctx.send("❌ Invalid activity type! Use one of: playing, streaming, listening, watching, competing.")
        return

    activity = discord.Activity(type=activity_types[activity_type.lower()], name=message)
    await bot.change_presence(activity=activity)
    await ctx.send(f"✅ Status changed to: {activity_type.capitalize()} {message}")

    # Log the status change in the general log channel
    logger.info(f"Status changed to: {activity_type.capitalize()} {message} by {ctx.author.name}#{ctx.author.discriminator}")

# Slash command version of 'commands'
@bot.tree.command(name='commands')
async def custom_help(interaction: discord.Interaction):
    """Displays a list of available commands.""" 
    help_message = """
    **Available Commands:** 

    1. **/مقبول [member]** — Gives the specified member a role.
    2. **/مرفوض [member]** — Removes the specified role from the member.
    3. **/setstatus [type] [message]** — Dynamically changes the bot’s status.
       - **Types**: playing, streaming, listening, watching, competing
    4. **/commands** — Displays this help message.
    """
    try:
        await interaction.user.send(help_message)
        await interaction.response.send_message("*تم الرد على الخاص*")
    except discord.Forbidden:
        await interaction.response.send_message("❌ لا يمكن إرسال الرسالة إلى الخاص. يرجى التأكد من إعدادات الخصوصية الخاصة بك.")

# Custom error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('*لا تملك الصلاحية لأستخدام هذه الامر.*')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('*يرجى تقديم جميع المعطيات المطلوبة.*')
    elif isinstance(error, commands.BadArgument):
        await ctx.send('*لا يوجد شخص بهذا الاسم.*')
    elif isinstance(error, commands.CheckFailure):
        await ctx.send('*لا تملك الصلاحية لأستخدام هذه الامر.*')
    else:
        # Log the error details for debugging
        logger.error(f"An unexpected error occurred: {error}", exc_info=True)
        await ctx.send('*حدث خطأ غير متوقع. ارجو التواصل مع إدارة الديسكورد وتقديم تفاصيل الأمر.*')

bot.run(TOKEN)
