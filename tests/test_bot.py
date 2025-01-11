import pytest
import discord
import discord.ext.test as dpytest
from bot import ArabLifeBot
from discord.ext import commands
import asyncio

@pytest.mark.asyncio
async def test_bot_initialization(bot: ArabLifeBot):
    """Test bot initialization"""
    assert bot.user is not None
    assert bot.is_ready()
    assert len(bot.guilds) > 0
    assert hasattr(bot, 'command_stats')
    assert hasattr(bot, 'error_count')
    assert hasattr(bot, 'health_server')

@pytest.mark.asyncio
async def test_prefix_command(bot: ArabLifeBot, guild: discord.Guild):
    """Test prefix command"""
    # Test default prefix
    message = await dpytest.message("!help")
    assert len(dpytest.get_message()) > 0
    
    # Test custom prefix
    async with bot.db.transaction() as cursor:
        await cursor.execute("""
            UPDATE bot_settings 
            SET prefix = ? 
            WHERE guild_id = ?
        """, ("?", str(guild.id)))
    
    bot.prefixes = {}  # Clear cache
    message = await dpytest.message("?help")
    assert len(dpytest.get_message()) > 0

@pytest.mark.asyncio
async def test_error_handling(bot: ArabLifeBot):
    """Test error handling"""
    initial_error_count = bot.error_count
    
    # Test missing permissions error
    class TestCog(commands.Cog):
        @commands.command()
        @commands.has_permissions(administrator=True)
        async def testcmd(self, ctx):
            await ctx.send("Success")
    
    await bot.add_cog(TestCog(bot))
    await dpytest.message("!testcmd")
    
    assert len(dpytest.get_message()) > 0
    assert "لا تملك الصلاحية" in dpytest.get_message().content
    assert bot.error_count == initial_error_count + 1

@pytest.mark.asyncio
async def test_command_tracking(bot: ArabLifeBot):
    """Test command usage tracking"""
    # Create test command
    @bot.command()
    async def testcmd(ctx):
        await ctx.send("Test command executed")
    
    # Execute command
    initial_count = bot.command_stats.get('testcmd', 0)
    await dpytest.message("!testcmd")
    
    assert bot.command_stats['testcmd'] == initial_count + 1
    assert "Test command executed" in dpytest.get_message().content

@pytest.mark.asyncio
async def test_health_check(bot: ArabLifeBot):
    """Test health check endpoint"""
    # Make request to health check endpoint
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:8080/health') as response:
            assert response.status == 200
            text = await response.text()
            assert text == "OK"

@pytest.mark.asyncio
async def test_metrics_endpoint(bot: ArabLifeBot):
    """Test metrics endpoint"""
    # Make request to metrics endpoint
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:8080/metrics') as response:
            assert response.status == 200
            data = await response.json()
            
            # Check required metrics
            assert 'uptime' in data
            assert 'guilds' in data
            assert 'users' in data
            assert 'latency' in data
            assert 'cpu_percent' in data
            assert 'memory' in data
            assert 'cached_tickets' in data
            assert 'cached_prefixes' in data
            assert 'commands_used' in data
            assert 'error_count' in data

@pytest.mark.asyncio
async def test_database_operations(bot: ArabLifeBot, setup_database):
    """Test database operations"""
    async with bot.db.transaction() as cursor:
        # Test guild retrieval
        await cursor.execute("SELECT * FROM guilds WHERE id = ?", ("123456789",))
        guild = await cursor.fetchone()
        assert guild is not None
        assert guild['name'] == "Test Guild"
        
        # Test settings retrieval
        await cursor.execute("SELECT prefix FROM bot_settings WHERE guild_id = ?", ("123456789",))
        settings = await cursor.fetchone()
        assert settings is not None
        assert settings['prefix'] == "!"
        
        # Test ticket retrieval
        await cursor.execute("SELECT * FROM tickets WHERE guild_id = ?", ("123456789",))
        ticket = await cursor.fetchone()
        assert ticket is not None
        assert ticket['ticket_type'] == "player_report"
        assert ticket['status'] == "open"

@pytest.mark.asyncio
async def test_bot_shutdown(bot: ArabLifeBot):
    """Test bot shutdown"""
    # Trigger shutdown
    await bot.close()
    
    # Verify cleanup
    assert not bot.is_ready()
    assert not bot._connection.is_connected
    
    # Health server should be stopped
    import aiohttp
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:8080/health') as response:
                assert False, "Health server should be stopped"
    except:
        pass  # Expected - server should be down

@pytest.mark.asyncio
async def test_command_cooldowns(bot: ArabLifeBot):
    """Test command cooldowns"""
    @bot.command()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def cooldown_cmd(ctx):
        await ctx.send("Command executed")
    
    # First execution should work
    await dpytest.message("!cooldown_cmd")
    assert "Command executed" in dpytest.get_message().content
    
    # Second execution should fail
    await dpytest.message("!cooldown_cmd")
    assert "يرجى الانتظار" in dpytest.get_message().content

@pytest.mark.asyncio
async def test_guild_join(bot: ArabLifeBot):
    """Test guild join handling"""
    # Create new guild
    guild = await dpytest.simulate_guild_join()
    
    # Check database entries
    async with bot.db.transaction() as cursor:
        await cursor.execute("SELECT * FROM guilds WHERE id = ?", (str(guild.id),))
        guild_entry = await cursor.fetchone()
        assert guild_entry is not None
        
        await cursor.execute("SELECT * FROM bot_settings WHERE guild_id = ?", (str(guild.id),))
        settings = await cursor.fetchone()
        assert settings is not None
        assert settings['prefix'] == "!"
