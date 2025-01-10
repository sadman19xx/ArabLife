import pytest
import asyncio
import discord.ext.test as dpytest
from typing import AsyncGenerator, Generator
from bot import ArabLifeBot
from config import Config
import os
import aiosqlite
import json

# Test database path
TEST_DB_PATH = "test_data/bot_test.db"

@pytest.fixture
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test case"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def bot(event_loop: asyncio.AbstractEventLoop) -> AsyncGenerator[ArabLifeBot, None]:
    """Create a bot instance for testing"""
    # Set test configuration
    Config.TOKEN = "test_token"
    Config.GUILD_ID = 123456789
    os.environ["TEST_MODE"] = "true"
    
    # Create test directories
    os.makedirs("test_data", exist_ok=True)
    os.makedirs("test_data/logs", exist_ok=True)
    
    # Initialize test database
    async with aiosqlite.connect(TEST_DB_PATH) as db:
        with open("utils/schema.sql") as f:
            await db.executescript(f.read())
        await db.commit()
    
    # Create bot instance
    bot = ArabLifeBot()
    
    # Configure for testing
    bot.db_path = TEST_DB_PATH
    
    # Setup dpytest
    await dpytest.configure(bot)
    
    yield bot
    
    # Cleanup
    await bot.close()
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    if os.path.exists("test_data"):
        import shutil
        shutil.rmtree("test_data")

@pytest.fixture
async def guild(bot: ArabLifeBot) -> discord.Guild:
    """Create a test guild"""
    return bot.guilds[0]

@pytest.fixture
async def text_channel(guild: discord.Guild) -> discord.TextChannel:
    """Create a test text channel"""
    return guild.text_channels[0]

@pytest.fixture
async def member(guild: discord.Guild) -> discord.Member:
    """Create a test member"""
    return guild.members[0]

@pytest.fixture
async def admin_member(guild: discord.Guild) -> discord.Member:
    """Create a test admin member"""
    admin_role = await guild.create_role(name="Admin", permissions=discord.Permissions.all())
    member = guild.members[0]
    await member.add_roles(admin_role)
    return member

@pytest.fixture
def mock_config(monkeypatch):
    """Mock configuration for testing"""
    test_config = {
        "TOKEN": "test_token",
        "GUILD_ID": 123456789,
        "ROLE_IDS_ALLOWED": [123, 456],
        "ROLE_ID_TO_GIVE": 789,
        "ROLE_ID_REMOVE_ALLOWED": 101,
        "ROLE_ACTIVITY_LOG_CHANNEL_ID": 102,
        "AUDIT_LOG_CHANNEL_ID": 103,
        "ERROR_LOG_CHANNEL_ID": 104,
        "TICKET_STAFF_ROLE_ID": 105,
        "TICKET_CATEGORY_ID": 106,
        "TICKET_LOG_CHANNEL_ID": 107,
        "PLAYER_REPORT_ROLE_ID": 108,
        "HEALTH_DEPT_ROLE_ID": 109,
        "INTERIOR_DEPT_ROLE_ID": 110,
        "FEEDBACK_ROLE_ID": 111
    }
    
    for key, value in test_config.items():
        monkeypatch.setattr(Config, key, value)
    
    return test_config

@pytest.fixture
async def setup_database():
    """Setup test database with initial data"""
    async with aiosqlite.connect(TEST_DB_PATH) as db:
        # Create test guild
        await db.execute("""
            INSERT INTO guilds (id, name, owner_id, member_count)
            VALUES (?, ?, ?, ?)
        """, ("123456789", "Test Guild", "987654321", 1))
        
        # Create test settings
        await db.execute("""
            INSERT INTO bot_settings (guild_id, prefix)
            VALUES (?, ?)
        """, ("123456789", "!"))
        
        # Create test tickets
        await db.execute("""
            INSERT INTO tickets (
                channel_id, guild_id, user_id, ticket_type, status, created_at
            ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, ("111111111", "123456789", "987654321", "player_report", "open"))
        
        await db.commit()

@pytest.fixture
def mock_redis(monkeypatch):
    """Mock Redis for testing"""
    class MockRedis:
        def __init__(self):
            self.data = {}
            
        async def get(self, key):
            return self.data.get(key)
            
        async def set(self, key, value, ex=None):
            self.data[key] = value
            
        async def delete(self, key):
            if key in self.data:
                del self.data[key]
                
        async def exists(self, key):
            return key in self.data
    
    mock_redis = MockRedis()
    monkeypatch.setattr("bot.redis", mock_redis)
    return mock_redis
