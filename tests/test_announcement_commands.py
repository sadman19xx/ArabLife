import pytest
from discord.ext import commands
import discord
from cogs.announcement_commands import AnnouncementCommands

class MockContext:
    def __init__(self, bot):
        self.bot = bot
        self.guild = discord.Object(id=1)
        self.guild.me = discord.Object(id=2)
        self.responded = False
        self.response = None
        
    async def respond(self, content, ephemeral=False):
        self.responded = True
        self.response = content
        self.is_ephemeral = ephemeral

class MockChannel:
    def __init__(self, permissions=None):
        self.id = 1
        self.name = "test-channel"
        self._permissions = permissions or discord.Permissions()
        self.sent_messages = []
        
    def permissions_for(self, member):
        return self._permissions
        
    @property
    def mention(self):
        return f"#{self.name}"
        
    async def send(self, content):
        self.sent_messages.append(content)

class MockMember:
    def __init__(self, permissions=None):
        self.id = 1
        self.guild_permissions = permissions or discord.Permissions()

@pytest.mark.asyncio
async def test_announce_command_no_permissions():
    """Test announce command when user lacks required permissions"""
    bot = commands.Bot(command_prefix="!")
    ctx = MockContext(bot)
    ctx.author = MockMember()  # No permissions
    channel = MockChannel()
    
    cog = AnnouncementCommands(bot)
    await cog.announce(ctx, message="Test announcement", channel=channel)
    
    assert ctx.responded
    assert "Error: You need 'Administrator' permission" in ctx.response
    assert ctx.is_ephemeral
    assert not channel.sent_messages  # No message should be sent

@pytest.mark.asyncio
async def test_announce_command_no_bot_permissions():
    """Test announce command when bot lacks required permissions"""
    bot = commands.Bot(command_prefix="!")
    ctx = MockContext(bot)
    
    # Give user required permissions
    permissions = discord.Permissions()
    permissions.administrator = True
    ctx.author = MockMember(permissions)
    
    # But don't give bot send permissions
    channel = MockChannel()
    
    cog = AnnouncementCommands(bot)
    await cog.announce(ctx, message="Test announcement", channel=channel)
    
    assert ctx.responded
    assert "Error: I don't have permission to send messages" in ctx.response
    assert ctx.is_ephemeral
    assert not channel.sent_messages

@pytest.mark.asyncio
async def test_announce_command_success():
    """Test successful announcement"""
    bot = commands.Bot(command_prefix="!")
    ctx = MockContext(bot)
    
    # Give user and bot required permissions
    permissions = discord.Permissions()
    permissions.administrator = True
    permissions.send_messages = True
    ctx.author = MockMember(permissions)
    channel = MockChannel(permissions)
    
    cog = AnnouncementCommands(bot)
    test_message = "Test announcement"
    await cog.announce(ctx, message=test_message, channel=channel)
    
    assert ctx.responded
    assert "✅ Announcement sent successfully" in ctx.response
    assert ctx.is_ephemeral
    assert len(channel.sent_messages) == 1
    assert channel.sent_messages[0] == f"@everyone {test_message}"
